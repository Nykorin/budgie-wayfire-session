# Changelog

All notable changes to the wayfire bridge, its launcher and the shipped Wayfire config, made on top of upstream commit 41842ea. Dates are local time.

Contributors: user (design & direction), Claude (code)

Each bullet starts with the file it touches; paths are relative to the repository root.

## [2026-10-22]

### Added
- **src/wayfire_bridge/config_manager.py:** `remove_section` *(Claude)*
- **src/wayfire-bridge, src/systemd/wayfire-bridge.service:** Only one bridge runs at a time: a second one, from `[autostart]` and the systemd unit both, exits on a lock in `$XDG_RUNTIME_DIR/wayfire-bridge.lock` instead of fighting the first over `wayfire.ini`; the unit may write `%t` for it *(Claude)*

### Changed
- **README.md:** The bridge's installed path (`/usr/libexec/budgie-desktop/wayfire-bridge`), the clone folder's name, debugging with `pkill -f wayfire-bridge` and `wayfire-bridge --verbose`, and no `__init__.py` or GTK theme in the lists *(Claude)*
- **src/wayfire.ini:** The settings list says focus mode comes from `com.solus-project.budgie-wm` and the follow-focus plugin, not `[core] focus_mode` *(Claude)*
- **src/wayfire_bridge/bridge.py:** On startup, configs written by older versions lose the `[notifications]` section and `[core] gtk_theme`, and `[vswitch] vwidth`/`vheight` are removed, a `vheight` set there moving to `[core]` *(Claude)*
- **src/wayfire.ini:** The `[command]` and `[vswitch]` comments and the commented-out example bindings give Wayfire's binding format, modifiers first (`<ctrl> <alt> KEY_T`), instead of `KEY_T CTRL ALT` *(Claude, directed by user)*
- **src/wayfire_bridge/media_keys.py:** The terminal shortcut runs the default terminal from `org.gnome.desktop.default-applications.terminal exec` (falling back to `x-terminal-emulator`), so changing the shortcut no longer resets the command the default-terminal handler wrote *(Claude)*

### Removed
- **src/wayfire_bridge/transforms.py:** The unused `focus_mode` and `num_workspaces` transforms *(Claude)*
- **src/wayfire_bridge/mappings.py:** A second, identical `switch-to-workspace-last` entry *(Claude)*
- **src/wayfire_bridge/bridge.py:** A second placement-mode sync at startup, the same as the one just before it *(Claude)*
- **src/wayfire_bridge/bridge.py:** Writing Budgie's notification position to a `[notifications]` section, which isn't a Wayfire section *(Claude)*
- **src/wayfire_bridge/mappings.py, src/wayfire.ini:** `gtk-theme` to `[core] gtk_theme`, which isn't a Wayfire option *(Claude)*
- **src/wayfire.ini:** The `[command]` entries for close, maximize, minimize and moving a window to the left/right workspace: their bindings put the key before the modifiers (`KEY_Q ALT`) and their commands (`wm-actions close`, `vswitch-move left`) don't exist, so they did nothing. The bridge writes the real bindings to `[core]`, `[wm-actions]` and `[vswitch]` *(Claude, directed by user)*

