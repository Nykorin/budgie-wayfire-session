"""
Custom keybindings handler for Wayfire Bridge
Manages dynamic custom keybindings from budgie-control-center
"""

from typing import Dict
import gi

gi.require_version('Gio', '2.0')
from gi.repository import Gio

from .budgie_wm_actions import BUDGIE_WM_ACTION_MAPPINGS
from .logging_config import get_logger
from .media_keys import MEDIA_KEY_MAPPINGS

log = get_logger(__name__)

# [command] names the bridge writes itself; custom keybindings must not reuse them
RESERVED_COMMAND_NAMES = {
    m['command_name']
    for m in (*MEDIA_KEY_MAPPINGS.values(), *BUDGIE_WM_ACTION_MAPPINGS.values())
} | {'budgie_menu'}


class CustomKeybindingsHandler:
    """Handles custom keybindings from gsettings"""

    def __init__(self, config_manager, transforms):
        self.config_manager = config_manager
        self.transforms = transforms
        self.schema = 'org.buddiesofbudgie.settings-daemon.plugins.media-keys'
        self.custom_schema = (
            'org.buddiesofbudgie.settings-daemon.plugins.media-keys.custom-keybinding'
        )
        self.settings = None

        # path -> {name, sanitized_name, command, binding}
        self.custom_keybindings: Dict[str, Dict] = {}
        # path -> Gio.Settings
        self.custom_keybinding_settings: Dict[str, Gio.Settings] = {}

    def setup(self):
        """Setup monitoring for custom keybindings"""
        try:
            source = Gio.SettingsSchemaSource.get_default()

            if not source.lookup(self.schema, True):
                log.warning("Custom keybindings schema %s not found", self.schema)
                return

            self.settings = Gio.Settings.new(self.schema)

            # Apply initial custom keybindings
            self._sync_custom_keybindings(self.settings)

            # Monitor changes to the custom-keybindings list
            self.settings.connect(
                'changed::custom-keybindings',
                lambda s, k: self._sync_custom_keybindings(s),
            )

            log.info("Custom keybindings monitoring enabled")

        except Exception:
            log.exception("Error setting up custom keybindings")

    def _sync_custom_keybindings(self, settings: Gio.Settings):
        """Sync all custom keybindings from gsettings"""
        try:
            paths = settings.get_value('custom-keybindings').unpack()
            current_paths = set(paths)
            previous_paths = set(self.custom_keybindings.keys())

            # Remove deleted keybindings
            for path in previous_paths - current_paths:
                self._remove_custom_keybinding(path)

            # Add or update keybindings, in list order so name clashes
            # resolve the same way every time
            for path in paths:
                if path in previous_paths:
                    self._update_custom_keybinding(path, save=False)
                else:
                    self._add_custom_keybinding(path)

            if previous_paths or current_paths:
                self.config_manager.save()

        except Exception:
            log.exception("Error syncing custom keybindings")

    def _config_name(self, name: str, path: str) -> str:
        """Pick the [command] suffix for a custom keybinding.

        Uses the sanitized name, falling back to name + path id when that
        clashes with a built-in binding or another custom keybinding.
        """
        sanitized = self.transforms.sanitize_name(name)
        taken = {
            kb['sanitized_name'] for p, kb in self.custom_keybindings.items()
            if p != path
        }
        if sanitized in RESERVED_COMMAND_NAMES or sanitized in taken:
            path_id = self.transforms.sanitize_name(path.rstrip('/').rsplit('/', 1)[-1])
            sanitized = f"{sanitized}_{path_id}"
        return sanitized

    def _add_custom_keybinding(self, path: str):
        """Add a new custom keybinding"""
        try:
            settings = Gio.Settings.new_with_path(self.custom_schema, path)

            # Track the path even while name/command are still empty:
            # control-center may add the path before filling in its fields
            self.custom_keybindings[path] = {
                'name': '',
                'sanitized_name': '',
                'command': '',
                'binding': '',
            }
            self.custom_keybinding_settings[path] = settings

            settings.connect('changed::name',    lambda s, k, p=path: self._update_custom_keybinding(p))
            settings.connect('changed::command', lambda s, k, p=path: self._update_custom_keybinding(p))
            settings.connect('changed::binding', lambda s, k, p=path: self._update_custom_keybinding(p))

            self._update_custom_keybinding(path, save=False)

        except Exception:
            log.exception("Error adding custom keybinding %s", path)

    def _update_custom_keybinding(self, path: str, save: bool = True):
        """Apply the current state of a tracked custom keybinding"""
        try:
            if path not in self.custom_keybinding_settings:
                return

            settings = self.custom_keybinding_settings[path]

            name = settings.get_string('name')
            command = settings.get_string('command')
            binding = settings.get_string('binding')

            old_sanitized = self.custom_keybindings[path]['sanitized_name']
            complete = bool(name and command)
            new_sanitized = self._config_name(name, path) if complete else ''

            self.custom_keybindings[path] = {
                'name': name,
                'sanitized_name': new_sanitized,
                'command': command,
                'binding': binding,
            }

            # If name changed, remove the old config entries
            if old_sanitized and old_sanitized != new_sanitized:
                self._remove_custom_keybinding_entries(old_sanitized)

            if complete:
                self._apply_custom_keybinding(path)
                log.info("Applied custom keybinding: %r -> %s", name, command)
            else:
                log.debug("Incomplete custom keybinding at %s (no name/command), waiting", path)

            if save:
                self.config_manager.save()

        except Exception:
            log.exception("Error updating custom keybinding %s", path)

    def _remove_custom_keybinding(self, path: str):
        """Remove a custom keybinding"""
        try:
            if path in self.custom_keybindings:
                sanitized_name = self.custom_keybindings[path]['sanitized_name']
                if sanitized_name:
                    self._remove_custom_keybinding_entries(sanitized_name)

                del self.custom_keybindings[path]
                self.custom_keybinding_settings.pop(path, None)

                log.info("Removed custom keybinding: %s", sanitized_name)

        except Exception:
            log.exception("Error removing custom keybinding %s", path)

    def _remove_custom_keybinding_entries(self, sanitized_name: str):
        """Remove config entries for a custom keybinding"""
        self.config_manager.remove_option('command', f'binding_{sanitized_name}')
        self.config_manager.remove_option('command', f'command_{sanitized_name}')

    def _apply_custom_keybinding(self, path: str):
        """Apply a custom keybinding to the config"""
        try:
            kb = self.custom_keybindings[path]
            sanitized_name = kb['sanitized_name']
            command = kb['command']
            binding = kb['binding']

            wayfire_binding = (
                self.transforms.convert_keybinding(binding) if binding else ''
            )

            if wayfire_binding:
                self.config_manager.set_value('command', f'binding_{sanitized_name}', wayfire_binding)
                self.config_manager.set_value('command', f'command_{sanitized_name}', command)
                log.debug(
                    "Applied custom keybinding: %s = %s -> %s",
                    sanitized_name, wayfire_binding, command,
                )
            else:
                # No valid binding – remove entries
                self._remove_custom_keybinding_entries(sanitized_name)
                log.debug("Removed binding for %s (no keybinding set)", sanitized_name)

        except Exception:
            log.exception("Error applying custom keybinding %s", path)
