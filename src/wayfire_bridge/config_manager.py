"""
Configuration file management for Wayfire Bridge
"""

import configparser
from pathlib import Path

from .logging_config import get_logger

log = get_logger(__name__)


class ConfigManager:
    """Manages wayfire.ini configuration file"""

    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = Path.home() / '.config' / 'budgie-desktop' / 'wayfire' / 'wayfire.ini'
        else:
            self.config_path = Path(config_path)

        # Changes made since the last save, replayed onto the file if it was
        # edited externally (WCM, a text editor) in the meantime
        self._pending = []
        # (mtime, size) of the file as last read or written by us
        self._disk_stamp = None

        # Load existing config or create new one
        if self.config_path.exists():
            try:
                self._load()
                log.info("Loaded existing config from %s", self.config_path)
            except configparser.Error as e:
                log.error("Error reading config file: %s", e)
                log.warning("Creating backup and starting with fresh config")
                # Backup the problematic file
                backup_path = self.config_path.with_suffix('.ini.backup')
                try:
                    self.config_path.rename(backup_path)
                    log.info("Backed up problematic config to %s", backup_path)
                except Exception:
                    log.exception("Could not backup config file")
                self.config = self._new_parser()
        else:
            self.config = self._new_parser()
            log.info("Will create new config at %s", self.config_path)

        self._ensure_required()

    @staticmethod
    def _new_parser():
        # strict=False allows duplicate keys (last one wins)
        config = configparser.ConfigParser(
            interpolation=None,
            strict=False,
            allow_no_value=True  # Allow keys without values
        )
        config.optionxform = str  # Preserve case sensitivity
        return config

    def _load(self):
        """Read wayfire.ini from disk, replacing the in-memory config"""
        config = self._new_parser()
        config.read(self.config_path)
        self.config = config
        self._disk_stamp = self._stamp()

    def _stamp(self):
        try:
            st = self.config_path.stat()
            return (st.st_mtime_ns, st.st_size)
        except FileNotFoundError:
            return None

    def _ensure_required(self):
        # Ensure critical autostart section exists for budgie-desktop
        self._ensure_autostart_section()
        self._normalize_plugins_list()

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    def set_value(self, section: str, option: str, value: str):
        """Set a configuration value"""
        self._pending.append(('set', section, option, value))
        self._set_value(section, option, value)

    def _set_value(self, section: str, option: str, value: str):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][option] = value

    def get_value(self, section: str, option: str, default=None):
        """Get a configuration value"""
        if section in self.config and option in self.config[section]:
            return self.config[section][option]
        return default

    def remove_option(self, section: str, option: str):
        """Remove a configuration option"""
        self._pending.append(('remove_option', section, option))
        self._remove_option(section, option)

    def _remove_option(self, section: str, option: str):
        if section in self.config and option in self.config[section]:
            del self.config[section][option]

    def remove_section(self, section: str):
        """Remove a whole configuration section"""
        self._pending.append(('remove_section', section))
        self.config.remove_section(section)

    def has_option(self, section: str, option: str) -> bool:
        """Check if an option exists"""
        return section in self.config and option in self.config[section]

    def ensure_wm_plugins(self):
        """Ensure all plugins required for WM keybinding mappings are loaded.

        Called once during bridge_config() initial sync. Covers:
        wm-actions  — minimize, maximize, fullscreen, sticky, send_to_back etc.
        grid        — slot_l, slot_c, slot_r, restore, edge snapping
        move        — enable_snap
        place       — placement mode
        switcher    — next_view, prev_view
        fast-switcher — activate, activate_backward
        xdg-activation — lets apps pass focus to an existing window (a link
                         clicked elsewhere raising the browser, a notification
                         raising its app)
        """
        required = ['wm-actions', 'grid', 'move', 'place', 'switcher', 'fast-switcher',
                    'xdg-activation']
        for plugin in required:
            self.ensure_plugin(plugin)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_autostart_section(self):
        """Ensure the critical autostart section exists for budgie-desktop"""
        if 'autostart' not in self.config:
            self.config['autostart'] = {}

        autostart = self.config['autostart']

        if autostart.get('desktop') != 'budgie-desktop':
            log.debug("Creating/updating autostart section for budgie-desktop")

            autostart.setdefault(
                '0_env',
                'dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY XAUTHORITY',
            )
            autostart.setdefault('autostart_wf_shell', 'false')
            autostart.setdefault('portal', '/usr/libexec/xdg-desktop-portal')
            autostart.setdefault('desktop', 'budgie-desktop')

            log.debug("Autostart section configured for budgie-desktop")
        else:
            log.debug("Autostart section already configured correctly")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _merge_external_changes(self):
        """Re-read wayfire.ini if it was edited since we last read or wrote it.

        Without this, every save wrote back the copy loaded at login and
        silently undid edits made meanwhile in WCM or a text editor. The
        bridge's own changes since the last save are replayed on top.
        """
        if self._disk_stamp is None or self._stamp() in (None, self._disk_stamp):
            return
        log.info("%s changed on disk, merging before saving", self.config_path)
        try:
            self._load()
        except configparser.Error:
            log.exception("Could not re-read edited %s, keeping in-memory copy", self.config_path)
            return
        for op, *args in self._pending:
            if op == 'set':
                self._set_value(*args)
            elif op == 'remove_option':
                self._remove_option(*args)
            elif op == 'remove_section':
                self.config.remove_section(*args)
            elif op == 'ensure_plugin':
                self._ensure_plugin(*args)
            elif op == 'remove_plugin':
                self._remove_plugin(*args)
        self._ensure_required()

    def save(self):
        """Write configuration to wayfire.ini"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            self._merge_external_changes()

            log.debug("Saving configuration to %s", self.config_path)

            with open(self.config_path, 'w') as f:
                self.config.write(f)
                f.flush()

            self._pending.clear()
            self._disk_stamp = self._stamp()
            log.debug("Configuration written to %s", self.config_path)

        except Exception:
            log.exception("Error saving config to %s", self.config_path)

    def _get_plugins_list(self) -> list:
        """Return the current plugins list as a Python list of strings."""
        if 'core' not in self.config:
            return []
        raw = self.config['core'].get('plugins', '')
        # Older configs spread the list over lines with "\" continuations
        return raw.replace('\\', ' ').split()

    def _set_plugins_list(self, plugins: list):
        """Write a plugins list back to [core] plugins, on one line.

        A multi-line list with backslash continuations loads in Wayfire but reaches
        WCM with tabs between the names, so WCM shows those plugins as
        unloaded. A plain space-separated line works for both.
        """
        if 'core' not in self.config:
            self.config['core'] = {}
        self.config['core']['plugins'] = ' '.join(plugins)

    def _normalize_plugins_list(self):
        """Rewrite a multi-line plugins list as a single line."""
        raw = self.get_value('core', 'plugins')
        if raw and ('\\' in raw or '\n' in raw or '\t' in raw):
            self._set_plugins_list(self._get_plugins_list())

    def ensure_plugin(self, plugin_name: str):
        """Add plugin_name to [core] plugins if not already present."""
        self._pending.append(('ensure_plugin', plugin_name))
        self._ensure_plugin(plugin_name)

    def _ensure_plugin(self, plugin_name: str):
        plugins = self._get_plugins_list()
        if plugin_name not in plugins:
            plugins.append(plugin_name)
            self._set_plugins_list(plugins)
            log.info("Added plugin %s to [core] plugins", plugin_name)

    def remove_plugin(self, plugin_name: str):
        """Remove plugin_name from [core] plugins if present."""
        self._pending.append(('remove_plugin', plugin_name))
        self._remove_plugin(plugin_name)

    def _remove_plugin(self, plugin_name: str):
        plugins = self._get_plugins_list()
        if plugin_name in plugins:
            plugins.remove(plugin_name)
            self._set_plugins_list(plugins)
            log.info("Removed plugin %s from [core] plugins", plugin_name)