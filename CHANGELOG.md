# Changelog

All notable changes to the wayfire bridge, its launcher and the shipped Wayfire config, made on top of upstream commit 41842ea. Dates are local time.

Contributors: user (design & direction), Claude (code)

Each bullet starts with the file it touches; paths are relative to the repository root.

## [2026-10-23]

### Added
- **src/wayfire_bridge/transforms.py:** Key names for the modifier keys (`Shift_L`, `Super_R`, …) and more hardware keys Budgie's defaults use: screensaver (`KEY_COFFEE`), suspend, rfkill, UWB, keyboard backlight toggle, keyboard layout, brightness cycle, rotate display and rotation lock, shuffle, and the touchpad toggles (`KEY_F21`–`F23`, where xkb places them) *(Claude)*
- **src/wayfire_bridge/bridge.py:** Options shared by mouse and touchpad in Wayfire (`left_handed_mode`, `middle_emulation`) are on if either device's setting asks for it (`_merged_flag`); a touchpad set to follow the mouse uses the mouse's value *(Claude)*

### Changed
- **src/wayfire_bridge/bridge.py:** On startup, options older versions wrote that Wayfire doesn't have (`tap_button_map`, `touchpad_natural_scroll`, `touchpad_left_handed_mode`, `disable_while_typing`, `touchpad_send_events`, `xkb_repeat_delay`/`rate`, `[grid] mouse_snap`) are removed *(Claude)*
- **src/wayfire.ini:** The `[input]` defaults and the settings list use Wayfire's option names *(Claude)*
- **README.md, src/wayfire.ini:** Night light is handled by budgie-daemon, which runs gammastep from the night-light settings; it works on Wayfire through the wlr gamma-control protocol *(Claude, directed by user)*
- **src/wayfire_bridge/bridge.py:** On startup the `[gamma]` section older versions wrote is removed *(Claude, directed by user)*

### Removed
- **src/wayfire_bridge/mappings.py, src/wayfire_bridge/transforms.py:** Touchpad `tap-button-map`: Wayfire has no such option *(Claude)*
- **src/wayfire_bridge/bridge.py:** The touchpad and mouse left-handed handlers, replaced by the shared flag *(Claude)*
- **src/wayfire_bridge/mappings.py, src/wayfire.ini:** Syncing night light to a `[gamma]` section: no Wayfire plugin reads it, so it never did anything *(Claude, directed by user)*

### Fixed
- **src/wayfire_bridge/media_keys.py:** The keyboard's own media keys (a key's `-static` bindings, like `XF86AudioRaiseVolume`) were only bound while no custom shortcut was set, so giving volume-up a shortcut disabled the volume key. Both are now bound, as in GNOME *(Claude)*
- **src/wayfire_bridge/transforms.py:** Wayfire resolves key names with libevdev, which rejects kernel aliases, so `XF86LaunchB` as `KEY_DASHBOARD` was never bound; it is `KEY_ALL_APPLICATIONS`. An XF86 keysym with no evdev key (`XF86Hibernate`, `XF86AudioRepeat`) is skipped instead of becoming an invalid `KEY_XF86…` name *(Claude)*
- **src/wayfire_bridge/mappings.py, src/wayfire_bridge/transforms.py:** GNOME's `custom` mouse and touchpad acceleration profile was passed through, which Wayfire rejects (it accepts `default`, `none`, `adaptive`, `flat`); it falls back to `default` *(Claude)*
- **src/wayfire_bridge/mappings.py:** Mouse natural scroll was written to `natural_scroll`, the touchpad's option, so it flipped the touchpad; it is `mouse_natural_scroll`, and touchpad natural scroll (written to the nonexistent `touchpad_natural_scroll`) is `natural_scroll` *(Claude)*
- **src/wayfire_bridge/mappings.py, src/wayfire_bridge/transforms.py:** Touchpad disable-while-typing, left-handed and send-events went to options Wayfire doesn't have: they are `disable_touchpad_while_typing`, the shared `left_handed_mode`, and `disable_touchpad_while_mouse` (true for disabled-on-external-mouse) *(Claude)*
- **src/wayfire_bridge/transforms.py:** Touchpad click methods `fingers` and `areas` were passed through, which Wayfire rejects; they are `clickfinger` and `button-areas` *(Claude)*
- **src/wayfire_bridge/bridge.py:** Edge tiling also wrote `[grid] mouse_snap`, which doesn't exist; `[move] enable_snap` alone covers it *(Claude)*
- **src/wayfire_bridge/bridge.py:** Mouse and touchpad changes only reached `wayfire.ini` at login: `setup_peripheral_monitoring` replaced the stored settings objects with new ones, and the change signals connected to the old ones stopped once they were freed, so speed, natural scroll, acceleration, tap-to-click and the rest didn't follow Control Center. Every handler now gets the one shared object from `_get_settings` *(Claude)*
- **src/wayfire_bridge/transforms.py:** The button layout only had its `:` removed, so `appmenu:minimize,maximize,close` became `appmenuminimize,maximize,close`, which Wayfire's decorations can't read. It is now the supported buttons (minimize, maximize, close) in the user's order, space-separated (`minimize maximize close`) *(Claude, directed by user)*
- **src/wayfire.ini:** The default `button_order` was comma-separated; it is `minimize maximize close` *(Claude, directed by user)*

