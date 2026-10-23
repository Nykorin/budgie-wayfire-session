"""
Core bridge logic for Wayfire Bridge - Full Feature Parity with labwc
Includes: environment file, peripherals, mutter settings, panel settings
"""

import os
import shlex
from pathlib import Path
from typing import Dict
import gi

gi.require_version('Gio', '2.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gio, GLib

try:
    import dbus
    import dbus.mainloop.glib
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False

from .config_manager import ConfigManager
from .keybindings import CustomKeybindingsHandler
from .media_keys import MediaKeysHandler, MEDIA_KEY_MAPPINGS
from .mappings import GSETTINGS_MAPPINGS
from .transforms import (
    TransformFunctions,
    parse_options_string,
    normalize_xkb_options,
    format_keyboard_layout,
    split_keyboard_layout,
)
from .budgie_wm_actions import BudgieWMActionsHandler
from .logging_config import get_logger

log = get_logger(__name__)


def read_key_value_file(filepath, strip_quotes=False):
    """Read a key=value config file into a dict."""
    config = {}
    if not os.path.exists(filepath):
        return config

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if strip_quotes:
                        value = value.strip('"').strip("'")
                    config[key] = value
    except Exception:
        log.debug("Could not read %s", filepath, exc_info=True)

    return config


def get_locale1_all_properties(dbus_bus):
    """Get all properties from org.freedesktop.locale1"""
    if not dbus_bus:
        return None

    try:
        proxy = dbus_bus.get_object(
            'org.freedesktop.locale1',
            '/org/freedesktop/locale1'
        )
        props_iface = dbus.Interface(
            proxy,
            'org.freedesktop.DBus.Properties'
        )
        return props_iface.GetAll('org.freedesktop.locale1')
    except Exception:
        log.debug("Could not read locale1 properties", exc_info=True)
        return None


class WayfireBridge:
    """Main bridge coordinator with full feature parity to labwc bridge"""

    def __init__(self):
        # Initialize dbus mainloop FIRST if available
        if DBUS_AVAILABLE:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.config_manager = ConfigManager()
        self.transforms = TransformFunctions()
        self.settings_objects: Dict[str, Gio.Settings] = {}
        self.dbus_system_bus = None

        # Delay config writes when doing bulk updates
        self.delay_config_write = False

        # Wayfire options fed by more than one gsettings key (e.g. Alt-Tab
        # from both switch-applications and switch-windows). Their bindings
        # are merged rather than letting the last key applied win.
        sources_by_target = {}
        for (schema, key), mapping in GSETTINGS_MAPPINGS.items():
            if mapping.get('transform') != 'keybinding':
                continue
            target = (mapping['section'], mapping['option'])
            sources_by_target.setdefault(target, []).append((schema, key))
        self.shared_targets = {
            target: sources for target, sources in sources_by_target.items()
            if len(sources) > 1
        }

        # Wayfire "key" options take one binding, not a "|" list
        self.single_binding_targets = {
            (mapping['section'], mapping['option'])
            for mapping in GSETTINGS_MAPPINGS.values()
            if mapping.get('single_binding')
        }

        # Initialise handlers
        self.keybindings_handler = CustomKeybindingsHandler(
            self.config_manager,
            self.transforms
        )
        self.media_keys_handler = MediaKeysHandler(
            self.config_manager,
            self.transforms
        )
        self.budgie_wm_handler = BudgieWMActionsHandler(
            self.config_manager,
            self.transforms
        )

        # Setup locale1 monitoring
        if DBUS_AVAILABLE:
            self.setup_locale1_monitor()

        # Setup all gsettings monitoring
        self.setup_gsettings()
        self.keybindings_handler.setup()
        self.media_keys_handler.setup()
        self.budgie_wm_handler.setup()

        # Setup peripheral monitoring with special handlers
        self.setup_peripheral_monitoring()

        # Setup mutter settings
        self.setup_mutter_settings()

        # Setup default terminal monitoring
        self.setup_default_terminal()

        # Write initial environment file
        self.write_environment_file()

        # Perform initial bridge config sync
        self.bridge_config()

    def setup_locale1_monitor(self):
        """Setup monitoring of org.freedesktop.locale1 using dbus-python"""
        try:
            bus = dbus.SystemBus()
            self.dbus_system_bus = bus

            bus.add_signal_receiver(
                self.on_locale1_properties_changed,
                signal_name='PropertiesChanged',
                dbus_interface='org.freedesktop.DBus.Properties',
                path='/org/freedesktop/locale1',
                arg0='org.freedesktop.locale1'
            )
            log.info("locale1 monitoring enabled")
        except Exception:
            log.warning("Could not setup locale1 monitoring", exc_info=True)

    def on_locale1_properties_changed(self, interface, changed, invalidated):
        """Handler for PropertiesChanged signals from locale1"""
        log.debug("locale1 PropertiesChanged received for interface: %s", interface)
        if changed:
            log.debug("Changed properties: %s", dict(changed))
        if invalidated:
            log.debug("Invalidated properties: %s", list(invalidated))

        # Update environment file
        self.write_environment_file()

        # locale1 is the fallback source for [input] xkb_layout/xkb_options
        schema = 'org.gnome.desktop.input-sources'
        if schema in self.settings_objects:
            for key in ('sources', 'xkb-options'):
                mapping = GSETTINGS_MAPPINGS.get((schema, key))
                if mapping:
                    self._apply_setting(
                        schema, key, mapping['section'], mapping['option'],
                        getattr(self.transforms, mapping['transform']),
                    )

        # Reload wayfire config if not delayed
        if not self.delay_config_write:
            self.config_manager.save()
            self.config_manager.reload_wayfire()

    def setup_peripheral_monitoring(self):
        """Setup special monitoring for peripheral settings that need custom handling"""
        # Touchpad scroll method requires monitoring two keys
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if source.lookup('org.gnome.desktop.peripherals.touchpad', True):
                touchpad_settings = Gio.Settings.new('org.gnome.desktop.peripherals.touchpad')
                touchpad_settings.connect(
                    'changed::two-finger-scrolling-enabled',
                    self._on_scroll_method_changed
                )
                touchpad_settings.connect(
                    'changed::edge-scrolling-enabled',
                    self._on_scroll_method_changed
                )
                touchpad_settings.connect(
                    'changed::left-handed',
                    self._on_touchpad_left_handed_changed
                )
                self.settings_objects['org.gnome.desktop.peripherals.touchpad'] = touchpad_settings
                log.debug("Touchpad monitoring enabled")
        except Exception:
            log.warning("Could not setup touchpad monitoring", exc_info=True)

        # Mouse settings
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if source.lookup('org.gnome.desktop.peripherals.mouse', True):
                mouse_settings = Gio.Settings.new('org.gnome.desktop.peripherals.mouse')
                mouse_settings.connect('changed::left-handed', self._on_mouse_left_handed_changed)
                mouse_settings.connect('changed::double-click', self._on_double_click_unsupported)
                self.settings_objects['org.gnome.desktop.peripherals.mouse'] = mouse_settings
                log.debug("Mouse monitoring enabled")
        except Exception:
            log.warning("Could not setup mouse monitoring", exc_info=True)

    def _on_double_click_unsupported(self, settings, key):
        """Wayfire has no double-click time setting in [input].
        Log a warning so it's clear why this gsetting has no effect.
        """
        value = settings.get_int('double-click')
        log.warning(
            "double-click time changed to %dms but Wayfire has no equivalent "
            "input option — this setting has no effect under Wayfire", value
        )

    def setup_mutter_settings(self):
        """Setup monitoring for mutter settings"""
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if source.lookup('org.gnome.mutter', True):
                mutter_settings = Gio.Settings.new('org.gnome.mutter')
                mutter_settings.connect('changed::center-new-windows', self._on_mutter_changed)
                mutter_settings.connect('changed::overlay-key', self._on_mutter_changed)
                self.settings_objects['org.gnome.mutter'] = mutter_settings

            # mutter.keybindings is handled via GSETTINGS_MAPPINGS in setup_gsettings()
            # but we need to confirm the schema exists and log appropriately
            if source.lookup('org.gnome.mutter.keybindings', True):
                log.info("org.gnome.mutter.keybindings schema found — tiling keybindings active")
            else:
                log.warning("org.gnome.mutter.keybindings schema not found — tiling keybindings unavailable")

            self._setup_budgie_wm_focus_monitor()

        except Exception:
            log.warning("Could not setup mutter settings monitoring", exc_info=True)

    def _setup_budgie_wm_focus_monitor(self):
        """Monitor com.solus-project.budgie-wm settings that need special handling."""
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if not source.lookup('com.solus-project.budgie-wm', True):
                log.warning("com.solus-project.budgie-wm schema not found")
                return

            budgie_wm = Gio.Settings.new('com.solus-project.budgie-wm')
            self.settings_objects['com.solus-project.budgie-wm'] = budgie_wm

            budgie_wm.connect(
                'changed::window-focus-mode',
                lambda s, k: self._on_budgie_wm_focus_changed(s)
            )
            budgie_wm.connect(
                'changed::edge-tiling',
                lambda s, k: self._on_edge_tiling_changed(s)
            )
            log.info("budgie-wm monitoring enabled (focus-mode, edge-tiling)")
        except Exception:
            log.warning("Could not setup budgie-wm monitor", exc_info=True)

    def _on_edge_tiling_changed(self, settings):
        """Handle edge-tiling from com.solus-project.budgie-wm.

        labwc maps this to <snapping><range> of 10 or 0.

        In Wayfire, aero-snap is controlled by TWO settings:
        [move] enable_snap   — master switch for edge snapping during drag
        [grid] mouse_snap    — whether dragging to edge triggers a grid slot

        Both must be toggled together to match labwc behaviour.
        The grid plugin must also be loaded for either to work.
        """
        enabled = settings.get_boolean('edge-tiling')
        value = 'true' if enabled else 'false'

        self.config_manager.set_value('move', 'enable_snap', value)
        self.config_manager.set_value('grid', 'mouse_snap', value)

        if enabled:
            self._ensure_plugin('grid')
            self._ensure_plugin('move')
            log.info("Edge tiling enabled (move.enable_snap + grid.mouse_snap = true)")
        else:
            log.info("Edge tiling disabled (move.enable_snap + grid.mouse_snap = false)")

        if not self.delay_config_write:
            self.config_manager.save()
            self.config_manager.reload_wayfire()

    def _on_budgie_wm_focus_changed(self, settings):
        """Handle window-focus-mode from com.solus-project.budgie-wm.

        Wayfire has no built-in focus_mode. Focus-follows-mouse is provided
        entirely by the follow-focus plugin from wayfire-plugins-extra.

        Mapping:
        click  -> remove follow-focus from plugins list entirely
        sloppy -> follow-focus loaded, raise_on_top = false
        mouse  -> follow-focus loaded, raise_on_top = true
        """
        mode = settings.get_string('window-focus-mode')
        log.info("Focus mode changed to: %s", mode)

        if mode == 'click':
            # Disable follow-focus entirely by removing it from plugins
            self._remove_plugin('follow-focus')
            # Clean up its section so there's no stale config
            self.config_manager.set_value('follow-focus', 'change_view', 'false')
        elif mode == 'sloppy':
            # Focus follows mouse but don't raise
            self._ensure_plugin('follow-focus')
            self.config_manager.set_value('follow-focus', 'change_view', 'true')
            self.config_manager.set_value('follow-focus', 'change_output', 'true')
            self.config_manager.set_value('follow-focus', 'raise_on_top', 'false')
        elif mode == 'mouse':
            # Focus follows mouse AND raise the window
            self._ensure_plugin('follow-focus')
            self.config_manager.set_value('follow-focus', 'change_view', 'true')
            self.config_manager.set_value('follow-focus', 'change_output', 'true')
            self.config_manager.set_value('follow-focus', 'raise_on_top', 'true')

        if not self.delay_config_write:
            self.config_manager.save()
            self.config_manager.reload_wayfire()
    def _ensure_plugin(self, plugin_name: str):
        self.config_manager.ensure_plugin(plugin_name)

    def _remove_plugin(self, plugin_name: str):
        self.config_manager.remove_plugin(plugin_name)

    def setup_default_terminal(self):
        """Setup monitoring for default terminal"""
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if source.lookup('org.gnome.desktop.default-applications.terminal', True):
                terminal_settings = Gio.Settings.new('org.gnome.desktop.default-applications.terminal')
                terminal_settings.connect('changed::exec', self._on_default_terminal_changed)
                self.settings_objects['org.gnome.desktop.default-applications.terminal'] = terminal_settings
                log.info("Default terminal monitoring enabled")
        except Exception:
            log.warning("Could not setup default terminal monitoring", exc_info=True)

    def _on_scroll_method_changed(self, settings, key):
        """Handle scroll method change (two keys control one setting)"""
        try:
            two_finger = settings.get_boolean("two-finger-scrolling-enabled")
            edge_scroll = settings.get_boolean("edge-scrolling-enabled")

            scroll_method = 'two-finger' if two_finger else ('edge' if edge_scroll else 'none')

            self.config_manager.set_value('input', 'scroll_method', scroll_method)
            log.debug("Scroll method changed to: %s", scroll_method)

            if not self.delay_config_write:
                self.config_manager.save()
                self.config_manager.reload_wayfire()
        except Exception:
            log.exception("Error handling scroll method change")

    def _on_touchpad_left_handed_changed(self, settings, key):
        """Handle touchpad left-handed change with 'mouse' mode support"""
        try:
            value = settings.get_string('left-handed')
            log.debug("Touchpad left-handed changed to: %s", value)

            if value == 'left':
                result = 'true'
            elif value == 'right':
                result = 'false'
            else:  # 'mouse' - follow mouse setting
                mouse_settings = self.settings_objects.get('org.gnome.desktop.peripherals.mouse')
                if mouse_settings:
                    mouse_left_handed = mouse_settings.get_boolean('left-handed')
                    result = 'true' if mouse_left_handed else 'false'
                    log.debug("Touchpad follows mouse left-handed: %s", result)
                else:
                    result = 'false'

            self.config_manager.set_value('input', 'touchpad_left_handed_mode', result)

            if not self.delay_config_write:
                self.config_manager.save()
                self.config_manager.reload_wayfire()
        except Exception:
            log.exception("Error handling touchpad left-handed change")

    def _on_mouse_left_handed_changed(self, settings, key):
        """When mouse left-handed changes, update touchpad if in 'mouse' mode"""
        try:
            touchpad_settings = self.settings_objects.get('org.gnome.desktop.peripherals.touchpad')
            if not touchpad_settings:
                return

            touchpad_mode = touchpad_settings.get_string('left-handed')
            if touchpad_mode != 'mouse':
                return  # Touchpad not following mouse

            mouse_left_handed = settings.get_boolean('left-handed')
            result = 'true' if mouse_left_handed else 'false'

            log.debug("Mouse left-handed changed, updating touchpad (mouse mode): %s", result)

            self.config_manager.set_value('input', 'touchpad_left_handed_mode', result)

            if not self.delay_config_write:
                self.config_manager.save()
                self.config_manager.reload_wayfire()
        except Exception:
            log.exception("Error handling mouse left-handed change for touchpad")

    def _on_mutter_changed(self, settings, key):
        """Handle mutter settings changes"""
        try:
            if key == 'center-new-windows':
                value = settings.get_boolean(key)
                mode = 'center' if value else 'cascade'
                self.config_manager.set_value('place', 'mode', mode)
                self._ensure_plugin('place')
                log.info("Placement mode set to: %s", mode)
                if not self.delay_config_write:
                    self.config_manager.save()
                    self.config_manager.reload_wayfire()
            elif key == 'overlay-key':
                self._apply_overlay_key(settings.get_string(key))

        except Exception:
            log.exception("Error handling mutter settings change")

    def _apply_overlay_key(self, key_name: str):
        """Map mutter overlay-key to a Budgie panel menu binding in [command].

        labwc fires the panel ActivateAction(2) dbus call on Super release.
        Wayfire has no on-release bindings, so we use <super> alone as the
        binding in [command], which fires on Super press.

        This requires removing expo's default <super> toggle to avoid conflict,
        since expo also claims <super> by default.
        """
        if not key_name:
            log.debug("overlay-key is empty, skipping")
            return

        # Convert the key name to Wayfire format.
        # mutter overlay-key is a plain string like "Super_L", not a GSettings
        # keybinding array, so convert_keybinding won't work directly.
        # In Wayfire, bare <super> is the correct binding for a lone Super press.
        if key_name in ('Super_L', 'Super_R', 'Super'):
            wayfire_binding = '<super>'
        else:
            # Fallback: attempt a normal conversion
            wayfire_binding = self.transforms.convert_keybinding(f'<Super>{key_name}')
            if not wayfire_binding:
                log.warning("Could not convert overlay-key %s to Wayfire format", key_name)
                return

        budgie_panel_command = (
            'dbus-send --type=method_call '
            '--dest=org.budgie_desktop.Panel '
            '/org/budgie_desktop/Panel '
            'org.budgie_desktop.Panel.ActivateAction int32:2'
        )

        # Write the [command] binding for the Budgie panel menu
        self.config_manager.set_value('command', 'binding_budgie_menu', wayfire_binding)
        self.config_manager.set_value('command', 'command_budgie_menu', budgie_panel_command)

        # Drop the same binding from expo's toggle so the two don't collide
        expo_toggle = self.config_manager.get_value('expo', 'toggle')
        if expo_toggle:
            alternatives = [a.strip() for a in expo_toggle.split('|')]
            if wayfire_binding in alternatives:
                remaining = [a for a in alternatives if a != wayfire_binding]
                self.config_manager.set_value(
                    'expo', 'toggle', ' | '.join(remaining) or 'disabled'
                )
                log.info("Removed %s from [expo] toggle (used by Budgie menu)", wayfire_binding)

        if not self.delay_config_write:
            self.config_manager.save()
            self.config_manager.reload_wayfire()

    def _on_default_terminal_changed(self, settings, key):
        """Handle default terminal change"""
        try:
            if key == 'exec':
                terminal = settings.get_string(key)
                log.debug("Default terminal changed to: %s", terminal)

                # The media keys handler owns the terminal binding and picks
                # an installed command (this setting first)
                self.media_keys_handler._apply_media_key(
                    'terminal', MEDIA_KEY_MAPPINGS['terminal']
                )

                if not self.delay_config_write:
                    self.config_manager.save()
                    self.config_manager.reload_wayfire()

        except Exception:
            log.exception("Error handling default terminal change")

    def setup_gsettings(self):
        """Setup gsettings monitoring for all mapped keys"""
        for (schema, key), mapping in GSETTINGS_MAPPINGS.items():
            try:
                section = mapping['section']
                option = mapping['option']
                transform_name = mapping.get('transform', 'str')

                # Get transform function
                transform = getattr(self.transforms, transform_name)

                # Check if schema exists
                source = Gio.SettingsSchemaSource.get_default()
                if not source.lookup(schema, True):
                    log.warning("Schema %s not found, skipping", schema)
                    continue

                # Create settings object if not already cached
                if schema not in self.settings_objects:
                    self.settings_objects[schema] = Gio.Settings.new(schema)

                settings = self.settings_objects[schema]

                # Apply initial value
                self._apply_setting(schema, key, section, option, transform)

                # Connect change signal
                settings.connect(
                    f'changed::{key}',
                    lambda s, k, sc=schema, se=section, o=option, t=transform:
                        self._on_setting_changed(sc, k, se, o, t)
                )

            except Exception:
                log.exception("Error setting up %s::%s", schema, key)

    def _apply_setting(self, schema: str, key: str, section: str,
                       option: str, transform):
        """Apply a gsettings value to the wayfire config"""
        try:
            settings = self.settings_objects[schema]
            value = settings.get_value(key).unpack()
            transformed_value = transform(value)

            # Keyboard layout: get_keyboard_layout() covers GSettings and the
            # fallbacks, and keeps variants, which Wayfire takes separately
            if option == 'xkb_layout':
                transformed_value, variant = split_keyboard_layout(self.get_keyboard_layout())
                self.config_manager.set_value(section, 'xkb_variant', variant)
                log.debug("xkb_layout=%r xkb_variant=%r", transformed_value, variant)

            # Several keybinding keys share this option: merge all of them
            elif (section, option) in self.shared_targets:
                transformed_value = self._merged_keybinding(section, option)

            if (section, option) in self.single_binding_targets:
                transformed_value = self._pick_single_binding(transformed_value)

            # Special handling for xkb_options - use fallback if empty
            elif option == 'xkb_options' and not transformed_value:
                # GSettings is empty, use the priority system
                transformed_value = self.get_merged_xkb_options()
                log.debug("GSettings xkb_options empty, using fallback: %s", transformed_value)

            # Special handling for touchpad_left_handed with 'mouse' mode
            elif option == 'touchpad_left_handed_mode' and transformed_value == 'mouse':
                mouse_settings = self.settings_objects.get('org.gnome.desktop.peripherals.mouse')
                if mouse_settings:
                    mouse_left_handed = mouse_settings.get_boolean('left-handed')
                    transformed_value = 'true' if mouse_left_handed else 'false'
                    log.debug("Touchpad follows mouse left-handed: %s", transformed_value)
                else:
                    transformed_value = 'false'

            log.debug(
                "Applying %s::%s  raw=%r (%s)  transformed=%r (%s)  target=[%s] %s",
                schema, key,
                value, type(value).__name__,
                transformed_value, type(transformed_value).__name__,
                section, option,
            )

            self.config_manager.set_value(section, option, str(transformed_value))

            log.debug(
                "Applied %s::%s -> [%s] %s = %s",
                schema, key, section, option, transformed_value,
            )

        except Exception:
            log.exception("Error applying %s::%s", schema, key)

    def _merged_keybinding(self, section: str, option: str) -> str:
        """Combine the bindings of every gsettings key that targets one option."""
        bindings = []
        for schema, key in self.shared_targets[(section, option)]:
            settings = self.settings_objects.get(schema)
            if settings is None:
                continue
            value = self.transforms.keybinding(settings.get_value(key).unpack())
            for binding in value.split(' | '):
                if binding and binding not in bindings:
                    bindings.append(binding)
        return ' | '.join(bindings)

    @staticmethod
    def _pick_single_binding(value: str) -> str:
        """Reduce a "|" list to one binding for options that only take one.

        Prefers an <alt> binding, matching Wayfire's own switcher defaults
        (Alt-Tab, Alt-Esc), and otherwise keeps the first one.
        """
        bindings = [b.strip() for b in value.split('|') if b.strip()]
        if not bindings:
            return ''
        chosen = next((b for b in bindings if '<alt>' in b), bindings[0])
        if len(bindings) > 1:
            log.info("Wayfire accepts one binding here, using %s of %s", chosen, bindings)
        return chosen

    def _on_setting_changed(self, schema: str, key: str, section: str,
                            option: str, transform):
        """Handle a gsettings change event"""
        log.debug("Setting changed: %s::%s", schema, key)

        # If input-sources changed, regenerate environment file AND update config
        if schema == 'org.gnome.desktop.input-sources':
            self.write_environment_file()
            # Also write directly to wayfire.ini
            self._apply_setting(schema, key, section, option, transform)

        # If cursor settings changed, regenerate environment file AND update config
        elif schema == 'org.gnome.desktop.interface' and key in ('cursor-theme', 'cursor-size'):
            self.write_environment_file()
            self._apply_setting(schema, key, section, option, transform)

        else:
            self._apply_setting(schema, key, section, option, transform)

        if not self.delay_config_write:
            self.config_manager.save()
            self.config_manager.reload_wayfire()

    def get_keyboard_layout(self):
        """Get keyboard layout from GSettings, locale1, or fallback"""
        # 1. GSettings input-sources
        if 'org.gnome.desktop.input-sources' in self.settings_objects:
            settings = self.settings_objects['org.gnome.desktop.input-sources']
            sources = settings.get_value('sources').unpack()

            layout_parts = []
            for source in sources:
                if len(source) >= 2 and source[0] == 'xkb':
                    extract = source[1].replace("'", "")
                    if '+' in extract:
                        rhs = extract.split('+')
                        extract = f"{rhs[0]}({rhs[1]})"
                    layout_parts.append(extract)

            if layout_parts:
                layout = ','.join(layout_parts)
                log.debug("Using keyboard layout from GSettings: %s", layout)
                return layout

        # 2. systemd-localed
        if self.dbus_system_bus:
            props = get_locale1_all_properties(self.dbus_system_bus)
            if props:
                layout = props.get('X11Layout', '')
                variant = props.get('X11Variant', '')
                formatted = format_keyboard_layout(str(layout), str(variant))
                if formatted:
                    log.debug("Using keyboard layout from locale1: %s", formatted)
                    return formatted

        # 3. /etc/default/keyboard
        keyboard_config = read_key_value_file('/etc/default/keyboard', strip_quotes=True)
        layout = keyboard_config.get('XKBLAYOUT', '')
        variant = keyboard_config.get('XKBVARIANT', '')
        formatted = format_keyboard_layout(layout, variant)
        if formatted:
            log.debug("Using keyboard layout from /etc/default/keyboard: %s", formatted)
            return formatted

        # 4. Default
        log.debug("Using default keyboard layout: us")
        return 'us'

    def get_merged_xkb_options(self):
        """Get XKB options with priority: user GSettings > locale1 > /etc/default/keyboard > default"""
        options_set = set()
        gsettings_default = set()

        # 1. GSettings (if user-modified)
        if 'org.gnome.desktop.input-sources' in self.settings_objects:
            settings = self.settings_objects['org.gnome.desktop.input-sources']
            try:
                user_value = settings.get_user_value('xkb-options')
                if user_value is not None:
                    gsettings_options = settings.get_strv('xkb-options')
                    options_set = set(gsettings_options)
                    log.debug("Using USER GSettings XKB options: %s", options_set)
                else:
                    gsettings_options = settings.get_strv('xkb-options')
                    if gsettings_options:
                        gsettings_default = set(gsettings_options)
                    log.debug("GSettings xkb-options not user-modified")
            except Exception:
                log.debug("Could not read GSettings xkb-options", exc_info=True)

        # 2. systemd-localed
        if not options_set and self.dbus_system_bus:
            props = get_locale1_all_properties(self.dbus_system_bus)
            if props and 'X11Options' in props:
                options_set = parse_options_string(str(props['X11Options']))
                if options_set:
                    log.debug("Got XKB options from locale1: %s", options_set)

        # 3. /etc/default/keyboard
        if not options_set:
            keyboard_config = read_key_value_file('/etc/default/keyboard', strip_quotes=True)
            options_set = parse_options_string(keyboard_config.get('XKBOPTIONS', ''))
            if options_set:
                log.debug("Got XKB options from /etc/default/keyboard: %s", options_set)

        # 4. GSettings default (if nothing else found)
        if not options_set and gsettings_default:
            options_set = gsettings_default
            log.debug("Using DEFAULT GSettings XKB options: %s", options_set)

        if not options_set:
            log.debug("No XKB options found from any source")
            options_set = set()

        # Normalize
        options_set = normalize_xkb_options(options_set)

        # Inject grp:alt_shift_toggle if multiple layouts and no grp: option
        current_layout = self.get_keyboard_layout()
        has_multiple_layouts = ',' in current_layout
        has_grp_option = any(opt.startswith('grp:') for opt in options_set)

        if has_multiple_layouts and not has_grp_option:
            options_set.add('grp:alt_shift_toggle')
            log.debug("Injected grp:alt_shift_toggle for multiple layouts")

        result = ','.join(sorted(options_set))
        log.debug("Final XKB options: %s", result)
        return result

    def get_locale_from_locale1(self):
        """Get locale settings from systemd-localed"""
        locale_vars = {}

        if not self.dbus_system_bus:
            return locale_vars

        props = get_locale1_all_properties(self.dbus_system_bus)
        if not props or 'Locale' not in props:
            return locale_vars

        for locale_entry in props['Locale']:
            if '=' in locale_entry:
                key, value = locale_entry.split('=', 1)
                locale_vars[key] = value
                log.debug("Got from locale1: %s=%s", key, value)

        return locale_vars

    def write_environment_file(self):
        """Write environment file with keyboard, cursor, and locale settings"""
        env_file = self.config_manager.config_path.parent / 'environment'

        fully_managed_vars = {
            'XKB_DEFAULT_LAYOUT', 'XKB_DEFAULT_OPTIONS',
            'XCURSOR_THEME', 'XCURSOR_SIZE',
            'LANG', 'LC_CTYPE', 'LC_NUMERIC', 'LC_TIME', 'LC_COLLATE',
            'LC_MONETARY', 'LC_MESSAGES', 'LC_PAPER', 'LC_NAME',
            'LC_ADDRESS', 'LC_TELEPHONE', 'LC_MEASUREMENT', 'LC_IDENTIFICATION'
        }

        existing_vars = read_key_value_file(str(env_file))
        new_vars = {}

        # Keyboard layout and options
        new_vars['XKB_DEFAULT_LAYOUT'] = self.get_keyboard_layout()
        new_vars['XKB_DEFAULT_OPTIONS'] = self.get_merged_xkb_options()

        # Cursor settings
        if 'org.gnome.desktop.interface' in self.settings_objects:
            settings = self.settings_objects['org.gnome.desktop.interface']
            cursor_theme = settings.get_string('cursor-theme')
            if cursor_theme:
                new_vars['XCURSOR_THEME'] = cursor_theme
            cursor_size = settings.get_int('cursor-size')
            if cursor_size:
                new_vars['XCURSOR_SIZE'] = str(cursor_size)

        # Locale settings
        locale_from_locale1 = self.get_locale_from_locale1()
        if locale_from_locale1:
            log.debug("Got %d locale variables from locale1", len(locale_from_locale1))
            new_vars.update(locale_from_locale1)
        else:
            # Fallback to environment
            log.debug("No locale from locale1, using environment fallback")
            for var in fully_managed_vars:
                if var.startswith('LANG') or var.startswith('LC_'):
                    value = os.environ.get(var)
                    if value:
                        new_vars[var] = value
            if 'LANG' not in new_vars:
                new_vars['LANG'] = 'en_US.UTF-8'

        # Check if keyboard layout or XKB options changed
        keyboard_changed = False
        if 'XKB_DEFAULT_LAYOUT' in existing_vars:
            if existing_vars['XKB_DEFAULT_LAYOUT'] != shlex.quote(new_vars['XKB_DEFAULT_LAYOUT']):
                keyboard_changed = True
                log.info("Keyboard layout changed: %s -> %s",
                        existing_vars['XKB_DEFAULT_LAYOUT'],
                        new_vars['XKB_DEFAULT_LAYOUT'])
        if 'XKB_DEFAULT_OPTIONS' in existing_vars:
            if existing_vars['XKB_DEFAULT_OPTIONS'] != shlex.quote(new_vars['XKB_DEFAULT_OPTIONS']):
                keyboard_changed = True
                log.info("XKB options changed: %s -> %s",
                        existing_vars['XKB_DEFAULT_OPTIONS'],
                        new_vars['XKB_DEFAULT_OPTIONS'])

        # Merge: keep user vars, update managed ones
        final_vars = {}
        for key, value in existing_vars.items():
            if key not in fully_managed_vars:
                final_vars[key] = value
        final_vars.update(new_vars)

        # Write file
        env_file.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Budgie Desktop - Wayfire environment configuration\n",
            "# Variables fully managed by budgie: XKB_DEFAULT_*, XCURSOR_*, LC_*, LANG\n",
            "# Other user customizations are preserved\n\n",
        ]

        xkb_vars = {k: v for k, v in final_vars.items() if k.startswith('XKB_')}
        cursor_vars = {k: v for k, v in final_vars.items() if k.startswith('XCURSOR_')}
        locale_vars = {k: v for k, v in final_vars.items() if k.startswith('LC_') or k == 'LANG'}
        other_vars = {k: v for k, v in final_vars.items()
                      if not k.startswith(('XKB_', 'XCURSOR_', 'LC_')) and k != 'LANG'}

        for vars_dict in [xkb_vars, cursor_vars, locale_vars]:
            if vars_dict:
                for key in sorted(vars_dict.keys()):
                    value = vars_dict[key]
                    # The file is sourced by a shell: quote values we
                    # generate (e.g. cursor themes with spaces), keep user
                    # lines exactly as written
                    if key in new_vars:
                        value = shlex.quote(value)
                    lines.append(f"{key}={value}\n")
                lines.append("\n")

        if other_vars:
            lines.append("# User customizations\n")
            for key in sorted(other_vars.keys()):
                lines.append(f"{key}={other_vars[key]}\n")

        with open(env_file, "w") as f:
            f.writelines(lines)

        log.info("Updated environment file: %s", env_file)

        # Warn if keyboard settings changed
        if keyboard_changed:
            log.warning(
                "Keyboard layout or options changed. "
                "XWayland and newly started apps pick this up after logging "
                "out and back in"
            )

    def bridge_config(self):
        """Perform initial sync of all settings to wayfire config"""
        log.info("Performing initial bridge config sync")

        # Ensure all required plugins are in [core] plugins list
        self.config_manager.ensure_wm_plugins()

        # Drop entries written by older bridge versions that Wayfire ignores
        self.config_manager.remove_section('notifications')
        self.config_manager.remove_option('core', 'gtk_theme')
        # The workspace grid lives in [core], not [vswitch]; carry vheight over
        vheight = self.config_manager.get_value('vswitch', 'vheight')
        if vheight is not None and not self.config_manager.has_option('core', 'vheight'):
            self.config_manager.set_value('core', 'vheight', vheight)
        self.config_manager.remove_option('vswitch', 'vwidth')
        self.config_manager.remove_option('vswitch', 'vheight')
        # Old vswitch names: binding_win_* doesn't exist and binding_0 was an
        # off-by-one (workspaces are numbered from 1)
        if 'vswitch' in self.config_manager.config:
            for option in list(self.config_manager.config['vswitch']):
                if option.startswith('binding_win_') or option == 'binding_0':
                    self.config_manager.remove_option('vswitch', option)

        # Log layout switching status so it's visible in journal
        layout = self.get_keyboard_layout()
        if ',' in layout:
            options = self.get_merged_xkb_options()
            grp = next((o for o in options.split(',') if o.startswith('grp:')), None)
            log.info(
                "Multiple keyboard layouts detected (%s). "
                "Layout switching via xkb_options: %s. "
                "Note: switch-input-source gsetting keybinding has no Wayfire equivalent — "
                "switching is handled by the grp: xkb option.",
                layout,
                grp or 'none set — grp:alt_shift_toggle will be injected'
            )

        self.delay_config_write = True

        try:
            # Sync all peripheral settings
            if 'org.gnome.desktop.peripherals.touchpad' in self.settings_objects:
                touchpad = self.settings_objects['org.gnome.desktop.peripherals.touchpad']
                touchpad_keys = [
                    'natural-scroll', 'left-handed', 'speed',
                    'tap-to-click', 'disable-while-typing',
                    'click-method', 'send-events',
                    'tap-and-drag',
                    'tap-and-drag-lock',
                    'middle-click-emulation',
                    'tap-button-map',
                    'accel-profile'
                ]
                for key in touchpad_keys:
                    try:
                        # Find the mapping for this key
                        full_key = ('org.gnome.desktop.peripherals.touchpad', key)
                        if full_key in GSETTINGS_MAPPINGS:
                            mapping = GSETTINGS_MAPPINGS[full_key]
                            transform = getattr(self.transforms, mapping.get('transform', 'str'))
                            self._apply_setting(
                                'org.gnome.desktop.peripherals.touchpad',
                                key,
                                mapping['section'],
                                mapping['option'],
                                transform
                            )
                    except Exception:
                        log.debug("Could not sync touchpad key %s", key, exc_info=True)

                # Special handling for scroll method
                try:
                    self._on_scroll_method_changed(touchpad, 'two-finger-scrolling-enabled')
                except Exception:
                    log.debug("Could not sync scroll method", exc_info=True)

            # Sync all mouse settings
            if 'org.gnome.desktop.peripherals.mouse' in self.settings_objects:
                mouse = self.settings_objects['org.gnome.desktop.peripherals.mouse']
                mouse_keys = ['natural-scroll', 'left-handed', 'speed', 'accel-profile','middle-click-emulation']
                for key in mouse_keys:
                    try:
                        full_key = ('org.gnome.desktop.peripherals.mouse', key)
                        if full_key in GSETTINGS_MAPPINGS:
                            mapping = GSETTINGS_MAPPINGS[full_key]
                            transform = getattr(self.transforms, mapping.get('transform', 'str'))
                            self._apply_setting(
                                'org.gnome.desktop.peripherals.mouse',
                                key,
                                mapping['section'],
                                mapping['option'],
                                transform
                            )
                    except Exception:
                        log.debug("Could not sync mouse key %s", key, exc_info=True)

            # Sync mutter settings
            if 'org.gnome.mutter' in self.settings_objects:
                mutter = self.settings_objects['org.gnome.mutter']
                for key in ['center-new-windows', 'overlay-key']:
                    try:
                        self._on_mutter_changed(mutter, key)
                    except Exception:
                        log.debug("Could not sync mutter key %s", key, exc_info=True)

            # Sync default terminal
            if 'org.gnome.desktop.default-applications.terminal' in self.settings_objects:
                terminal = self.settings_objects['org.gnome.desktop.default-applications.terminal']
                try:
                    self._on_default_terminal_changed(terminal, 'exec')
                except Exception:
                    log.debug("Could not sync default terminal", exc_info=True)

            # Sync focus mode from budgie-wm
            if 'com.solus-project.budgie-wm' in self.settings_objects:
                budgie_wm = self.settings_objects['com.solus-project.budgie-wm']
                try:
                    self._on_budgie_wm_focus_changed(budgie_wm)
                except Exception:
                    log.debug("Could not sync budgie-wm focus mode", exc_info=True)
                try:
                    self._on_edge_tiling_changed(budgie_wm)
                except Exception:
                    log.debug("Could not sync edge-tiling", exc_info=True)

        finally:
            self.delay_config_write = False
            self.config_manager.save()
            log.info("Initial bridge config sync complete")

    def run(self):
        """Run the bridge (blocking)"""
        log.info(
            "Wayfire Bridge started – config=%s  monitoring %d gsettings keys",
            self.config_manager.config_path,
            len(GSETTINGS_MAPPINGS),
        )

        # Run main loop
        try:
            loop = GLib.MainLoop()
            loop.run()
        except KeyboardInterrupt:
            log.info("Keyboard interrupt received – shutting down Wayfire Bridge")
