"""Changing a GSettings key updates wayfire.ini while the bridge runs."""
import unittest

from tests.helpers import METADATA_DIR, BridgeTestCase, bridge_module, ConfigManager, option_type, pump, wayfire_metadata
from wayfire_bridge.mappings import GSETTINGS_MAPPINGS

TEST_STRINGS = {
    'button-layout': 'close:minimize',
    'titlebar-font': 'Sans Italic 13',
    'cursor-theme': 'TestCursorTheme',
}

# The switcher takes one key and prefers an Alt binding, which the default
# switch-applications already has: switch-windows can't change it
NO_EFFECT_WHILE_ALT_TAB_IS_SET = {'switch-windows', 'switch-windows-backward'}


def other_value(settings, key):
    """A valid value for KEY that differs from its current one, or None."""
    current = settings.get_value(key)
    kind = current.get_type_string()
    range_kind, choices = settings.get_property('settings-schema').get_key(key).get_range().unpack()
    if key == 'xkb-options':
        return ['ctrl:nocaps']
    if key == 'sources':
        return [('xkb', 'de+neo'), ('xkb', 'fr')]
    if range_kind == 'enum':
        others = [c for c in choices if c != current.unpack() and c != 'custom']
        return others[-1] if others else None
    if kind == 'b':
        return not current.unpack()
    if kind in ('i', 'u', 'd'):
        low, high = choices if range_kind == 'range' else (None, None)
        step = 1 if kind != 'd' else 0.5
        value = current.unpack() + step
        if high is not None and value > high:
            value = current.unpack() - step
        if low is not None and value < low:
            return None
        return value
    if kind == 's':
        return TEST_STRINGS.get(key, 'test-value')
    if kind == 'as':
        return ['<Alt><Super>F12']
    return None


class EveryMapping(BridgeTestCase):

    def test_every_mapped_key_reaches_wayfire_ini(self):
        metadata = wayfire_metadata() if METADATA_DIR.is_dir() else None
        for (schema, key), mapping in GSETTINGS_MAPPINGS.items():
            if key in NO_EFFECT_WHILE_ALT_TAB_IS_SET:
                continue
            section, option = mapping['section'], mapping['option']
            settings = self.bridge.settings_objects[schema]
            value = other_value(settings, key)
            with self.subTest(f'{schema}::{key} -> [{section}] {option}'):
                if value is None:
                    self.skipTest('no other valid value')
                before = self.option(section, option)
                self.set(schema, key, value, wait=0.1)
                after = self.option(section, option)
                # Back to the default, so keys sharing an option are each
                # tested from the same starting point
                settings.reset(key)
                pump(0.1)
                self.assertNotEqual(before, after, f'{value!r} did not change [{section}] {option}')
                if metadata:
                    kind, allowed = metadata[0].get((section, option), (option_type(metadata, section, option), []))
                    if kind == 'bool':
                        self.assertIn(after, ('true', 'false'))
                    if allowed:
                        self.assertIn(after, allowed)


