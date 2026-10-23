"""
Transform functions for converting gsettings values to Wayfire format
"""

from typing import Any


class TransformFunctions:
    """Collection of transform functions for gsettings to Wayfire conversion"""

    @staticmethod
    def str(value: Any) -> str:
        """Pass through as string"""
        return str(value)

    @staticmethod
    def int(value: Any) -> int:
        """Convert to integer"""
        return int(value)

    @staticmethod
    def float(value: Any) -> float:
        """Convert to float"""
        return float(value)

    @staticmethod
    def bool(value: bool) -> str:
        """Transform boolean to wayfire format (true/false)"""
        return 'true' if value else 'false'

    @staticmethod
    def button_layout(value: str) -> str:
        """Transform GNOME button layout to Wayfire format

        GNOME: 'left,buttons:right,buttons', e.g. 'appmenu:minimize,maximize,close'
        Wayfire: space-separated, e.g. 'minimize maximize close'

        Wayfire's decorations only have minimize, maximize and close, so other
        entries (appmenu, spacer, icon, menu) are dropped and the order kept.
        """
        supported = ('minimize', 'maximize', 'close')
        buttons = []
        for name in value.replace(':', ',').split(','):
            name = name.strip()
            if name in supported and name not in buttons:
                buttons.append(name)
        return ' '.join(buttons)

    @staticmethod
    def scroll_method(value: bool) -> str:
        """Transform two-finger scrolling to scroll method"""
        return 'two-finger' if value else 'edge'

    @staticmethod
    def titlebar_font(value: str) -> str:
        """Transform GNOME titlebar-font Pango string to Wayfire decoration font.

        labwc decomposes the Pango string into separate family/weight/slant/size
        XML attributes. Wayfire's [decoration] font option takes the Pango string
        directly, so this is a near pass-through.

        GSettings value:  'Cantarell Bold 11'
        Wayfire value:    'Cantarell Bold 11'

        Empty string means use system default — fall back to sans-serif.
        """
        if not value or not value.strip():
            return 'sans-serif'
        return value.strip()

    @staticmethod
    def touchpad_left_handed(value: str) -> str:
        """Transform touchpad left-handed mode

        GNOME uses: 'left', 'right', 'mouse' (follow mouse setting)
        Wayfire uses: true/false

        Note: When value is 'mouse', caller must check mouse left-handed setting
        """
        if value == 'left':
            return 'true'
        elif value == 'right':
            return 'false'
        # 'mouse' - caller needs to handle this specially
        return 'mouse'

    @staticmethod
    def send_events(value: str) -> str:
        """Transform touchpad send-events to [input] disable_touchpad_while_mouse

        GNOME: enabled, disabled, disabled-on-external-mouse
        Wayfire only has the "disabled while a mouse is connected" switch; it
        has no option to turn the touchpad off entirely, so 'disabled' maps
        to false like 'enabled'.
        """
        return 'true' if value == 'disabled-on-external-mouse' else 'false'

    @staticmethod
    def accel_profile(value: str) -> str:
        """Transform a pointer accel-profile to Wayfire

        GNOME: default, flat, adaptive, custom
        Wayfire: default, none, adaptive, flat (no custom curves, so 'custom'
        falls back to libinput's default)
        """
        return value if value in ('default', 'flat', 'adaptive') else 'default'

    @staticmethod
    def click_method(value: str) -> str:
        """Transform touchpad click-method to Wayfire names

        GNOME: default, none, areas, fingers
        Wayfire: default, none, button-areas, clickfinger
        """
        return {
            'areas': 'button-areas',
            'fingers': 'clickfinger',
            'none': 'none',
        }.get(value, 'default')

    @staticmethod
    def keybinding(value: Any) -> str:
        """Transform GNOME keybinding format to Wayfire format"""
        if isinstance(value, list) and len(value) > 0:
            # GNOME can have multiple keybindings in array
            # Convert each and join with pipe separator
            converted = []
            for binding in value:
                wayfire_binding = TransformFunctions.convert_keybinding(binding)
                if wayfire_binding:
                    converted.append(wayfire_binding)
            return ' | '.join(converted) if converted else ''
        return ''

    @staticmethod
    def convert_keybinding(gnome_binding: str) -> str:
        """Convert GNOME keybinding to Wayfire format

        Wayfire format: <modifier1> <modifier2> KEY_X
        - Modifiers FIRST, lowercase, in angle brackets
        - Key LAST, uppercase with KEY_ prefix
        """
        if not gnome_binding or gnome_binding == 'disabled':
            return ''

        modifiers = []
        key = gnome_binding

        # Extract modifiers in order - will be lowercase in angle brackets
        if '<Super>' in key or '<Mod4>' in key:
            modifiers.append('<super>')
        if '<Primary>' in key or '<Control>' in key or '<Ctrl>' in key:
            modifiers.append('<ctrl>')
        if '<Alt>' in key:
            modifiers.append('<alt>')
        if '<Shift>' in key:
            modifiers.append('<shift>')

        # Remove modifiers to get key
        for mod in ['<Super>', '<Mod4>', '<Primary>', '<Control>', '<Ctrl>', '<Alt>', '<Shift>']:
            key = key.replace(mod, '')
        key = key.strip('<>')

        if key:
            # Handle special key names and XF86 hardware keys. Values must be
            # the canonical evdev name: Wayfire resolves them with libevdev,
            # which rejects kernel aliases (KEY_SCREENLOCK, KEY_DASHBOARD)
            key_map = {
                # Standard keys
                'Return': 'ENTER',
                'BackSpace': 'BACKSPACE',
                'Escape': 'ESC',
                'space': 'SPACE',
                'Space': 'SPACE',
                'Tab': 'TAB',
                'Page_Up': 'PAGEUP',
                'Page_Down': 'PAGEDOWN',
                'Prior': 'PAGEUP',
                'Next': 'PAGEDOWN',
                'Print': 'SYSRQ',
                'Caps_Lock': 'CAPSLOCK',
                'Num_Lock': 'NUMLOCK',
                'Scroll_Lock': 'SCROLLLOCK',
                'Menu': 'COMPOSE',
                'Shift_L': 'LEFTSHIFT',
                'Shift_R': 'RIGHTSHIFT',
                'Control_L': 'LEFTCTRL',
                'Control_R': 'RIGHTCTRL',
                'Alt_L': 'LEFTALT',
                'Alt_R': 'RIGHTALT',
                'Super_L': 'LEFTMETA',
                'Super_R': 'RIGHTMETA',

                # Punctuation keysyms whose evdev names differ
                'period': 'DOT',
                'bracketleft': 'LEFTBRACE',
                'bracketright': 'RIGHTBRACE',
                'Above_Tab': 'GRAVE',

                # Keypad
                'KP_Enter': 'KPENTER',
                'KP_Add': 'KPPLUS',
                'KP_Subtract': 'KPMINUS',
                'KP_Multiply': 'KPASTERISK',
                'KP_Divide': 'KPSLASH',
                'KP_Decimal': 'KPDOT',
                'KP_Equal': 'KPEQUAL',
                # Keypad navigation keysyms share the digit keys
                'KP_Insert': 'KP0',
                'KP_End': 'KP1',
                'KP_Down': 'KP2',
                'KP_Next': 'KP3',
                'KP_Page_Down': 'KP3',
                'KP_Left': 'KP4',
                'KP_Begin': 'KP5',
                'KP_Right': 'KP6',
                'KP_Home': 'KP7',
                'KP_Up': 'KP8',
                'KP_Prior': 'KP9',
                'KP_Page_Up': 'KP9',
                'KP_Delete': 'KPDOT',

                # XF86 Hardware keys -> KEY_ equivalents
                'XF86AudioLowerVolume': 'VOLUMEDOWN',
                'XF86AudioRaiseVolume': 'VOLUMEUP',
                'XF86AudioMute': 'MUTE',
                'XF86AudioMicMute': 'MICMUTE',
                'XF86AudioPlay': 'PLAYPAUSE',
                'XF86AudioPause': 'PAUSECD',
                'XF86AudioStop': 'STOPCD',
                'XF86AudioNext': 'NEXTSONG',
                'XF86AudioPrev': 'PREVIOUSSONG',
                'XF86AudioRewind': 'REWIND',
                'XF86AudioForward': 'FASTFORWARD',
                'XF86AudioMedia': 'MEDIA',
                'XF86AudioRecord': 'RECORD',
                'XF86MonBrightnessUp': 'BRIGHTNESSUP',
                'XF86MonBrightnessDown': 'BRIGHTNESSDOWN',
                'XF86KbdBrightnessUp': 'KBDILLUMUP',
                'XF86KbdBrightnessDown': 'KBDILLUMDOWN',
                'XF86Display': 'SWITCHVIDEOMODE',
                'XF86WLAN': 'WLAN',
                'XF86Tools': 'CONFIG',
                'XF86Search': 'SEARCH',
                'XF86LaunchA': 'SCALE',
                'XF86LaunchB': 'ALL_APPLICATIONS',
                'XF86Explorer': 'FILE',
                'XF86Calculator': 'CALC',
                'XF86Mail': 'MAIL',
                'XF86WWW': 'WWW',
                'XF86HomePage': 'HOMEPAGE',
                'XF86Favorites': 'FAVORITES',
                'XF86Back': 'BACK',
                'XF86Forward': 'FORWARD',
                'XF86Eject': 'EJECTCD',
                'XF86Sleep': 'SLEEP',
                'XF86PowerOff': 'POWER',
                'XF86Battery': 'BATTERY',
                'XF86Bluetooth': 'BLUETOOTH',
                'XF86ScreenSaver': 'COFFEE',
                'XF86Suspend': 'SUSPEND',
                'XF86RFKill': 'RFKILL',
                'XF86UWB': 'UWB',
                'XF86KbdLightOnOff': 'KBDILLUMTOGGLE',
                'XF86Keyboard': 'KEYBOARD',
                'XF86MonBrightnessCycle': 'BRIGHTNESS_CYCLE',
                'XF86RotateWindows': 'ROTATE_DISPLAY',
                'XF86RotationLockToggle': 'ROTATE_LOCK_TOGGLE',
                'XF86AudioRandomPlay': 'SHUFFLE',
                'XF86TouchpadToggle': 'F21',
                'XF86TouchpadOn': 'F22',
                'XF86TouchpadOff': 'F23',
            }
            if key not in key_map and key.startswith('XF86'):
                # An XF86 keysym we can't place on an evdev key (some, like
                # XF86Hibernate, have none): skip it rather than bind a
                # KEY_ name Wayfire would reject
                return ''
            key = key_map.get(key, key)
            # Keypad digits: KP_1 -> KP1
            if len(key) == 4 and key.startswith('KP_') and key[3].isdigit():
                key = 'KP' + key[3]

            # Build the keybinding: <modifier1> <modifier2> KEY_X
            key_part = f"KEY_{key.upper()}"

            # Modifiers FIRST (lowercase in angle brackets), key LAST
            if modifiers:
                # Join modifiers with space, then add key at the end
                return ' '.join(modifiers) + ' ' + key_part
            else:
                return key_part
        return ''

    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize custom keybinding name for use in config"""
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        sanitized = sanitized.lower().strip('_')
        return sanitized or 'custom'

    @staticmethod
    def kb_repeat_rate(value: int) -> int:
        """Transform keyboard repeat interval (ms) to repeat rate (chars/sec)"""
        # GNOME uses repeat-interval in milliseconds between repeats
        # Wayfire uses kb_repeat_rate as characters per second
        # Rate = 1000 / interval
        if value > 0:
            return max(1, int(1000 / value))
        return 30  # Default fallback

    @staticmethod
    def placement_mode(value: bool) -> str:
        """Transform mutter center-new-windows boolean to Wayfire place mode.

        Wayfire [place] modes: center, cascade, random
        - center-new-windows = true  -> center
        - center-new-windows = false -> cascade  (matches labwc 'automatic')
        """
        return 'center' if value else 'cascade'


def parse_options_string(options_string):
    """Parse comma-separated options into a set."""
    if not options_string:
        return set()
    return {opt.strip() for opt in options_string.split(',') if opt.strip()}


def normalize_xkb_options(options_set):
    """
    Normalize XKB options to avoid conflicts.
    Only certain option families are mutually exclusive.
    Other families like lv3:, compose: can have multiple options.

    Known mutually-exclusive families: grp, caps, ctrl, altwin

    Args:
        options_set: Set of XKB option strings

    Returns:
        Set of normalized options
    """
    if not options_set:
        return set()

    # Families where only one option should be kept
    exclusive_families = {'grp', 'caps', 'ctrl', 'altwin'}

    seen_exclusive = {}
    normalized = set()

    for option in sorted(options_set):  # Sort for consistent behavior
        if ':' in option:
            family = option.split(':', 1)[0]

            if family in exclusive_families:
                # Keep only first of exclusive families
                if family not in seen_exclusive:
                    seen_exclusive[family] = option
                    normalized.add(option)
                # else: skip duplicate exclusive family
            else:
                # Non-exclusive family - keep all
                normalized.add(option)
        else:
            # Options without family (rare) - keep all
            normalized.add(option)

    return normalized


def split_keyboard_layout(formatted):
    """
    Inverse of format_keyboard_layout: split 'us(dvorak),de' into
    ('us,de', 'dvorak,') for Wayfire's separate xkb_layout/xkb_variant options.
    """
    layouts = []
    variants = []
    for part in (formatted or '').split(','):
        part = part.strip()
        if not part:
            continue
        if '(' in part and part.endswith(')'):
            layout, variant = part[:-1].split('(', 1)
        else:
            layout, variant = part, ''
        layouts.append(layout)
        variants.append(variant)

    if not any(variants):
        return ','.join(layouts), ''
    return ','.join(layouts), ','.join(variants)


def format_keyboard_layout(layout, variant=''):
    """
    Convert layout and variant strings to labwc/wayfire format.

    Args:
        layout: Comma-separated layout string
        variant: Comma-separated variant string

    Returns:
        Formatted layout string or None if no layout
    """
    if not layout:
        return None

    if not variant:
        return layout

    variants = variant.split(',')
    layouts = layout.split(',')

    combined = []
    for i, l in enumerate(layouts):
        if i < len(variants) and variants[i]:
            combined.append(f"{l}({variants[i]})")
        else:
            combined.append(l)

    return ','.join(combined)
