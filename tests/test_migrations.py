"""Configs written by older versions are cleaned up when the bridge starts."""
import unittest

from tests.helpers import BridgeTestCase, plugin_list

OLD_CONFIG = """\
[core]
plugins = \\
\talpha \\
\tcommand \\
\tvswitch
vwidth = 4
gtk_theme = Adwaita

[input]
touchpad_natural_scroll = true
touchpad_left_handed_mode = false
disable_while_typing = true
touchpad_send_events = enabled
tap_button_map = lrm
xkb_repeat_delay = 500

[grid]
mouse_snap = true

[vswitch]
vwidth = 6
vheight = 2
binding_0 = <super> KEY_HOME
binding_win_left = <super> <shift> KEY_LEFT

[command]
binding_close = KEY_Q ALT
command_close = wm-actions close
binding_move_left = KEY_LEFT SHIFT LOGO
command_move_left = vswitch-move left
binding_mine = <super> KEY_M
command_mine = my-own-script

[notifications]
vertical_position = top

[gamma]
enabled = false

[decoration]
title_height = 25
"""


class OldConfig(BridgeTestCase):

    def prepare_ini(self):
        self.ini.write_text(OLD_CONFIG)

    def test_options_wayfire_does_not_have_are_removed(self):
        config = self.config()
        for section, option in (('core', 'gtk_theme'), ('input', 'touchpad_natural_scroll'),
                                ('input', 'touchpad_left_handed_mode'), ('input', 'disable_while_typing'),
                                ('input', 'touchpad_send_events'), ('input', 'tap_button_map'),
                                ('input', 'xkb_repeat_delay'), ('grid', 'mouse_snap'),
                                ('vswitch', 'binding_0'), ('vswitch', 'binding_win_left')):
            with self.subTest(f'[{section}] {option}'):
                self.assertFalse(config.has_option(section, option))
        self.assertFalse(config.has_section('notifications'))
        self.assertFalse(config.has_section('gamma'))

    def test_workspace_grid_moves_to_core(self):
        config = self.config()
        self.assertFalse(config.has_option('vswitch', 'vwidth'))
        self.assertFalse(config.has_option('vswitch', 'vheight'))
        self.assertEqual(config.get('core', 'vheight'), '2')
        self.assertIsNotNone(config.get('core', 'vwidth'))

    def test_broken_command_entries_are_removed_but_not_the_users_own(self):
        config = self.config()
        for name in ('close', 'move_left'):
            self.assertFalse(config.has_option('command', f'binding_{name}'))
            self.assertFalse(config.has_option('command', f'command_{name}'))
        self.assertEqual(config.get('command', 'command_mine'), 'my-own-script')

    def test_plugin_list_becomes_one_line_with_the_required_plugins(self):
        raw = next(line for line in self.ini.read_text().splitlines() if line.startswith('plugins'))
        self.assertNotIn('\\', raw)
        self.assertNotIn('\t', raw)
        plugins = plugin_list(self.config())
        for plugin in ('alpha', 'command', 'vswitch', 'wm-actions', 'grid', 'move', 'place',
                       'switcher', 'fast-switcher', 'xdg-activation'):
            self.assertIn(plugin, plugins)

    def test_unrelated_settings_are_kept(self):
        self.assertEqual(self.option('decoration', 'title_height'), '25')

    def test_autostart_section_is_added(self):
        self.assertEqual(self.option('autostart', 'desktop'), 'budgie-desktop')


if __name__ == '__main__':
    unittest.main()
