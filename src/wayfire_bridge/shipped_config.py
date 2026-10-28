"""
A new build's default wayfire.ini, offered next to the user's

The launcher copies the shipped wayfire.ini only at the first login, so
bindings a later build adds or renames never reach an existing config. When
the shipped file changes, it is saved once as wayfire.ini.new beside the
user's, and a notification says so. A fingerprint of the shipped file, kept
in the state directory, marks it as handled: the copy isn't made again until
a build ships a different one.
"""

import hashlib
import os
from pathlib import Path

import gi

gi.require_version('Gio', '2.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gio, GLib

from .logging_config import get_logger

log = get_logger(__name__)

SHIPPED_CONFIG = Path('budgie-desktop') / 'wayfire' / 'wayfire.ini'
MARKER_NAME = 'shipped-wayfire.ini.sha256'


def find_shipped_config():
    """The installed default wayfire.ini, from the XDG data directories."""
    data_dirs = os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share'
    for data_dir in data_dirs.split(':'):
        path = Path(data_dir) / SHIPPED_CONFIG
        if data_dir and path.is_file():
            return path
    return None


def state_dir():
    state_home = os.environ.get('XDG_STATE_HOME') or Path.home() / '.local' / 'state'
    return Path(state_home) / 'budgie-wayfire'


def check_shipped_config(config_path, shipped=None, state=None):
    """Save a changed shipped config as <config>.new, once per change.

    Returns the path written, or None. A config that is still the shipped
    one (a first login) needs no copy; neither does a missing one.
    """
    shipped = shipped or find_shipped_config()
    if shipped is None:
        log.debug("No shipped wayfire.ini found, not checking for a new one")
        return None
    marker = Path(state or state_dir()) / MARKER_NAME

    data = shipped.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    try:
        if marker.read_text().strip() == digest:
            return None
    except FileNotFoundError:
        pass

    config_path = Path(config_path)
    new_path = None
    try:
        differs = config_path.read_bytes() != data
    except FileNotFoundError:
        differs = False
    if differs:
        new_path = config_path.with_name(config_path.name + '.new')
        partial = new_path.with_name(new_path.name + '.tmp')
        partial.write_bytes(data)
        partial.replace(new_path)
        log.info("The shipped wayfire.ini changed; saved it as %s", new_path)

    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(digest + '\n')
    return new_path


def notify_new_config(new_path):
    """Tell the user about new_path once the notification server is up."""
    home = str(Path.home())
    shown_dir = str(new_path.parent)
    if shown_dir.startswith(home + os.sep):
        shown_dir = '~' + shown_dir[len(home):]

    def on_appeared(connection, name, owner):
        Gio.bus_unwatch_name(watch_id)
        connection.call(
            'org.freedesktop.Notifications', '/org/freedesktop/Notifications',
            'org.freedesktop.Notifications', 'Notify',
            GLib.Variant('(susssasa{sv}i)', (
                'Budgie Wayfire', 0, 'dialog-information',
                'New default Wayfire config',
                f'{new_path.name} is in {shown_dir}/',
                [], {}, -1,
            )),
            None, Gio.DBusCallFlags.NONE, -1, None, _finish_notify,
        )

    watch_id = Gio.bus_watch_name(
        Gio.BusType.SESSION, 'org.freedesktop.Notifications',
        Gio.BusNameWatcherFlags.NONE, on_appeared, None)


def _finish_notify(connection, result):
    try:
        connection.call_finish(result)
    except GLib.Error:
        log.warning("Could not show the new config notification", exc_info=True)
