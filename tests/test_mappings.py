"""The GSettings -> wayfire.ini table against Wayfire's own option definitions."""
import unittest

from tests.helpers import (METADATA_DIR, BRIDGE_SCHEMAS, Gio, libevdev_key_valid,
                           missing_schemas, option_type, wayfire_metadata)
from wayfire_bridge.mappings import GSETTINGS_MAPPINGS
from wayfire_bridge.media_keys import MEDIA_KEY_MAPPINGS
from wayfire_bridge.budgie_wm_actions import BUDGIE_WM_ACTION_MAPPINGS
from wayfire_bridge.transforms import TransformFunctions as T


@unittest.skipUnless(METADATA_DIR.is_dir(), f'Wayfire metadata not found in {METADATA_DIR}')
class AgainstWayfireMetadata(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.metadata = wayfire_metadata()

    def test_every_target_option_exists(self):
        for (schema, key), mapping in GSETTINGS_MAPPINGS.items():
            with self.subTest(f'{schema}::{key}'):
                self.assertIsNotNone(option_type(self.metadata, mapping['section'], mapping['option']),
                                     f"[{mapping['section']}] {mapping['option']} is not a Wayfire option")

    def test_keybindings_go_to_binding_options(self):
        for (schema, key), mapping in GSETTINGS_MAPPINGS.items():
            if mapping['transform'] != 'keybinding':
                continue
            kind = option_type(self.metadata, mapping['section'], mapping['option'])
            with self.subTest(f'{schema}::{key}'):
                # Wayfire "key" options take one binding: the bridge must pick one
                if kind == 'key':
                    self.assertTrue(mapping.get('single_binding'), 'key option needs single_binding')
                else:
                    self.assertEqual(kind, 'activator')

    def test_plugin_activator_targets_exist_when_the_plugin_is_installed(self):
        for key, mapping in MEDIA_KEY_MAPPINGS.items():
            if 'activator' not in mapping:
                continue
            section, option = mapping['activator']
            if not (METADATA_DIR / f'{section}.xml').exists():
                continue  # plugin not installed here
            with self.subTest(key):
                self.assertEqual(option_type(self.metadata, section, option), 'activator')


class Table(unittest.TestCase):

    def test_every_transform_exists(self):
        for (schema, key), mapping in GSETTINGS_MAPPINGS.items():
            with self.subTest(f'{schema}::{key}'):
                self.assertTrue(callable(getattr(T, mapping.get('transform', 'str'), None)))

    def test_media_entries_bind_something(self):
        for key, mapping in MEDIA_KEY_MAPPINGS.items():
            with self.subTest(key):
                self.assertTrue(mapping.get('command') or mapping.get('fallback_command')
                                or mapping.get('command_gsetting') or mapping.get('activator')
                                or mapping.get('unsupported'))

    def test_command_names_are_unique(self):
        names = [m['command_name'] for m in (*MEDIA_KEY_MAPPINGS.values(), *BUDGIE_WM_ACTION_MAPPINGS.values())]
        self.assertEqual(len(names), len(set(names)))


@unittest.skipIf(missing_schemas(), 'GSettings schemas not installed')
class DefaultBindings(unittest.TestCase):

    def test_every_default_binding_converts_to_a_valid_key(self):
        valid = libevdev_key_valid()
        if valid is None:
            self.skipTest('libevdev not found')
        schemas = [s for s in BRIDGE_SCHEMAS if s.endswith(('keybindings', 'media-keys', 'budgie-wm'))]
        for schema in schemas:
            settings = Gio.Settings.new(schema)
            for key in settings.get_property('settings-schema').list_keys():
                value = settings.get_default_value(key)
                if value is None or value.get_type_string() != 'as':
                    continue
                for binding in value.unpack():
                    converted = T.convert_keybinding(binding)
                    if not converted:
                        continue  # disabled, or a keysym with no evdev key
                    with self.subTest(f'{schema}::{key} {binding}'):
                        self.assertTrue(valid(converted.split()[-1]), converted)


if __name__ == '__main__':
    unittest.main()
