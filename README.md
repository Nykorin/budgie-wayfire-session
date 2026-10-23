session creation for wayfire with budgie-desktop

# ubuntu prereqs
    sudo apt install meson build-essential git
    sudo apt install procps wayfire

# install and start
    git clone https://github.com/ubuntubudgie/budgie-wayfire-session
    cd budgie-wayfire-session
    meson build --prefix=/usr
    sudo meson install -C build

At the login screen, choose the budgie (wayfire) session to launch

```
in the src folder
wayfire-bridge                 # Main entry point
wayfire_bridge/
├── bridge.py                  # Core bridge coordinator
├── config_manager.py          # Config file I/O
├── transforms.py              # Value transformation functions
├── keybindings.py             # Custom keybindings handler
├── media_keys.py              # Static media keys handler
└── mappings.py                # Gsettings mappings configuration

Supported Settings
Desktop Interface

Cursor theme and size
Focus mode

Input Devices (libinput)
Mouse:

Natural scrolling
Acceleration profile
Cursor speed
Left-handed mode

Touchpad:

Natural scrolling
Tap-to-click
Scroll method (two-finger/edge)
Cursor speed
Left-handed mode
Disable while typing
Click method
Send events mode

Keyboard:

Repeat rate and delay
Numlock default state

Window Management

Window decorations button layout
Window close/maximize/minimize keybindings
Move window to workspace keybindings

Workspaces (Viewports)

Number of workspaces
Workspace switching keybindings (left/right/up/down)

Media Keys

Terminal launcher
Web browser
Email client
File manager
Calculator
Help browser
TBD Magnifier toggle (requires mag plugin)
TBD Magnifier zoom in/out
Screen reader toggle
Lock screen

Display

Night light (gamma adjustment)
Color temperature

Custom Keybindings

Automatically synced from budgie-control-center
Full create/update/delete support
```

installs wayfire.ini to ~/.config/budgie-desktop/wayfire/

the autostart section of wayfire.ini starts budgie by running budgie-desktop
It also starts the bridge that is installed to /usr/libexec/budgie-desktop/wayfire-bridge

----

# debugging

kill the running bridge

    pkill -f wayfire-bridge

Manually run it with debug output

    /usr/libexec/budgie-desktop/wayfire-bridge --verbose

Note the output from the bridge to aid debugging.
