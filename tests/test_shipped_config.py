"""The default wayfire.ini that meson installs."""
import unittest

from tests.helpers import METADATA_DIR, SRC, option_type, plugin_list, read_ini, wayfire_metadata

INI = SRC / 'wayfire.ini'

# Plugins that ship with Wayfire itself (anything else needs another package)
EXTRA_PLUGINS = {'fisheye', 'mag', 'follow-focus', 'wobbly'}


class ShippedConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = read_ini(INI)
        cls.text = INI.read_text()

    def test_plugin_list_is_one_space_separated_line(self):
        line = next(l for l in self.text.splitlines() if l.startswith('plugins'))
        self.assertNotIn('\\', line)
        self.assertNotIn('\t', line)

    def test_plugins_are_unique_and_need_no_extra_package(self):
        plugins = plugin_list(self.config)
        self.assertEqual(len(plugins), len(set(plugins)))
        self.assertFalse(set(plugins) & EXTRA_PLUGINS)
        self.assertIn('xdg-activation', plugins)

    def test_autostart_starts_budgie_and_the_bridge(self):
        self.assertEqual(self.config['autostart']['desktop'], 'budgie-desktop')
        self.assertEqual(self.config['autostart']['bridge'], '/usr/libexec/budgie-desktop/wayfire-bridge')

    def test_bindings_put_modifiers_first(self):
        for section in self.config.sections():
            for option, value in self.config[section].items():
                if 'KEY_' not in value:
                    continue
                for binding in value.split('|'):
                    words = binding.split()
                    with self.subTest(f'[{section}] {option}'):
                        self.assertTrue(words[-1].startswith('KEY_'), value)
                        self.assertTrue(all(w.startswith('<') for w in words[:-1]), value)

    @unittest.skipUnless(METADATA_DIR.is_dir(), f'Wayfire metadata not found in {METADATA_DIR}')
    def test_every_option_is_valid_for_wayfire(self):
        metadata = wayfire_metadata()
        sections_known = {section for section, _ in metadata[0]}
        for section in self.config.sections():
            if section not in sections_known:
                continue  # a plugin not installed here
            for option, value in self.config[section].items():
                if section == 'autostart' or (section == 'command' and option.startswith(('binding_', 'command_'))):
                    continue
                with self.subTest(f'[{section}] {option}'):
                    kind = option_type(metadata, section, option)
                    self.assertIsNotNone(kind, 'not a Wayfire option')
                    allowed = metadata[0].get((section, option), (None, []))[1]
                    if kind == 'bool':
                        self.assertIn(value, ('true', 'false'))
                    if allowed:
                        self.assertIn(value, allowed)


if __name__ == '__main__':
    unittest.main()
