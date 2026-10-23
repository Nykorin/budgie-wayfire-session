# budgie-wayfire-session

A Wayland session for the Budgie desktop running on the [Wayfire](https://wayfire.org) compositor. It adds a "Budgie Desktop (Wayfire)" entry to the login screen, and its bridge keeps Wayfire in step with Budgie's settings: keyboard shortcuts, mouse and keyboard options, cursor, workspaces and window behaviour changed in Budgie Control Center or Budgie Desktop Settings apply to Wayfire straight away.

This is a fork of [UbuntuBudgie/budgie-wayfire-session](https://github.com/UbuntuBudgie/budgie-wayfire-session).

> [!IMPORTANT]
> **This fork's changes were written with AI.** Everything after upstream commit `41842ea`, listed in [`CHANGELOG.md`](CHANGELOG.md), was written by Claude (Anthropic), following the author's design, requests and review; the code before it is Ubuntu Budgie's. The author tested it only on their own system (CachyOS, Wayfire 0.11, Budgie 10.10), and it has not been reviewed or tested by anyone else, including the upstream project. The magnifier and focus-follows-mouse also need wayfire-plugins-extra built for your Wayfire version. Read the changes before installing, and keep a copy of `~/.config/budgie-desktop/wayfire/`. It comes with no warranty.

## Dependencies

Arch package names are the ones on the tested system. Debian/Ubuntu names are the usual equivalents and have not been tested.

### To build

| What | Arch | Debian/Ubuntu |
|---|---|---|
| meson 0.60 or newer | `meson` | `meson` |
| ninja | `ninja` | `ninja-build` |

Nothing is compiled: meson only installs the files.

### To run

| What | Used for | Arch | Debian/Ubuntu |
|---|---|---|---|
| Wayfire (tested with 0.11) | the compositor | `wayfire` | `wayfire` |
| Budgie 10.10 | panel, Raven, `budgie-daemon` (night light, OSD), the settings app, run and power dialogs, screenshots | `budgie-desktop` | `budgie-desktop` |
| budgie-session | `budgie-session-binary`, which the launcher waits for; `budgie-session-quit` for the logout key | `budgie-session` | `budgie-session` |
| Python 3 | the bridge | `python` | `python3` |
| PyGObject with GLib/Gio | reading GSettings | `python-gobject`, `glib2` | `python3-gi`, `gir1.2-glib-2.0` |
| GNOME desktop schemas | most of the settings the bridge reads | `gsettings-desktop-schemas` | `gsettings-desktop-schemas` |
| D-Bus tools | `dbus-send` (Budgie actions), `dbus-update-activation-environment` (autostart), `dbus-launch` (only if no session bus is running) | `dbus` | `dbus`, `dbus-x11` |
| procps | `pgrep`; `pidwait` (procps 4) if present, a polling loop otherwise | `procps-ng` | `procps` |
| util-linux | `logger` in the launcher | `util-linux` | `bsdutils` |
| xdg-desktop-portal | file pickers and screen sharing for apps | `xdg-desktop-portal`, `xdg-desktop-portal-gtk` | `xdg-desktop-portal`, `xdg-desktop-portal-gtk` |

### Recommended

| What | Used for | Arch | Debian/Ubuntu |
|---|---|---|---|
| Budgie Control Center | changing the settings the bridge syncs | `budgie-control-center` | `budgie-control-center` |
| mutter's schemas | Super key menu, centering new windows, tiling shortcuts (`org.gnome.mutter`); without them those settings are skipped | `mutter` | `mutter-common` |
| dbus-python | following system keyboard layout changes (systemd-localed) | `python-dbus` | `python3-dbus` |
| WirePlumber | volume and mic-mute keys (`wpctl`) | `wireplumber` | `wireplumber` |
| playerctl | play/pause, next, previous and stop keys | `playerctl` | `playerctl` |
| xdg-utils | email, file manager and browser keys (`xdg-email`, `xdg-open`, `xdg-settings`) | `xdg-utils` | `xdg-utils` |
| xdg-terminal-exec | the terminal key when Budgie's default terminal is set to it | `xdg-terminal-exec` | `xdg-terminal-exec` |
| gammastep | night light, run by `budgie-daemon` | `gammastep` | `gammastep` |
| wayfire-plugins-extra, built for your Wayfire | magnifier (`mag`) and focus-follows-mouse (`follow-focus`) | build from source if the packaged one is older than Wayfire | `wayfire-plugins-extra` |
| Wayfire Config Manager | changing Wayfire's own options (effects, animations, title bars) | `wcm` | `wcm` |
| mesa-utils | `eglinfo`, used only to detect virgl in VMs | `mesa-utils` | `mesa-utils` |

The media keys also call a browser, email client and calculator: `x-www-browser` where it exists (Debian and Ubuntu), else your default browser through `xdg-settings` and `gtk-launch`; and the first installed of `xdg-email`/`thunderbird` and `mate-calc`/`gnome-calculator`.

A Wayfire plugin only loads in the Wayfire version it was built for, and Wayfire skips a mismatched one without saying so on screen. If the magnifier or focus-follows-mouse stops working after a Wayfire update, rebuild wayfire-plugins-extra.

## Install

    git clone https://github.com/Nykorin/budgie-wayfire-session
    cd budgie-wayfire-session
    meson setup build --prefix=/usr
    sudo meson install -C build

Log out and choose **Budgie Desktop (Wayfire)** at the login screen.

This installs:

| File | Purpose |
|---|---|
| `/usr/bin/startbudgiewayfire` | the session launcher |
| `/usr/share/wayland-sessions/budgie-wayfire.desktop` | the login screen entry |
| `/usr/share/budgie-desktop/wayfire/wayfire.ini` | the default Wayfire config |
| `/usr/libexec/budgie-desktop/wayfire-bridge`, `wayfire_bridge/` | the bridge |

`src/systemd/wayfire-bridge.service` is not installed: the default config starts the bridge from `[autostart]`. Only one bridge runs at a time, so enabling the unit as well is harmless.

## How it works

The launcher sets up the Wayland environment and, on first login, copies the default config to `~/.config/budgie-desktop/wayfire/wayfire.ini`, so Budgie's Wayfire config stays apart from any other Wayfire setup. It starts Wayfire with that config, waits for the Budgie session and stops Wayfire when the session ends. Wayfire's `[autostart]` starts Budgie, the portal and the bridge.

The bridge watches GSettings and writes the matching options into `wayfire.ini`, which Wayfire reloads by itself. It also writes `~/.config/budgie-desktop/wayfire/environment` (keyboard layout, cursor and locale for XWayland and new apps), which the launcher reads at login.

## What the bridge syncs

- **Windows:** close, minimize, maximize and restore, toggle maximized, fullscreen, always on top, show on all workspaces, raise and lower, show desktop, tile left and right, the Alt+Tab switcher and fast window cycling, title-bar buttons and font, focus mode (follow-focus needs wayfire-plugins-extra), edge tiling, and centering new windows.
- **Workspaces:** how many there are, laid out as the squarest grid they fill exactly (4 make 2×2, 6 make 3×2, 9 make 3×3, and a prime number of them one row), switching left/right/up/down, to the previously used one or to 1–12, and moving the focused window to any of those.
- **Budgie:** the Super key opens the Budgie menu. Shortcuts for Raven, notifications, the power dialog, screenshots and the run dialog work.
- **Keyboard:** layouts and their variants, XKB options (from GSettings, else systemd-localed, else `/etc/default/keyboard`), key repeat on/off, delay and rate, and Num Lock at startup.
- **Mouse and touchpad:** speed, acceleration profile, natural scrolling, left-handed mode, and middle-click emulation. For touchpads also tap-to-click, tap-and-drag, drag lock, scroll method and speed, click method, disable while typing, and disable while a mouse is connected.
- **Cursor:** theme and size.
- **Media keys:** terminal, browser, email, file manager, calculator, settings, lock screen, log out, volume, mic mute, playback, screen brightness and magnifier. The keyboard's own keys stay bound alongside any custom shortcut.
- **Custom shortcuts** from Budgie Control Center, as they are added, changed and removed.

Some settings can't be synced because Wayfire has no equivalent:

- Wayfire's window switcher takes one key, so "Switch windows" has no effect while "Switch applications" has an Alt binding.
- "Show all windows in tab switcher".
- Custom acceleration curves (the default profile is used instead).
- The touchpad tap button map.
- Title-bar click actions and the double-click time.
- Magnifier zoom in and out (with the zoom plugin, Super+scroll zooms the whole screen).
- Moving windows between monitors.
- Keyboard backlight keys: Budgie has no tool for the keyboard backlight.

Night light isn't the bridge's job: `budgie-daemon` runs gammastep, which works on Wayfire.

## Your config

- **Settings the bridge manages:** set these in Budgie's settings, not in `wayfire.ini`. The GSettings value replaces a hand edit the next time that setting changes or you log in.
- **Everything else in `wayfire.ini`:** plugins, effects, animations, title-bar sizes and the like are yours to change, by hand or in Wayfire Config Manager, even while logged in. The bridge keeps those edits when it saves.

To start again from the default config, move `~/.config/budgie-desktop/wayfire/` aside and log in again.

## Debugging

Wayfire's output, along with that of Budgie and the bridge, goes to `~/.local/state/budgie-wayfire/wayfire.log`; the previous session's is `wayfire.log.old`. Look there for options Wayfire rejected and plugins that failed to load.

To watch the bridge in detail, stop it and run it by hand with debug output:

    pkill -f wayfire-bridge
    /usr/libexec/budgie-desktop/wayfire-bridge --verbose

## Tests

    tests/run.sh

The tests use Python's `unittest`, nothing to install beyond the bridge's own dependencies. GSettings are kept in memory and every test works on temporary files, so your settings and `~/.config` are never touched. They cover the value conversions, every GSettings mapping and handler syncing into `wayfire.ini`, cleanup of configs from older versions, keeping edits made in WCM, the shipped `wayfire.ini`, the bridge's single-instance lock, and the launcher, including that it only counts this user's session and refuses a runtime directory that isn't private. Tests that need Wayfire's option metadata (`/usr/share/wayfire/metadata`), libevdev or Budgie's GSettings schemas are skipped where those aren't installed. `tests/run.sh -v` lists every test; `tests/run.sh -k magnifier` runs the matching ones. To check against another Wayfire build's options, point `WAYFIRE_METADATA_DIR` at its `share/wayfire/metadata` folder.

## Known limitations

- Tested only on CachyOS with Wayfire 0.11 and Budgie 10.10.
- The default config starts the portal from `/usr/libexec/xdg-desktop-portal`. Arch installs it in `/usr/lib/`, so that line does nothing there; the portal still starts on demand over D-Bus.
- Wayfire's `animate` plugin logs `Unknown animation type: ""` for Budgie's panel and desktop, which get no animation. This is harmless.

## Code layout

```
src/
├── startbudgiewayfire.in      # session launcher (meson fills in the paths)
├── budgie-wayfire.desktop     # login screen entry
├── wayfire.ini                # default Wayfire config
├── systemd/                   # optional user unit for the bridge
├── wayfire-bridge             # bridge entry point: arguments, logging, single-instance lock
└── wayfire_bridge/
    ├── bridge.py              # watches GSettings, writes wayfire.ini and the environment file
    ├── mappings.py            # GSettings key -> wayfire.ini option table
    ├── transforms.py          # value conversions (key names, button layout, ...)
    ├── config_manager.py      # reads and writes wayfire.ini, keeps external edits
    ├── media_keys.py          # media and launcher keys
    ├── budgie_wm_actions.py   # Budgie actions (Raven, screenshots, power dialog, ...)
    ├── keybindings.py         # custom shortcuts
    └── logging_config.py      # logging setup
tests/                         # unittest suite, run with tests/run.sh
```

## License

MIT, see [LICENSE](LICENSE). Copyright Ubuntu Budgie; changes in this fork by Nykorin, written with Claude.
