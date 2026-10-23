"""
Mappings from gsettings to Wayfire configuration
Format: (schema, key): {'section': ..., 'option': ..., 'transform': ...}
"""

GSETTINGS_MAPPINGS = {
    # ==========================================================================
    # Desktop Interface Settings
    # ==========================================================================
    ('org.gnome.desktop.interface', 'cursor-theme'): {
        'section': 'input',
        'option': 'cursor_theme',
        'transform': 'str'
    },
    ('org.gnome.desktop.interface', 'cursor-size'): {
        'section': 'input',
        'option': 'cursor_size',
        'transform': 'int'
    },

    # ==========================================================================
    # Window Manager Preferences
    # ==========================================================================
    ('org.gnome.desktop.wm.preferences', 'button-layout'): {
        'section': 'decoration',
        'option': 'button_order',
        'transform': 'button_layout'
    },
    # vwidth is the workspace count divided by vheight (see _grid_columns)
    ('org.gnome.desktop.wm.preferences', 'num-workspaces'): {
        'section': 'core',
        'option': 'vwidth',
        'transform': 'int'
    },
    ('org.gnome.desktop.wm.preferences', 'titlebar-font'): {
        'section': 'decoration',
        'option': 'font',
        'transform': 'titlebar_font'
    },
    # ==========================================================================
    # Window Manager Keybindings
    # ==========================================================================
    # --- [core] ---
    # close is a core binding, not wm-actions
    ('org.gnome.desktop.wm.keybindings', 'close'): {
        'section': 'core',
        'option': 'close_top_view',
        'transform': 'keybinding'
    },

    # --- [wm-actions] activator bindings ---
    ('org.gnome.desktop.wm.keybindings', 'minimize'): {
        'section': 'wm-actions',
        'option': 'minimize',
        'transform': 'keybinding'
    },
    # maximize/unmaximize are one-way actions: grid's slot_c (fill the
    # screen) and restore. Only toggle-maximized uses the wm-actions toggle,
    # so Super+Up isn't bound by two plugins at once.
    ('org.gnome.desktop.wm.keybindings', 'maximize'): {
        'section': 'grid',
        'option': 'slot_c',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'unmaximize'): {
        'section': 'grid',
        'option': 'restore',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'toggle-maximized'): {
        'section': 'wm-actions',
        'option': 'toggle_maximize',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'toggle-fullscreen'): {
        'section': 'wm-actions',
        'option': 'toggle_fullscreen',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'toggle-on-all-workspaces'): {
        'section': 'wm-actions',
        'option': 'toggle_sticky',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'lower'): {
        'section': 'wm-actions',
        'option': 'send_to_back',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'raise'): {
        'section': 'wm-actions',
        'option': 'bring_to_front',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'show-desktop'): {
        'section': 'wm-actions',
        'option': 'toggle_showdesktop',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'always-on-top'): {
        'section': 'wm-actions',
        'option': 'toggle_always_on_top',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'toggle-above'): {
        'section': 'wm-actions',
        'option': 'toggle_always_on_top',
        'transform': 'keybinding'
    },

    # --- [switcher] - visual Alt-Tab style switcher ---
    # switch-applications and switch-windows both map to the visual switcher.
    # [switcher] and [fast-switcher] options are Wayfire "key" options, not
    # activators: they take exactly one binding, so 'single_binding' makes the
    # bridge pick one instead of writing a "|" list Wayfire would reject.
    ('org.gnome.desktop.wm.keybindings', 'switch-applications'): {
        'section': 'switcher',
        'option': 'next_view',
        'transform': 'keybinding',
        'single_binding': True,
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-applications-backward'): {
        'section': 'switcher',
        'option': 'prev_view',
        'transform': 'keybinding',
        'single_binding': True,
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-windows'): {
        'section': 'switcher',
        'option': 'next_view',
        'transform': 'keybinding',
        'single_binding': True,
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-windows-backward'): {
        'section': 'switcher',
        'option': 'prev_view',
        'transform': 'keybinding',
        'single_binding': True,
    },

    # --- [fast-switcher] - instant Alt-Escape style switcher ---
    # cycle-windows maps to fast-switcher (no visual, instant switch)
    ('org.gnome.desktop.wm.keybindings', 'cycle-windows'): {
        'section': 'fast-switcher',
        'option': 'activate',
        'transform': 'keybinding',
        'single_binding': True,
    },
    ('org.gnome.desktop.wm.keybindings', 'cycle-windows-backward'): {
        'section': 'fast-switcher',
        'option': 'activate_backward',
        'transform': 'keybinding',
        'single_binding': True,
    },

    # --- [vswitch] - workspace switching ---
    # move-to-workspace-left/right move the window and follow it: with_win_*
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-left'): {
        'section': 'vswitch',
        'option': 'with_win_left',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-right'): {
        'section': 'vswitch',
        'option': 'with_win_right',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-left'): {
        'section': 'vswitch',
        'option': 'binding_left',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-right'): {
        'section': 'vswitch',
        'option': 'binding_right',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-up'): {
        'section': 'vswitch',
        'option': 'binding_up',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-down'): {
        'section': 'vswitch',
        'option': 'binding_down',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-up'): {
        'section': 'vswitch',
        'option': 'with_win_up',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-down'): {
        'section': 'vswitch',
        'option': 'with_win_down',
        'transform': 'keybinding'
    },
    ('org.gnome.mutter', 'center-new-windows'): {
        'section': 'place',
        'option': 'mode',
        'transform': 'placement_mode'
    },
    # Keys with NO Wayfire equivalent — intentionally omitted:
    # begin-move, begin-resize        — move/resize are mouse-only in Wayfire
    # raise-or-lower                  — no equivalent
    # maximize-horizontally/vertically — no equivalent
    # switch-group, cycle-group (and backward variants) — no app grouping
    # switch-panels, cycle-panels (and backward variants) — no panel cycling
    # move-to-monitor-*               — oswitch has no gsettings-driven keybinding

    # ==========================================================================
    # Mutter Keybindings
    # ==========================================================================
    # toggle-tiled-left/right map to grid plugin half-screen slots.
    # These are the Super+Left / Super+Right snap-to-half-screen bindings.
    ('org.gnome.mutter.keybindings', 'toggle-tiled-left'): {
        'section': 'grid',
        'option': 'slot_l',
        'transform': 'keybinding'
    },
    ('org.gnome.mutter.keybindings', 'toggle-tiled-right'): {
        'section': 'grid',
        'option': 'slot_r',
        'transform': 'keybinding'
    },

    # ==========================================================================
    # Workspace-specific keybindings
    # ==========================================================================
    # GSettings and Wayfire both number workspaces from 1:
    # switch-to-workspace-N -> vswitch binding_N
    # move-to-workspace-N   -> vswitch send_win_N (moves the window only,
    #                          like mutter; with_win_N would also follow it)
    #
    # switch-to-workspace-last: labwc goes to absolute last workspace.
    # Wayfire binding_last goes to previously-active workspace.
    # No direct equivalent exists; binding_last is the closest match.

    # --- Switch to numbered workspace ---
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-1'): {
        'section': 'vswitch',
        'option': 'binding_1',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-2'): {
        'section': 'vswitch',
        'option': 'binding_2',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-3'): {
        'section': 'vswitch',
        'option': 'binding_3',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-4'): {
        'section': 'vswitch',
        'option': 'binding_4',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-5'): {
        'section': 'vswitch',
        'option': 'binding_5',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-6'): {
        'section': 'vswitch',
        'option': 'binding_6',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-7'): {
        'section': 'vswitch',
        'option': 'binding_7',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-8'): {
        'section': 'vswitch',
        'option': 'binding_8',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-9'): {
        'section': 'vswitch',
        'option': 'binding_9',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-10'): {
        'section': 'vswitch',
        'option': 'binding_10',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-11'): {
        'section': 'vswitch',
        'option': 'binding_11',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-12'): {
        'section': 'vswitch',
        'option': 'binding_12',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'switch-to-workspace-last'): {
        'section': 'vswitch',
        'option': 'binding_last',
        'transform': 'keybinding'
        # Note: labwc 'last' = absolute final workspace.
        # Wayfire binding_last = previously active workspace.
        # Closest available equivalent.
    },

    # --- Move window to numbered workspace ---
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-1'): {
        'section': 'vswitch',
        'option': 'send_win_1',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-2'): {
        'section': 'vswitch',
        'option': 'send_win_2',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-3'): {
        'section': 'vswitch',
        'option': 'send_win_3',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-4'): {
        'section': 'vswitch',
        'option': 'send_win_4',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-5'): {
        'section': 'vswitch',
        'option': 'send_win_5',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-6'): {
        'section': 'vswitch',
        'option': 'send_win_6',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-7'): {
        'section': 'vswitch',
        'option': 'send_win_7',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-8'): {
        'section': 'vswitch',
        'option': 'send_win_8',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-9'): {
        'section': 'vswitch',
        'option': 'send_win_9',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-10'): {
        'section': 'vswitch',
        'option': 'send_win_10',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-11'): {
        'section': 'vswitch',
        'option': 'send_win_11',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-12'): {
        'section': 'vswitch',
        'option': 'send_win_12',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'move-to-workspace-last'): {
        'section': 'vswitch',
        'option': 'send_win_last',
        'transform': 'keybinding'
        # Note: same semantic difference as switch-to-workspace-last above.
    },

    # switch-input-source and switch-input-source-backward are intentionally
    # NOT mapped. Wayfire has no keybinding mechanism for switching layouts.
    # Layout switching is handled entirely via xkb_options grp:* toggle options,
    # which are written to [input] xkb_options by get_merged_xkb_options().
    # The grp: option is auto-injected when multiple layouts are present.

    # ==========================================================================
    # Peripherals - Mouse
    # ==========================================================================
    ('org.gnome.desktop.peripherals.mouse', 'natural-scroll'): {
        'section': 'input',
        'option': 'mouse_natural_scroll',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.mouse', 'accel-profile'): {
        'section': 'input',
        'option': 'mouse_accel_profile',
        'transform': 'accel_profile'
    },
    ('org.gnome.desktop.peripherals.mouse', 'speed'): {
        'section': 'input',
        'option': 'mouse_cursor_speed',
        'transform': 'float'
    },
    # left_handed_mode and middle_emulation are single options in Wayfire,
    # shared by mouse and touchpad: the bridge turns them on if either
    # device's setting asks for it
    ('org.gnome.desktop.peripherals.mouse', 'left-handed'): {
        'section': 'input',
        'option': 'left_handed_mode',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.mouse', 'middle-click-emulation'): {
        'section': 'input',
        'option': 'middle_emulation',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'tap-and-drag'): {
        'section': 'input',
        'option': 'tap_and_drag',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'tap-and-drag-lock'): {
        'section': 'input',
        'option': 'drag_lock',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'middle-click-emulation'): {
        'section': 'input',
        'option': 'middle_emulation',
        'transform': 'bool'
    },
    # tap-button-map is not mapped: Wayfire has no tap button map option
    ('org.gnome.desktop.peripherals.touchpad', 'accel-profile'): {
        'section': 'input',
        'option': 'touchpad_accel_profile',   # different key from mouse_accel_profile
        'transform': 'accel_profile'
    },

    # ==========================================================================
    # Peripherals - Touchpad (libinput)
    # ==========================================================================
    ('org.gnome.desktop.peripherals.touchpad', 'natural-scroll'): {
        'section': 'input',
        'option': 'natural_scroll',   # touchpad; the mouse has mouse_natural_scroll
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'tap-to-click'): {
        'section': 'input',
        'option': 'tap_to_click',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'two-finger-scrolling-enabled'): {
        'section': 'input',
        'option': 'scroll_method',
        'transform': 'scroll_method'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'speed'): {
        'section': 'input',
        'option': 'touchpad_cursor_speed',
        'transform': 'float'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'scroll-speed'): {
        'section': 'input',
        'option': 'touchpad_scroll_speed',
        'transform': 'float'
    },
    # 'left'/'right'/'mouse'; 'mouse' follows the mouse's left-handed setting
    ('org.gnome.desktop.peripherals.touchpad', 'left-handed'): {
        'section': 'input',
        'option': 'left_handed_mode',
        'transform': 'touchpad_left_handed'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'disable-while-typing'): {
        'section': 'input',
        'option': 'disable_touchpad_while_typing',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'click-method'): {
        'section': 'input',
        'option': 'click_method',
        'transform': 'click_method'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'send-events'): {
        'section': 'input',
        'option': 'disable_touchpad_while_mouse',
        'transform': 'send_events'
    },

    # ==========================================================================
    # Peripherals - Keyboard
    # ==========================================================================
    ('org.gnome.desktop.peripherals.keyboard', 'delay'): {
        'section': 'input',
        'option': 'kb_repeat_delay',
        'transform': 'int'
    },
    # 'repeat' (key repeat on/off) has no option of its own: the bridge
    # writes kb_repeat_rate = 0 when it is off, which disables repeat
    ('org.gnome.desktop.peripherals.keyboard', 'repeat-interval'): {
        'section': 'input',
        'option': 'kb_repeat_rate',
        'transform': 'kb_repeat_rate'
    },
    ('org.gnome.desktop.peripherals.keyboard', 'numlock-state'): {
        'section': 'input',
        'option': 'kb_numlock_default_state',
        'transform': 'bool'
    },

    # ==========================================================================
    # Input Sources (Keyboard Layout)
    # These are written to BOTH wayfire.ini AND environment file
    # wayfire.ini: Direct config for Wayfire to use
    # environment: For XWayland and other apps
    # ==========================================================================
    ('org.gnome.desktop.input-sources', 'sources'): {
        'section': 'input',
        'option': 'xkb_layout',
        'transform': 'str'   # computed by the bridge, see _apply_setting
    },
    ('org.gnome.desktop.input-sources', 'xkb-options'): {
        'section': 'input',
        'option': 'xkb_options',
        'transform': 'str'   # computed by the bridge, see _apply_setting
    },

    # Night light is not mapped: Wayfire has no gamma plugin. budgie-daemon
    # reads org.gnome.settings-daemon.plugins.color itself and runs gammastep,
    # which works on Wayfire through the wlr gamma-control protocol.

}
