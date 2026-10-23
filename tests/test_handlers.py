"""Settings synced by their own handlers rather than the mapping table."""
import unittest
from unittest import mock

from tests.helpers import BridgeTestCase, CUSTOM_KEYBINDING_SCHEMA, plugin_list
from wayfire_bridge import media_keys
from wayfire_bridge.budgie_wm_actions import BUDGIE_WM_ACTION_MAPPINGS

MEDIA = 'org.buddiesofbudgie.settings-daemon.plugins.media-keys'
BUDGIE_WM = 'com.solus-project.budgie-wm'


class WindowBehaviour(BridgeTestCase):

    def test_touchpad_scroll_method(self):
        touchpad = 'org.gnome.desktop.peripherals.touchpad'
        self.set(touchpad, 'two-finger-scrolling-enabled', False)
        self.set(touchpad, 'edge-scrolling-enabled', True)
        self.assertEqual(self.option('input', 'scroll_method'), 'edge')
        self.set(touchpad, 'edge-scrolling-enabled', False)
        self.assertEqual(self.option('input', 'scroll_method'), 'none')

    def test_focus_modes(self):
        self.set(BUDGIE_WM, 'window-focus-mode', 'sloppy')
        self.assertIn('follow-focus', plugin_list(self.config()))
        self.assertEqual(self.option('follow-focus', 'raise_on_top'), 'false')
        self.set(BUDGIE_WM, 'window-focus-mode', 'mouse')
        self.assertEqual(self.option('follow-focus', 'raise_on_top'), 'true')
        self.set(BUDGIE_WM, 'window-focus-mode', 'click')
        self.assertNotIn('follow-focus', plugin_list(self.config()))

    def test_edge_tiling(self):
        self.set(BUDGIE_WM, 'edge-tiling', False)
        self.assertEqual(self.option('move', 'enable_snap'), 'false')
        self.set(BUDGIE_WM, 'edge-tiling', True)
        self.assertEqual(self.option('move', 'enable_snap'), 'true')
        self.assertIsNone(self.option('grid', 'mouse_snap'))

    def test_center_new_windows(self):
        self.set('org.gnome.mutter', 'center-new-windows', True)
        self.assertEqual(self.option('place', 'mode'), 'center')
        self.set('org.gnome.mutter', 'center-new-windows', False)
        self.assertEqual(self.option('place', 'mode'), 'cascade')


class SuperKey(BridgeTestCase):

    def prepare_ini(self):
        super().prepare_ini()
        text = self.ini.read_text().replace('[expo]\ntoggle = disabled', '[expo]\ntoggle = <super> | <super> KEY_E')
        self.ini.write_text(text)

    def test_super_opens_the_menu_and_leaves_expo(self):
        self.assertEqual(self.option('command', 'binding_budgie_menu'), '<super>')
        self.assertIn('org.budgie_desktop.Panel.ActivateAction', self.option('command', 'command_budgie_menu'))
        self.assertEqual(self.option('expo', 'toggle'), '<super> KEY_E')


class MediaKeys(BridgeTestCase):

    def static(self, key):
        settings = self.settings(MEDIA)
        if not settings.get_property('settings-schema').has_key(f'{key}-static'):
            return []
        return [b for b in settings.get_strv(f'{key}-static') if b]

    def test_custom_shortcut_keeps_the_hardware_keys(self):
        hardware = self.static('volume-up')
        self.set(MEDIA, 'volume-up', ['<Super><Shift>F9'])
        binding = self.option('command', 'repeatable_binding_volume_up')
        self.assertTrue(binding.startswith('<super> <shift> KEY_F9'))
        self.assertEqual(binding.count('|'), len(hardware))
        self.assertEqual(self.option('command', 'command_volume_up'), 'wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+')

    def test_volume_keys_repeat_and_are_bound_once(self):
        # A plain binding under the same name (e.g. a hand edit) would fire too
        self.bridge.config_manager.set_value('command', 'binding_volume_up', 'KEY_VOLUMEUP')
        self.set(MEDIA, 'volume-up', ['<Super><Shift>F9'])
        self.assertTrue(self.option('command', 'repeatable_binding_volume_up').startswith('<super> <shift> KEY_F9'))
        self.assertIsNone(self.option('command', 'binding_volume_up'))
        self.set(MEDIA, 'volume-mute', ['<Super><Shift>F10'])
        self.assertTrue(self.option('command', 'binding_volume_mute').startswith('<super> <shift> KEY_F10'))
        self.assertIsNone(self.option('command', 'repeatable_binding_volume_mute'))

    def test_screen_brightness_keys_repeat_with_the_brightness_helper(self):
        self.set(MEDIA, 'screen-brightness-up', ['<Super><Shift>F11'])
        self.assertTrue(self.option('command', 'repeatable_binding_backlight_screen_up').startswith('<super> <shift> KEY_F11'))
        self.assertEqual(self.option('command', 'command_backlight_screen_up'), 'budgie-brightness-helper --up')

    def test_keyboard_backlight_keys_are_not_bound_to_the_screen(self):
        self.bridge.config_manager.set_value('command', 'binding_backlight_keyboard_up', 'KEY_KBDILLUMUP')
        self.bridge.config_manager.set_value('command', 'command_backlight_keyboard_up', 'budgie-brightness-helper --up')
        self.set(MEDIA, 'keyboard-brightness-up', ['<Super><Shift>F11'])
        self.assertIsNone(self.option('command', 'binding_backlight_keyboard_up'))
        self.assertIsNone(self.option('command', 'command_backlight_keyboard_up'))

    def test_clearing_a_shortcut_keeps_only_the_hardware_keys(self):
        self.set(MEDIA, 'www', ['<Super><Shift>F9'])
        self.set(MEDIA, 'www', [])
        binding = self.option('command', 'binding_launch_browser')
        if self.static('www'):
            self.assertNotIn('F9', binding)
        else:
            self.assertIsNone(binding)

    def test_browser_key_opens_the_default_browser_without_x_www_browser(self):
        real_which = media_keys.shutil.which
        with mock.patch.object(media_keys.shutil, 'which',
                               side_effect=lambda c: None if c == 'x-www-browser' else real_which(c)):
            self.set(MEDIA, 'www', ['<Super><Shift>F9'])
        self.assertEqual(self.option('command', 'command_launch_browser'),
                         'sh -c \'gtk-launch "$(xdg-settings get default-web-browser)"\'')

    def test_playback_keys_use_playerctl(self):
        self.set(MEDIA, 'next', ['<Super><Shift>F8'])
        self.assertEqual(self.option('command', 'command_media_next'), 'playerctl next')
        self.assertTrue(self.option('command', 'binding_media_next').startswith('<super> <shift> KEY_F8'))

    def test_terminal_uses_the_default_terminal_setting(self):
        if not self.bridge._get_settings('org.gnome.desktop.default-applications.terminal'):
            self.skipTest('default-applications schema not installed')
        self.set(MEDIA, 'terminal', ['<Primary><Alt>t'])
        self.set('org.gnome.desktop.default-applications.terminal', 'exec', 'sh')
        self.assertEqual(self.option('command', 'command_launch_terminal'), 'sh')

    def test_magnifier_binds_the_mag_plugin_when_installed(self):
        with mock.patch.object(media_keys, 'plugin_installed', return_value=True):
            self.set(MEDIA, 'magnifier', ['<Super><Shift>F7'])
            self.assertEqual(self.option('mag', 'toggle'), '<super> <shift> KEY_F7')
            self.assertIn('mag', plugin_list(self.config()))
            self.set(MEDIA, 'magnifier', [])
            self.assertEqual(self.option('mag', 'toggle'), 'disabled')



