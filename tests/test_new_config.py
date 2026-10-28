"""A changed shipped wayfire.ini, saved once beside the user's as wayfire.ini.new."""
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from tests.helpers import SRC  # noqa: F401  (puts src/ on the path)
from wayfire_bridge import shipped_config
from wayfire_bridge.shipped_config import check_shipped_config


class NewShippedConfig(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.shipped = tmp / 'share' / 'wayfire.ini'
        self.shipped.parent.mkdir()
        self.shipped.write_text('[command]\nbinding_media_play = KEY_PLAYPAUSE\n')
        self.config = tmp / 'config' / 'wayfire.ini'
        self.config.parent.mkdir()
        self.new = self.config.with_name('wayfire.ini.new')
        self.state = tmp / 'state'

    def tearDown(self):
        self._tmp.cleanup()

    def check(self):
        return check_shipped_config(self.config, shipped=self.shipped, state=self.state)

    def test_first_login_with_the_shipped_config_needs_no_copy(self):
        self.config.write_bytes(self.shipped.read_bytes())
        self.assertIsNone(self.check())
        self.assertFalse(self.new.exists())
        self.assertTrue((self.state / shipped_config.MARKER_NAME).exists())

    def test_saved_once_for_a_config_from_an_older_build(self):
        self.config.write_text('[command]\nbinding_on_play = KEY_PLAYPAUSE\n')
        self.assertEqual(self.check(), self.new)
        self.assertEqual(self.new.read_text(), self.shipped.read_text())
        self.assertEqual(self.config.read_text(), '[command]\nbinding_on_play = KEY_PLAYPAUSE\n')
        # Handled: deleting the copy doesn't bring it back
        self.new.unlink()
        self.assertIsNone(self.check())
        self.assertFalse(self.new.exists())

    def test_saved_again_when_a_later_build_changes_it(self):
        self.config.write_text('[command]\n')
        self.check()
        self.shipped.write_text('[command]\nbinding_media_next = KEY_NEXTSONG\n')
        self.assertEqual(self.check(), self.new)
        self.assertEqual(self.new.read_text(), self.shipped.read_text())

    def test_no_config_yet(self):
        self.assertIsNone(self.check())
        self.assertFalse(self.new.exists())

    def test_finds_the_installed_config_in_the_data_dirs(self):
        share = Path(self._tmp.name) / 'data'
        target = share / shipped_config.SHIPPED_CONFIG
        target.parent.mkdir(parents=True)
        target.write_text('')
        with unittest.mock.patch.dict('os.environ', {'XDG_DATA_DIRS': f'/nonexistent:{share}'}):
            self.assertEqual(shipped_config.find_shipped_config(), target)
