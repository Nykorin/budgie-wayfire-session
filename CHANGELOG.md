# Changelog

All notable changes to the wayfire bridge, its launcher and the shipped Wayfire config, made on top of upstream commit 41842ea. Dates are local time.

Contributors: user (design & direction), Claude (code)

Each bullet starts with the file it touches; paths are relative to the repository root.

## [2026-10-22]

### Changed
- **src/wayfire_bridge/media_keys.py:** The terminal shortcut runs the default terminal from `org.gnome.desktop.default-applications.terminal exec` (falling back to `x-terminal-emulator`), so changing the shortcut no longer resets the command the default-terminal handler wrote *(Claude)*

### Fixed
- **src/wayfire_bridge/transforms.py:** GNOME keysyms whose evdev names differ were turned into key names Wayfire rejects, so those shortcuts did nothing: `period` is `KEY_DOT`, `bracketleft`/`bracketright` `KEY_LEFTBRACE`/`KEY_RIGHTBRACE`, `Above_Tab` `KEY_GRAVE`, and `XF86Explorer`, `XF86Eject`, `XF86Tools`, `XF86LaunchA`/`B` get `KEY_FILE`, `KEY_EJECTCD`, `KEY_CONFIG`, `KEY_SCALE`, `KEY_DASHBOARD`. Keys that converted to a real but wrong name now match what keyboards send (`Print` `KEY_SYSRQ`, `XF86AudioPlay`/`Pause`/`Stop` `KEY_PLAYPAUSE`/`KEY_PAUSECD`/`KEY_STOPCD`, `XF86AudioForward` `KEY_FASTFORWARD`, `XF86Display` `KEY_SWITCHVIDEOMODE`), keyboard backlight keys are no longer screen brightness, and Caps/Num/Scroll Lock, Menu, `XF86AudioMicMute` and the keypad (`KP_1` is `KEY_KP1`) are added *(Claude)*
- **src/wayfire_bridge/bridge.py, src/wayfire_bridge/transforms.py:** Keyboard variants were dropped: `us+dvorak` was written as `xkb_layout = us`. The layout now comes from the same lookup as the environment file and is split into `xkb_layout` and `xkb_variant` (`us,de` and `dvorak,`) by the new `split_keyboard_layout` *(Claude)*