### Fixed
- **src/wayfire_bridge/bridge.py:** The startup sync called `_on_double_click_changed`, which doesn't exist (the method is `_on_double_click_unsupported`); the error was hidden at debug level *(Claude)*
- **src/startbudgiewayfire.in:** If `budgie-session-binary` hadn't started within about 10 seconds, `pidwait` returned at once and Wayfire was killed, ending a slow first login. The launcher now waits for the session for as long as Wayfire is alive, and exits if Wayfire does *(Claude)*
- **src/startbudgiewayfire.in:** Without `pidwait` (procps older than 4) the session ended immediately; a polling loop takes its place. The config path is quoted *(Claude)*
- **src/wayfire_bridge/bridge.py:** The Budgie menu binding said expo's `<super>` toggle had to be removed to avoid a clash, but nothing removed it. When the overlay key's binding is also one of `[expo] toggle`'s alternatives, that alternative is dropped (`disabled` if none is left) *(Claude)*
- **src/wayfire_bridge/bridge.py:** The environment file is sourced by the launcher's shell, but its values were written unquoted, so a cursor theme with a space in its name broke it. Values the bridge writes are shell-quoted; lines added by hand are kept as written *(Claude)*
- **src/wayfire_bridge/bridge.py:** The warning after a keyboard layout change suggested `pkill wayfire && wayfire`, which ends the whole session; it now says XWayland and new apps pick the change up after logging out and back in *(Claude)*
- **src/wayfire_bridge/keybindings.py:** A custom shortcut whose path was listed before its name and command were filled in was skipped without watching it, so it only appeared after the bridge restarted. Every listed path is now tracked and applied once it is complete *(Claude)*
- **src/wayfire_bridge/keybindings.py:** Custom shortcuts were written as `binding_NAME`/`command_NAME`, so "Open Term" and "open-term" overwrote each other and one named "Launch Terminal" replaced the built-in terminal key. A clash with a built-in name (`RESERVED_COMMAND_NAMES`) or another custom shortcut now adds the entry's id (`open_term_custom2`); entries are applied in list order so clashes resolve the same way every time *(Claude)*
- **src/wayfire_bridge/bridge.py:** A cursor theme or size change only rewrote the environment file; `[input] cursor_theme`/`cursor_size` were set once at startup. They now follow the change *(Claude)*
- **src/wayfire_bridge/bridge.py:** A keyboard layout change from systemd-localed (locale1) only rewrote the environment file and reloaded nothing; `[input] xkb_layout`/`xkb_options` are now updated and saved too *(Claude)*
- **src/wayfire_bridge/mappings.py, src/wayfire.ini:** The workspace count was written to `[vswitch] vwidth`, but Wayfire reads the workspace grid (`vwidth`, `vheight`) from `[core]` *(Claude)*
- **src/wayfire-bridge:** Logging was never set up and `-v` was never read, so `-v`/`--verbose` and `WAYFIRE_BRIDGE_VERBOSE=1` did nothing; the entry point now parses its arguments and calls `setup_logging` *(Claude)*
- **src/systemd/wayfire-bridge.service:** `ExecStart` pointed at `/usr/bin/wayfire-bridge`, but meson installs it to `/usr/libexec/budgie-desktop/`; the `Documentation=` man page doesn't exist and is gone *(Claude)*
- **src/wayfire_bridge/bridge.py:** Several GSettings keys write the same Wayfire option (`switch-applications` and `switch-windows` both `[switcher] next_view`; `maximize`, `unmaximize` and `toggle-maximized` all `toggle_maximize`), and the last one applied won: an empty `switch-windows` blanked Alt+Tab, and `<Super>Up` was lost to `<Alt>F10`. Their bindings are now merged into one `|` list *(Claude)*
- **src/wayfire.ini:** The default `[vswitch]` workspace bindings were written key first (`KEY_LEFT CTRL LOGO`) and only worked once the bridge replaced them; they are `<super> <ctrl> KEY_LEFT` and so on *(Claude)*
- **src/wayfire_bridge/transforms.py:** Keypad navigation keysyms (`KP_Prior`, `KP_Next`, `KP_Home`, …, used by GNOME's default workspace shortcuts) became `KEY_KP_PRIOR` and the like, which don't exist; they map to the digit keys they share (`KEY_KP9`, `KEY_KP3`, …), and `KP_Equal` is added *(Claude)*
- **src/wayfire_bridge/transforms.py:** GNOME keysyms whose evdev names differ were turned into key names Wayfire rejects, so those shortcuts did nothing: `period` is `KEY_DOT`, `bracketleft`/`bracketright` `KEY_LEFTBRACE`/`KEY_RIGHTBRACE`, `Above_Tab` `KEY_GRAVE`, and `XF86Explorer`, `XF86Eject`, `XF86Tools`, `XF86LaunchA`/`B` get `KEY_FILE`, `KEY_EJECTCD`, `KEY_CONFIG`, `KEY_SCALE`, `KEY_DASHBOARD`. Keys that converted to a real but wrong name now match what keyboards send (`Print` `KEY_SYSRQ`, `XF86AudioPlay`/`Pause`/`Stop` `KEY_PLAYPAUSE`/`KEY_PAUSECD`/`KEY_STOPCD`, `XF86AudioForward` `KEY_FASTFORWARD`, `XF86Display` `KEY_SWITCHVIDEOMODE`), keyboard backlight keys are no longer screen brightness, and Caps/Num/Scroll Lock, Menu, `XF86AudioMicMute` and the keypad (`KP_1` is `KEY_KP1`) are added *(Claude)*
- **src/wayfire_bridge/bridge.py, src/wayfire_bridge/transforms.py:** Keyboard variants were dropped: `us+dvorak` was written as `xkb_layout = us`. The layout now comes from the same lookup as the environment file and is split into `xkb_layout` and `xkb_variant` (`us,de` and `dvorak,`) by the new `split_keyboard_layout` *(Claude)*
