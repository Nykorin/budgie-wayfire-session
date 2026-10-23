"""
Media keys handler for Wayfire Bridge
Handles static media key bindings from gsettings
"""

import gi

gi.require_version('Gio', '2.0')
from gi.repository import Gio

from .logging_config import get_logger

log = get_logger(__name__)


# Mapping of media key gsettings keys to Wayfire commands
# Format: gsetting_key: {command_name, command, fallback_command, plugin}
MEDIA_KEY_MAPPINGS = {
    'terminal': {
        'command_name': 'launch_terminal',
        'command': 'x-terminal-emulator',
        'fallback_command': 'xfce4-terminal',
        # User's chosen terminal takes precedence over 'command'
        'command_gsetting': ('org.gnome.desktop.default-applications.terminal', 'exec'),
        'plugin': None,
    },
    'www': {
        'command_name': 'launch_browser',
        'command': 'x-www-browser',
        'fallback_command': 'firefox',
        'plugin': None,
    },
    'email': {
        'command_name': 'launch_email',
        'command': 'xdg-email',
        'fallback_command': 'thunderbird',
        'plugin': None,
    },
    'home': {
        'command_name': 'launch_file_manager',
        'command': 'xdg-open ~',
        'fallback_command': 'nemo',
        'plugin': None,
    },
    'calculator': {
        'command_name': 'launch_calculator',
        'command': 'mate-calc',
        'fallback_command': 'gnome-calculator',
        'plugin': None,
    },
    'help': {
        'command_name': 'launch_help',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'search': {
        'command_name': 'launch_search',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'magnifier': {
        'command_name': 'toggle_magnifier',
        'command': 'wf-mag',
        'fallback_command': '',
        'plugin': 'mag',
    },
    'magnifier-zoom-in': {
        'command_name': 'magnifier_zoom_in',
        'command': 'wf-mag zoom-in',
        'fallback_command': '',
        'plugin': 'mag',
    },
    'magnifier-zoom-out': {
        'command_name': 'magnifier_zoom_out',
        'command': 'wf-mag zoom-out',
        'fallback_command': '',
        'plugin': 'mag',
    },
    'screenreader': {
        'command_name': 'toggle_screenreader',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'screensaver': {
        'command_name': 'lock_screen',
        'command': (
            'dbus-send --type=method_call '
            '--dest=org.buddiesofbudgie.BudgieScreenlock '
            '/org/buddiesofbudgie/Screenlock '
            'org.buddiesofbudgie.BudgieScreenlock.Lock'
        ),
        'fallback_command': '',
        'plugin': None,
    },
    'decrease-text-size': {
        'command_name': 'decrease_text_size',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'toggle-contrast': {
        'command_name': 'toggle_contrast',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'increase-text-size': {
        'command_name': 'increase_text_size',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'on-screen-keyboard': {
        'command_name': 'on_screen_keyboard',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'control-center': {
        'command_name': 'on_control_center',
        'command': 'budgie-desktop-settings',
        'fallback_command': '',
        'plugin': None,
    },
    'eject': {
        'command_name': 'on_eject',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'media': {
        'command_name': 'on_media',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'mic-mute': {
        'command_name': 'on_mic_mute',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'next': {
        'command_name': 'on_next',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'pause': {
        'command_name': 'on_pause',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'play': {
        'command_name': 'on_play',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'previous': {
        'command_name': 'on_previous',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'stop': {
        'command_name': 'on_stop',
        'command': '',
        'fallback_command': '',
        'plugin': None,
    },
    'volume-down': {
        'command_name': 'on_volume_down',
        'command': 'wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-',
        'fallback_command': '',
        'plugin': None,
    },
    'volume-mute': {
        'command_name': 'on_volume_mute',
        'command': 'wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle',
        'fallback_command': '',
        'plugin': None,
    },
    'volume-up': {
        'command_name': 'on_volume_up',
        'command': 'wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+',
        'fallback_command': '',
        'plugin': None,
    },
    'logout': {
        'command_name': 'on_logout',
        'command': 'budgie-session-quit',
        'fallback_command': '',
        'plugin': None,
    },
    'keyboard-brightness-down': {
        'command_name': 'on_keyboard_brightness_down',
        'command': 'budgie-brightness-helper --down',
        'fallback_command': '',
        'plugin': None,
    },
    'keyboard-brightness-up': {
        'command_name': 'on_keyboard_brightness_up',
        'command': 'budgie-brightness-helper --up',
        'fallback_command': '',
        'plugin': None,
    },
}


class MediaKeysHandler:
    """Handles static media key bindings"""

    def __init__(self, config_manager, transforms):
        self.config_manager = config_manager
        self.transforms = transforms
        self.schema = 'org.buddiesofbudgie.settings-daemon.plugins.media-keys'
        self.settings = None

    def setup(self):
        """Setup monitoring for media keys"""
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if not source.lookup(self.schema, True):
                log.warning("Media keys schema %s not found", self.schema)
                return

            self.settings = Gio.Settings.new(self.schema)

            for key, mapping in MEDIA_KEY_MAPPINGS.items():
                try:
                    self._apply_media_key(key, mapping)
                    self.settings.connect(
                        f'changed::{key}',
                        lambda s, k, m=mapping, gk=key: self._on_media_key_changed(gk, m),
                    )
                except Exception:
                    log.exception("Error setting up media key %s", key)

            log.info("Media keys monitoring enabled (%d keys)", len(MEDIA_KEY_MAPPINGS))

        except Exception:
            log.exception("Error setting up media keys")

    def _apply_media_key(self, gsettings_key: str, mapping: dict):
        """Apply a media key binding"""
        try:
            if not self.settings:
                return

            try:
                value = self.settings.get_value(gsettings_key).unpack()
            except Exception:
                log.debug("Could not read media key %s (key may not exist in schema)", gsettings_key)
                return

            log.debug("Media key %s: raw value = %r (%s)", gsettings_key, value, type(value).__name__)

            # Normalise to a list of non-empty binding strings
            keybindings = self._extract_keybindings(gsettings_key, value)

            if not keybindings:
                log.debug("%s: no binding set", gsettings_key)
                self._remove_media_key_binding(mapping['command_name'])
                return

            log.debug("%s: keybindings = %s", gsettings_key, keybindings)

            # Convert to Wayfire format
            wayfire_bindings = [
                wb for kb in keybindings
                if (wb := self.transforms.convert_keybinding(kb))
            ]

            if not wayfire_bindings:
                log.debug("%s: could not convert any keybindings to Wayfire format", gsettings_key)
                self._remove_media_key_binding(mapping['command_name'])
                return

            wayfire_binding = ' | '.join(wayfire_bindings)

            # Resolve command
            command = self._get_gsetting_command(mapping) or mapping['command']
            if not command or not command.strip():
                command = mapping.get('fallback_command', '')
            if not command or not command.strip():
                log.debug("%s: no command defined, skipping", gsettings_key)
                self._remove_media_key_binding(mapping['command_name'])
                return

            binding_option = f"binding_{mapping['command_name']}"
            command_option = f"command_{mapping['command_name']}"

            self.config_manager.set_value('command', binding_option, wayfire_binding)
            self.config_manager.set_value('command', command_option, command)

            if mapping.get('plugin'):
                log.debug(
                    "Applied media key: %s -> %s (requires %s plugin)",
                    gsettings_key, mapping['command_name'], mapping['plugin'],
                )
            else:
                log.debug(
                    "Applied media key: %s = %s -> %s",
                    gsettings_key, wayfire_binding, command,
                )

        except Exception:
            log.exception("Error applying media key %s", gsettings_key)

    def _get_gsetting_command(self, mapping: dict) -> str:
        """Read the command from the mapping's 'command_gsetting', if any."""
        if not mapping.get('command_gsetting'):
            return ''
        schema, key = mapping['command_gsetting']
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if not source.lookup(schema, True):
                return ''
            return Gio.Settings.new(schema).get_string(key).strip()
        except Exception:
            log.debug("Could not read %s::%s", schema, key, exc_info=True)
            return ''

    def _extract_keybindings(self, gsettings_key: str, value) -> list:
        """Normalise a raw gsettings value to a list of binding strings."""
        if isinstance(value, list):
            keybindings = [k for k in value if k and k not in ('', 'disabled')]

            if not keybindings:
                # Try the -static variant if it exists
                static_key = f"{gsettings_key}-static"
                schema_obj = self.settings.get_property('settings-schema')
                if schema_obj and schema_obj.has_key(static_key):
                    try:
                        static_value = self.settings.get_value(static_key).unpack()
                        if isinstance(static_value, list):
                            keybindings = [k for k in static_value if k and k not in ('', 'disabled')]
                            if keybindings:
                                log.debug("Using %s (static fallback): %s", static_key, keybindings)
                    except Exception:
                        log.debug("Could not read %s", static_key)

            return keybindings

        if isinstance(value, str) and value and value not in ('', 'disabled'):
            return [value]

        return []

    def _remove_media_key_binding(self, command_name: str):
        """Remove a media key binding from config"""
        self.config_manager.remove_option('command', f'binding_{command_name}')
        self.config_manager.remove_option('command', f'command_{command_name}')

    def _on_media_key_changed(self, key: str, mapping: dict):
        """Handle a media key change event"""
        log.debug("Media key changed: %s", key)
        self._apply_media_key(key, mapping)
        self.config_manager.save()
        self.config_manager.reload_wayfire()