class Behaviour(BridgeTestCase):

    def test_alt_tab_survives_an_empty_switch_windows(self):
        self.set('org.gnome.desktop.wm.keybindings', 'switch-applications', ['<Super>Tab', '<Alt>Tab'])
        self.set('org.gnome.desktop.wm.keybindings', 'switch-windows', [])
        self.assertEqual(self.option('switcher', 'next_view'), '<alt> KEY_TAB')

    def test_keybindings_sharing_an_option_are_merged(self):
        self.set('org.gnome.desktop.wm.keybindings', 'always-on-top', ['<Super>t'])
        self.set('org.gnome.desktop.wm.keybindings', 'toggle-above', ['<Super>x'])
        self.assertEqual(self.option('wm-actions', 'toggle_always_on_top'), '<super> KEY_T | <super> KEY_X')

    def test_maximize_and_restore_use_the_grid(self):
        self.set('org.gnome.desktop.wm.keybindings', 'maximize', ['<Super>Up'])
        self.set('org.gnome.desktop.wm.keybindings', 'unmaximize', ['<Super>Down'])
        self.assertEqual(self.option('grid', 'slot_c'), '<super> KEY_UP')
        self.assertEqual(self.option('grid', 'restore'), '<super> KEY_DOWN')

    def test_workspaces_are_numbered_from_one(self):
        self.set('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-1', ['<Super>Home'])
        self.set('org.gnome.desktop.wm.keybindings', 'move-to-workspace-12', ['<Super><Shift>F12'])
        self.assertEqual(self.option('vswitch', 'binding_1'), '<super> KEY_HOME')
        self.assertEqual(self.option('vswitch', 'send_win_12'), '<super> <shift> KEY_F12')
        self.assertIsNone(self.option('vswitch', 'binding_0'))

    def test_left_handed_is_on_if_either_device_asks(self):
        self.set('org.gnome.desktop.peripherals.touchpad', 'left-handed', 'mouse')
        self.set('org.gnome.desktop.peripherals.mouse', 'left-handed', True)
        self.assertEqual(self.option('input', 'left_handed_mode'), 'true')
        self.set('org.gnome.desktop.peripherals.mouse', 'left-handed', False)
        self.assertEqual(self.option('input', 'left_handed_mode'), 'false')
        self.set('org.gnome.desktop.peripherals.touchpad', 'left-handed', 'left')
        self.assertEqual(self.option('input', 'left_handed_mode'), 'true')

    def test_mouse_and_touchpad_natural_scroll_are_separate(self):
        self.set('org.gnome.desktop.peripherals.mouse', 'natural-scroll', True)
        self.set('org.gnome.desktop.peripherals.touchpad', 'natural-scroll', False)
        self.assertEqual(self.option('input', 'mouse_natural_scroll'), 'true')
        self.assertEqual(self.option('input', 'natural_scroll'), 'false')

    def test_key_repeat_off_writes_rate_zero(self):
        self.set('org.gnome.desktop.peripherals.keyboard', 'repeat-interval', 20)
        self.assertEqual(self.option('input', 'kb_repeat_rate'), '50')
        self.set('org.gnome.desktop.peripherals.keyboard', 'repeat', False)
        self.assertEqual(self.option('input', 'kb_repeat_rate'), '0')
        self.set('org.gnome.desktop.peripherals.keyboard', 'repeat', True)
        self.assertEqual(self.option('input', 'kb_repeat_rate'), '50')

    def test_custom_acceleration_falls_back_to_default(self):
        self.set('org.gnome.desktop.peripherals.mouse', 'accel-profile', 'flat')
        self.set('org.gnome.desktop.peripherals.mouse', 'accel-profile', 'custom')
        self.assertEqual(self.option('input', 'mouse_accel_profile'), 'default')

    def test_layout_variants_go_to_xkb_variant(self):
        self.set('org.gnome.desktop.input-sources', 'sources', [('xkb', 'us+dvorak'), ('xkb', 'de')])
        self.assertEqual(self.option('input', 'xkb_layout'), 'us,de')
        self.assertEqual(self.option('input', 'xkb_variant'), 'dvorak,')

    def test_button_layout(self):
        self.set('org.gnome.desktop.wm.preferences', 'button-layout', 'appmenu:minimize,maximize,close')
        self.assertEqual(self.option('decoration', 'button_order'), 'minimize maximize close')

    def test_cursor_reaches_ini_and_environment_file(self):
        self.set('org.gnome.desktop.interface', 'cursor-theme', 'Some Cursor Theme')
        self.assertEqual(self.option('input', 'cursor_theme'), 'Some Cursor Theme')
        environment = (self.ini.parent / 'environment').read_text()
        self.assertIn("XCURSOR_THEME='Some Cursor Theme'", environment)



class StartupWrites(BridgeTestCase):
    """The startup sync writes wayfire.ini once, after Wayfire has settled."""

    def start_bridge(self):
        # Change something the sync will set back, then start the bridge
        # without the helper's immediate release
        text = self.ini.read_text()
        self.assertIn('\nvheight = 2\n', text)
        self.ini.write_text(text.replace('\nvheight = 2\n', '\nvheight = 7\n', 1))
        self.at_start = self.ini.read_text()
        original = bridge_module.ConfigManager
        bridge_module.ConfigManager = lambda: ConfigManager(self.ini)
        try:
            return bridge_module.WayfireBridge()
        finally:
            bridge_module.ConfigManager = original

    def test_nothing_is_written_until_the_delay_has_passed(self):
        self.assertEqual(self.ini.read_text(), self.at_start)
        self.bridge.release_startup_saves()
        self.assertNotEqual(self.option('core', 'vheight'), '7')

    def test_changes_after_startup_are_written_straight_away(self):
        self.bridge.release_startup_saves()
        self.set('org.gnome.desktop.wm.preferences', 'num-workspaces', 6)
        self.assertEqual((self.option('core', 'vwidth'), self.option('core', 'vheight')), ('3', '2'))


class WorkspaceGrid(BridgeTestCase):
    """The workspace count sets both vwidth and vheight, replacing a hand-set vheight."""

    def prepare_ini(self):
        super().prepare_ini()
        text = self.ini.read_text()
        self.assertIn('\nvheight = 2\n', text)
        self.ini.write_text(text.replace('\nvheight = 2\n', '\nvheight = 3\n', 1))

    def test_squarest_grid_or_one_row(self):
        for count, grid in ((4, ('2', '2')), (5, ('5', '1')), (6, ('3', '2')),
                            (9, ('3', '3')), (1, ('1', '1'))):
            with self.subTest(workspaces=count):
                self.set('org.gnome.desktop.wm.preferences', 'num-workspaces', count, wait=0.1)
                self.assertEqual((self.option('core', 'vwidth'), self.option('core', 'vheight')), grid)


if __name__ == '__main__':
    unittest.main()
