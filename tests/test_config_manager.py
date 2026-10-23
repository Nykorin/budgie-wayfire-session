"""Reading and writing wayfire.ini (wayfire_bridge/config_manager.py)."""
import os
import tempfile
import time
import unittest
from pathlib import Path

from tests.helpers import plugin_list, read_ini
from wayfire_bridge.config_manager import ConfigManager


class ConfigManagerTestCase(unittest.TestCase):

    initial = "[core]\nplugins = alpha command\n\n[animate]\nduration = 300ms circle\n"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ini = Path(self._tmp.name) / 'wayfire.ini'
        self.ini.write_text(self.initial)
        self.manager = ConfigManager(self.ini)

    def tearDown(self):
        self._tmp.cleanup()

    def edit_on_disk(self, old, new):
        """Change the file behind the manager's back, as WCM or an editor would."""
        text = self.ini.read_text()
        self.assertIn(old, text)
        time.sleep(0.01)  # a different mtime even on coarse filesystems
        self.ini.write_text(text.replace(old, new, 1))
        os.utime(self.ini)

    def raw_plugins_line(self):
        return next(line for line in self.ini.read_text().splitlines() if line.startswith('plugins'))


class ExternalEdits(ConfigManagerTestCase):

    def test_edit_made_after_load_survives_a_save(self):
        self.manager.save()
        self.edit_on_disk('duration = 300ms circle', 'duration = 650ms circle')
        self.manager.set_value('core', 'vwidth', '5')
        self.manager.save()
        config = read_ini(self.ini)
        self.assertEqual(config['animate']['duration'], '650ms circle')
        self.assertEqual(config['core']['vwidth'], '5')

    def test_plugins_added_externally_and_by_the_bridge_are_both_kept(self):
        self.manager.save()
        self.edit_on_disk('plugins = alpha command', 'plugins = alpha command blur')
        self.manager.ensure_plugin('follow-focus')
        self.manager.save()
        self.assertEqual(plugin_list(read_ini(self.ini)), ['alpha', 'command', 'blur', 'follow-focus'])

    def test_removals_are_replayed(self):
        self.manager.set_value('mag', 'toggle', '<super> KEY_M')
        self.manager.save()
        self.edit_on_disk('[animate]', '[extra]\nkept = yes\n\n[animate]')
        self.manager.remove_section('mag')
        self.manager.remove_plugin('command')
        self.manager.save()
        config = read_ini(self.ini)
        self.assertFalse(config.has_section('mag'))
        self.assertEqual(config['extra']['kept'], 'yes')
        self.assertNotIn('command', plugin_list(config))

    def test_changes_already_saved_are_not_replayed(self):
        self.manager.set_value('core', 'vwidth', '6')
        self.manager.save()
        self.edit_on_disk('vwidth = 6', 'vwidth = 2')
        self.manager.set_value('input', 'cursor_size', '32')
        self.manager.save()
        self.assertEqual(read_ini(self.ini)['core']['vwidth'], '2')

    def test_autostart_section_is_always_present(self):
        self.manager.save()
        self.assertEqual(read_ini(self.ini)['autostart']['desktop'], 'budgie-desktop')


class PluginList(ConfigManagerTestCase):

    initial = "[core]\nplugins = \\\n  alpha \\\n  command\n"

    def test_multi_line_list_is_rewritten_on_one_line(self):
        self.manager.save()
        self.assertEqual(self.raw_plugins_line(), 'plugins = alpha command')

    def test_tab_separated_list_from_wcm_is_rewritten(self):
        self.manager.save()
        self.edit_on_disk('plugins = alpha command', 'plugins = alpha \tcommand \tgrid')
        self.manager.set_value('core', 'vwidth', '4')
        self.manager.save()
        self.assertEqual(self.raw_plugins_line(), 'plugins = alpha command grid')

    def test_ensure_and_remove_keep_one_line(self):
        self.manager.ensure_plugin('grid')
        self.manager.ensure_plugin('grid')
        self.manager.remove_plugin('alpha')
        self.manager.save()
        self.assertEqual(self.raw_plugins_line(), 'plugins = command grid')


if __name__ == '__main__':
    unittest.main()
