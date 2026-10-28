"""Shared test setup.

GSettings live in memory (GSETTINGS_BACKEND=memory), so tests never touch the
desktop's settings; each bridge test runs on a temporary copy of the shipped
wayfire.ini. Tests that need something only a Budgie/Wayfire system has (the
GSettings schemas, Wayfire's option metadata, libevdev) skip without it.
"""
import configparser
import ctypes
import ctypes.util
import logging
import os
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

# Must be set before GLib is loaded
os.environ['GSETTINGS_BACKEND'] = 'memory'
# What the bridge keeps in ~/.local/state (the shipped config's fingerprint)
# goes to a folder that is removed when the tests end
_STATE_HOME = tempfile.TemporaryDirectory()
os.environ['XDG_STATE_HOME'] = _STATE_HOME.name
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))

from gi.repository import Gio, GLib  # noqa: E402

from wayfire_bridge import bridge as bridge_module  # noqa: E402
from wayfire_bridge.config_manager import ConfigManager  # noqa: E402

# The bridge's warnings (e.g. "none of [...] is installed") are expected here
logging.getLogger('wayfire_bridge').setLevel(logging.CRITICAL)

# WAYFIRE_METADATA_DIR checks against another Wayfire build's options
METADATA_DIR = Path(os.environ.get('WAYFIRE_METADATA_DIR') or '/usr/share/wayfire/metadata')

BRIDGE_SCHEMAS = (
    'org.gnome.desktop.wm.keybindings',
    'org.gnome.desktop.wm.preferences',
    'org.gnome.desktop.interface',
    'org.gnome.desktop.peripherals.mouse',
    'org.gnome.desktop.peripherals.touchpad',
    'org.gnome.desktop.peripherals.keyboard',
    'org.gnome.desktop.input-sources',
    'org.gnome.mutter',
    'org.gnome.mutter.keybindings',
    'com.solus-project.budgie-wm',
    'org.buddiesofbudgie.settings-daemon.plugins.media-keys',
)
CUSTOM_KEYBINDING_SCHEMA = 'org.buddiesofbudgie.settings-daemon.plugins.media-keys.custom-keybinding'


def schema_installed(schema):
    return Gio.SettingsSchemaSource.get_default().lookup(schema, True) is not None


def missing_schemas(schemas=BRIDGE_SCHEMAS):
    return [s for s in schemas if not schema_installed(s)]


def pump(seconds=0.2):
    """Run the GLib main loop for a while so change signals are delivered."""
    context = GLib.MainContext.default()
    end = GLib.get_monotonic_time() + int(seconds * 1e6)
    while GLib.get_monotonic_time() < end:
        context.iteration(False)


def read_ini(path):
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(path)
    return config


def plugin_list(config):
    return config['core']['plugins'].replace('\\', ' ').split()


def wayfire_metadata():
    """{(section, option): (type, [allowed values])} and {section: [dynamic prefixes]}."""
    options, prefixes = {}, {}
    for path in METADATA_DIR.glob('*.xml'):
        for plugin in ET.parse(path).getroot().iter('plugin'):
            section = plugin.get('name')
            for option in plugin.iter('option'):
                values = [d.findtext('value') for d in option.iter('desc') if d.findtext('value') is not None]
                options[(section, option.get('name'))] = (option.get('type'), values)
                for entry in option.iter('entry'):
                    prefixes.setdefault(section, []).append((entry.get('prefix'), entry.get('type')))
    return options, prefixes


def option_type(metadata, section, option):
    """Wayfire's type for an option, including dynamic-list entries (binding_N, ...)."""
    options, prefixes = metadata
    if (section, option) in options:
        return options[(section, option)][0]
    for prefix, entry_type in prefixes.get(section, []):
        if option.startswith(prefix):
            return entry_type
    return None


def libevdev_key_valid():
    """A function telling whether libevdev (which Wayfire uses) knows a KEY_ name, or None."""
    name = ctypes.util.find_library('evdev')
    if not name:
        return None
    from_name = ctypes.CDLL(name).libevdev_event_code_from_name
    from_name.argtypes = [ctypes.c_uint, ctypes.c_char_p]
    return lambda key: from_name(1, key.encode()) >= 0  # 1 = EV_KEY


class BridgeTestCase(unittest.TestCase):
    """A bridge running on a temporary copy of the shipped wayfire.ini.

    GSettings keys changed through self.set() are reset after each test.
    """

    initial_ini = SRC / 'wayfire.ini'

    def setUp(self):
        missing = missing_schemas()
        if missing:
            self.skipTest(f"GSettings schemas not installed: {', '.join(missing)}")
        self._tmp = tempfile.TemporaryDirectory()
        self.ini = Path(self._tmp.name) / 'wayfire.ini'
        self.prepare_ini()
        self._changed = []
        self.bridge = self.start_bridge()

    def prepare_ini(self):
        shutil.copy(self.initial_ini, self.ini)

    def new_bridge(self):
        """A bridge on self.ini, its startup saves still held."""
        original = bridge_module.ConfigManager, bridge_module.check_shipped_config
        bridge_module.ConfigManager = lambda: ConfigManager(self.ini)
        # The real one would compare with the installed config and could
        # show a notification
        bridge_module.check_shipped_config = lambda config_path: None
        try:
            return bridge_module.WayfireBridge()
        finally:
            bridge_module.ConfigManager, bridge_module.check_shipped_config = original

    def start_bridge(self):
        bridge = self.new_bridge()
        # What Wayfire would see 3 s after login
        bridge.release_startup_saves()
        return bridge

    def tearDown(self):
        # Earlier bridges stay connected to GSettings: keep them from writing
        # into this test's folder once it is gone
        self.bridge.config_manager.save = lambda: None
        self.bridge.write_environment_file = lambda: None
        for settings, key in reversed(self._changed):
            settings.reset(key)
        pump(0.05)
        self._tmp.cleanup()

    def settings(self, schema, path=None):
        return Gio.Settings.new_with_path(schema, path) if path else Gio.Settings.new(schema)

    def set(self, schema, key, value, path=None, wait=0.2):
        """Set a GSettings key (typed like its current value) and let the bridge react."""
        settings = self.settings(schema, path)
        variant_type = settings.get_value(key).get_type_string()
        settings.set_value(key, GLib.Variant(variant_type, value))
        self._changed.append((settings, key))
        pump(wait)

    def config(self):
        return read_ini(self.ini)

    def option(self, section, option):
        return self.config().get(section, option, fallback=None)