---

## [2026-10-22]

### Added
- **src/wayfire_bridge/config_manager.py:** `remove_section` *(Claude)*
- **src/wayfire-bridge, src/systemd/wayfire-bridge.service:** Only one bridge runs at a time: a second one, from `[autostart]` and the systemd unit both, exits on a lock in `$XDG_RUNTIME_DIR/wayfire-bridge.lock` instead of fighting the first over `wayfire.ini`; the unit may write `%t` for it *(Claude)*

### Changed
- **src/wayfire_bridge/media_keys.py:** The magnifier key is bound to the mag plugin's own `[mag] toggle` (`disabled` when the key is cleared, so mag's default doesn't apply) and the plugin is loaded, but only if `libmag.so` is found where Wayfire looks for plugins (`WAYFIRE_PLUGIN_PATH`, then the usual libdirs); otherwise a warning says to install wayfire-plugins-extra. Old `[command]` magnifier entries are removed *(Claude, directed by user)*
- **src/wayfire_bridge/media_keys.py:** The magnifier zoom-in and zoom-out keys are left unbound with an info line, as neither mag (fixed `zoom_level`) nor zoom (Super+scroll) has zoom bindings *(Claude, directed by user)*
- **README.md, src/wayfire.ini:** The magnifier notes *(Claude, directed by user)*
- **src/wayfire_bridge/bridge.py:** Configs copied from the old shipped `wayfire.ini` keep its broken close, maximize, minimize and move-left/right `[command]` entries; on startup the bridge removes them, matching on their nonexistent commands (`wm-actions …`, `vswitch-move …`) so entries a user wrote are left alone *(Claude)*
- **src/wayfire_bridge/mappings.py:** `maximize` and `unmaximize` go to `[grid] slot_c` and `restore`, which fill the screen and restore it; only `toggle-maximized` uses `[wm-actions] toggle_maximize`. Merged into the toggle, Super+Up was bound by both the toggle and grid's `slot_c` default, and Super+Down maximized an unmaximized window *(Claude)*
- **src/wayfire_bridge/media_keys.py, src/wayfire_bridge/bridge.py:** A media key's command is the first of its candidates whose program is installed: the `command_gsetting` value (for the terminal, the default terminal), then `command`, then `fallback_command`; with none installed the first is bound anyway and a warning names them. The default-terminal handler goes through the same code instead of writing the setting's value as it is *(Claude, directed by user)*
- **src/wayfire_bridge/bridge.py:** On startup, `binding_win_*` and `binding_0` written by older versions are removed from `[vswitch]` *(Claude)*
- **src/wayfire.ini:** The settings list names `with_win_left/right` for moving a window between workspaces (was `[command] binding_move_left/right`) *(Claude)*
- **README.md:** The bridge's installed path (`/usr/libexec/budgie-desktop/wayfire-bridge`), the clone folder's name, debugging with `pkill -f wayfire-bridge` and `wayfire-bridge --verbose`, and no `__init__.py` or GTK theme in the lists *(Claude)*
- **src/wayfire.ini:** The settings list says focus mode comes from `com.solus-project.budgie-wm` and the follow-focus plugin, not `[core] focus_mode` *(Claude)*
- **src/wayfire_bridge/bridge.py:** On startup, configs written by older versions lose the `[notifications]` section and `[core] gtk_theme`, and `[vswitch] vwidth`/`vheight` are removed, a `vheight` set there moving to `[core]` *(Claude)*
- **src/wayfire.ini:** The `[command]` and `[vswitch]` comments and the commented-out example bindings give Wayfire's binding format, modifiers first (`<ctrl> <alt> KEY_T`), instead of `KEY_T CTRL ALT` *(Claude, directed by user)*
- **src/wayfire_bridge/media_keys.py:** The terminal shortcut runs the default terminal from `org.gnome.desktop.default-applications.terminal exec` (falling back to `x-terminal-emulator`), so changing the shortcut no longer resets the command the default-terminal handler wrote *(Claude)*

