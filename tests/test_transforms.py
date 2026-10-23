"""Value conversions from GSettings to Wayfire (wayfire_bridge/transforms.py)."""
import inspect
import re
import unittest

from tests.helpers import libevdev_key_valid
from wayfire_bridge.transforms import TransformFunctions as T, split_keyboard_layout, format_keyboard_layout, workspace_grid


class KeybindingTests(unittest.TestCase):

    def test_modifiers_come_first_in_wayfire_order(self):
        self.assertEqual(T.convert_keybinding('<Shift><Alt><Primary><Super>t'),
                         '<super> <ctrl> <alt> <shift> KEY_T')

    def test_key_names_that_differ_from_the_keysym(self):
        cases = {
            '<Super>period': '<super> KEY_DOT',
            '<Super>bracketleft': '<super> KEY_LEFTBRACE',
            '<Super>Above_Tab': '<super> KEY_GRAVE',
            'Print': 'KEY_SYSRQ',
            '<Super>Return': '<super> KEY_ENTER',
            'XF86AudioPlay': 'KEY_PLAYPAUSE',
            'XF86AudioPause': 'KEY_PAUSECD',
            'XF86KbdBrightnessUp': 'KEY_KBDILLUMUP',
            'XF86ScreenSaver': 'KEY_COFFEE',
            'XF86LaunchB': 'KEY_ALL_APPLICATIONS',
            'Super_L': 'KEY_LEFTMETA',
        }
        for gnome, wayfire in cases.items():
            with self.subTest(gnome):
                self.assertEqual(T.convert_keybinding(gnome), wayfire)

    def test_keypad_keys(self):
        cases = {'KP_1': 'KEY_KP1', 'KP_Prior': 'KEY_KP9', 'KP_Next': 'KEY_KP3',
                 'KP_Begin': 'KEY_KP5', 'KP_Add': 'KEY_KPPLUS', 'KP_Enter': 'KEY_KPENTER'}
        for gnome, key in cases.items():
            with self.subTest(gnome):
                self.assertEqual(T.convert_keybinding(f'<Super>{gnome}'), f'<super> {key}')

    def test_unknown_xf86_keysym_is_skipped(self):
        # No evdev key exists for these: an empty result instead of KEY_XF86...
        self.assertEqual(T.convert_keybinding('XF86Hibernate'), '')
        self.assertEqual(T.convert_keybinding('XF86AudioRepeat'), '')

    def test_disabled_and_empty(self):
        self.assertEqual(T.convert_keybinding('disabled'), '')
        self.assertEqual(T.convert_keybinding(''), '')
        self.assertEqual(T.keybinding([]), '')

    def test_several_bindings_are_joined(self):
        self.assertEqual(T.keybinding(['<Alt>F4', '<Super>q']), '<alt> KEY_F4 | <super> KEY_Q')

    def test_every_table_entry_is_a_name_libevdev_accepts(self):
        valid = libevdev_key_valid()
        if valid is None:
            self.skipTest('libevdev not found')
        table = re.findall(r"'([^']+)': '([A-Z0-9_]+)'", inspect.getsource(T.convert_keybinding))
        self.assertGreater(len(table), 50)
        for keysym, name in table:
            with self.subTest(keysym):
                self.assertTrue(valid(f'KEY_{name}'), f'KEY_{name}')


class ValueTests(unittest.TestCase):

    def test_button_layout(self):
        cases = {
            'appmenu:minimize,maximize,close': 'minimize maximize close',
            'close,minimize,maximize:': 'close minimize maximize',
            ':minimize,spacer,close': 'minimize close',
            'appmenu:': '',
        }
        for gnome, wayfire in cases.items():
            with self.subTest(gnome):
                self.assertEqual(T.button_layout(gnome), wayfire)

    def test_keyboard_layout_split_and_join(self):
        self.assertEqual(split_keyboard_layout('us(dvorak),de'), ('us,de', 'dvorak,'))
        self.assertEqual(split_keyboard_layout('us,de(neo)'), ('us,de', ',neo'))
        self.assertEqual(split_keyboard_layout('us'), ('us', ''))
        self.assertEqual(split_keyboard_layout(None), ('', ''))
        self.assertEqual(split_keyboard_layout(format_keyboard_layout('us,de', 'dvorak,')), ('us,de', 'dvorak,'))

    def test_workspace_grid_is_the_squarest_exact_fit(self):
        cases = {1: (1, 1), 2: (2, 1), 3: (3, 1), 4: (2, 2), 5: (5, 1), 6: (3, 2), 7: (7, 1),
                 8: (4, 2), 9: (3, 3), 10: (5, 2), 12: (4, 3), 16: (4, 4), 0: (1, 1)}
        for count, grid in cases.items():
            with self.subTest(workspaces=count):
                self.assertEqual(workspace_grid(count), grid)

    def test_touchpad_values(self):
        self.assertEqual(T.click_method('fingers'), 'clickfinger')
        self.assertEqual(T.click_method('areas'), 'button-areas')
        self.assertEqual(T.click_method('default'), 'default')
        self.assertEqual(T.send_events('disabled-on-external-mouse'), 'true')
        self.assertEqual(T.send_events('disabled'), 'false')
        self.assertEqual(T.send_events('enabled'), 'false')
        self.assertEqual(T.touchpad_left_handed('left'), 'true')
        self.assertEqual(T.touchpad_left_handed('mouse'), 'mouse')

    def test_accel_profile(self):
        for profile in ('default', 'flat', 'adaptive'):
            self.assertEqual(T.accel_profile(profile), profile)
        self.assertEqual(T.accel_profile('custom'), 'default')

    def test_repeat_rate_from_interval(self):
        self.assertEqual(T.kb_repeat_rate(30), 33)
        self.assertEqual(T.kb_repeat_rate(28), 35)
        self.assertEqual(T.kb_repeat_rate(0), 30)

    def test_placement(self):
        self.assertEqual(T.placement_mode(True), 'center')
        self.assertEqual(T.placement_mode(False), 'cascade')


if __name__ == '__main__':
    unittest.main()