class MagnifierWithoutPlugin(BridgeTestCase):

    def setUp(self):
        # Missing from the moment the bridge starts, as on a system without
        # wayfire-plugins-extra
        patcher = mock.patch.object(media_keys, 'plugin_installed', return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()

    def test_magnifier_left_unbound(self):
        self.set(MEDIA, 'magnifier', ['<Super><Shift>F7'])
        self.assertIsNone(self.option('mag', 'toggle'))
        self.assertNotIn('mag', plugin_list(self.config()))


class BudgieActions(BridgeTestCase):

    def test_every_action_is_bound(self):
        for key, mapping in BUDGIE_WM_ACTION_MAPPINGS.items():
            schema = mapping.get('schema', BUDGIE_WM)
            if not self.settings(schema).get_property('settings-schema').has_key(key):
                continue
            with self.subTest(key):
                self.set(schema, key, ['<Super><Shift>F6'], wait=0.1)
                self.assertEqual(self.option('command', f"binding_{mapping['command_name']}"), '<super> <shift> KEY_F6')
                self.assertEqual(self.option('command', f"command_{mapping['command_name']}"), mapping['command'])


class CustomShortcuts(BridgeTestCase):

    PATH = '/org/buddiesofbudgie/settings-daemon/plugins/media-keys/custom-keybindings/custom{}/'

    def test_added_before_being_filled_in_then_renamed_and_removed(self):
        path = self.PATH.format(9)
        self.set(MEDIA, 'custom-keybindings', [path])
        self.set(CUSTOM_KEYBINDING_SCHEMA, 'name', 'My Tool', path=path)
        self.set(CUSTOM_KEYBINDING_SCHEMA, 'command', 'mytool --go', path=path)
        self.set(CUSTOM_KEYBINDING_SCHEMA, 'binding', '<Super>F6', path=path)
        self.assertEqual(self.option('command', 'binding_my_tool'), '<super> KEY_F6')
        self.assertEqual(self.option('command', 'command_my_tool'), 'mytool --go')

        self.set(CUSTOM_KEYBINDING_SCHEMA, 'name', 'Renamed Tool', path=path)
        self.assertIsNone(self.option('command', 'binding_my_tool'))
        self.assertEqual(self.option('command', 'binding_renamed_tool'), '<super> KEY_F6')

        self.set(MEDIA, 'custom-keybindings', [])
        self.assertIsNone(self.option('command', 'binding_renamed_tool'))

    def test_clashing_names_get_the_entry_id(self):
        first, second, builtin = (self.PATH.format(n) for n in (1, 2, 3))
        for path, name, binding in ((first, 'Open Term', '<Super>F1'), (second, 'open-term', '<Super>F2'),
                                    (builtin, 'Launch Terminal', '<Super>F3')):
            self.set(CUSTOM_KEYBINDING_SCHEMA, 'name', name, path=path, wait=0)
            self.set(CUSTOM_KEYBINDING_SCHEMA, 'command', 'true', path=path, wait=0)
            self.set(CUSTOM_KEYBINDING_SCHEMA, 'binding', binding, path=path, wait=0)
        self.set(MEDIA, 'custom-keybindings', [first, second, builtin])
        self.assertEqual(self.option('command', 'binding_open_term'), '<super> KEY_F1')
        self.assertEqual(self.option('command', 'binding_open_term_custom2'), '<super> KEY_F2')
        self.assertEqual(self.option('command', 'binding_launch_terminal_custom3'), '<super> KEY_F3')
        self.assertNotEqual(self.option('command', 'command_launch_terminal'), 'true')


if __name__ == '__main__':
    unittest.main()