### Removed
- **src/wf-mag:** The magnifier helper: it called a `wf-msg` command Wayfire doesn't have, and meson never installed it *(Claude, directed by user)*
- **src/wayfire_bridge/transforms.py:** The unused `focus_mode` and `num_workspaces` transforms *(Claude)*
- **src/wayfire_bridge/mappings.py:** A second, identical `switch-to-workspace-last` entry *(Claude)*
- **src/wayfire_bridge/bridge.py:** A second placement-mode sync at startup, the same as the one just before it *(Claude)*
- **src/wayfire_bridge/bridge.py:** Writing Budgie's notification position to a `[notifications]` section, which isn't a Wayfire section *(Claude)*
- **src/wayfire_bridge/mappings.py, src/wayfire.ini:** `gtk-theme` to `[core] gtk_theme`, which isn't a Wayfire option *(Claude)*
- **src/wayfire.ini:** The `[command]` entries for close, maximize, minimize and moving a window to the left/right workspace: their bindings put the key before the modifiers (`KEY_Q ALT`) and their commands (`wm-actions close`, `vswitch-move left`) don't exist, so they did nothing. The bridge writes the real bindings to `[core]`, `[wm-actions]` and `[vswitch]` *(Claude, directed by user)*

### Fixed
- **src/wayfire_bridge/bridge.py, src/wayfire_bridge/mappings.py:** `[switcher] next_view`/`prev_view` and `[fast-switcher] activate`/`activate_backward` are Wayfire key options that take one binding, so a merged `<super> KEY_TAB | <alt> KEY_TAB` was rejected and Wayfire fell back to its default. These mappings are marked `single_binding`, and the bridge writes one binding, an `<alt>` one when there is one (Wayfire's own defaults are Alt+Tab and Alt+Esc) *(Claude)*
- **src/wayfire_bridge/mappings.py:** Wayfire numbers `[vswitch] binding_N` from 1, but `switch-to-workspace-1` was written as `binding_0`, so Super+Home went nowhere and every numbered shortcut was off by one *(Claude)*
- **src/wayfire_bridge/mappings.py:** Moving a window to another workspace did nothing: the bridge wrote `binding_win_*`, which Wayfire 0.11 doesn't have. `move-to-workspace-left/right` use `with_win_*` (the window moves and you follow, like mutter) and `move-to-workspace-N`/`-last` use `send_win_*` (the window moves, you stay) *(Claude)*
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
