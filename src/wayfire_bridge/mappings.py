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
    # maximize, unmaximize, toggle-maximized all map to the same toggle
    ('org.gnome.desktop.wm.keybindings', 'maximize'): {
        'section': 'wm-actions',
        'option': 'toggle_maximize',
        'transform': 'keybinding'
    },
    ('org.gnome.desktop.wm.keybindings', 'unmaximize'): {
        'section': 'wm-actions',
        'option': 'toggle_maximize',
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
    # switch-to-workspace-1..8        — static numbered slots, not dynamically mappable
    # move-to-workspace-1..8          — same

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
        'option': 'natural_scroll',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.mouse', 'accel-profile'): {
        'section': 'input',
        'option': 'mouse_accel_profile',
        'transform': 'str'
    },
    ('org.gnome.desktop.peripherals.mouse', 'speed'): {
        'section': 'input',
        'option': 'mouse_cursor_speed',
        'transform': 'float'
    },
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
    ('org.gnome.desktop.peripherals.touchpad', 'tap-button-map'): {
        'section': 'input',
        'option': 'tap_button_map',
        'transform': 'tap_button_map'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'accel-profile'): {
        'section': 'input',
        'option': 'touchpad_accel_profile',   # different key from mouse_accel_profile
        'transform': 'str'
    },

    # ==========================================================================
    # Peripherals - Touchpad (libinput)
    # ==========================================================================
    ('org.gnome.desktop.peripherals.touchpad', 'natural-scroll'): {
        'section': 'input',
        'option': 'touchpad_natural_scroll',
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
    # Note: left-handed for touchpad handled specially due to 'mouse' option
    ('org.gnome.desktop.peripherals.touchpad', 'left-handed'): {
        'section': 'input',
        'option': 'touchpad_left_handed_mode',
        'transform': 'touchpad_left_handed'  # Special transform
    },
    ('org.gnome.desktop.peripherals.touchpad', 'disable-while-typing'): {
        'section': 'input',
        'option': 'disable_while_typing',
        'transform': 'bool'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'click-method'): {
        'section': 'input',
        'option': 'click_method',
        'transform': 'str'
    },
    ('org.gnome.desktop.peripherals.touchpad', 'send-events'): {
        'section': 'input',
        'option': 'touchpad_send_events',
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
        'transform': 'xkb_layout'
    },
    ('org.gnome.desktop.input-sources', 'xkb-options'): {
        'section': 'input',
        'option': 'xkb_options',
        'transform': 'xkb_options'
    },

    # ==========================================================================
    # Display Settings (Night Light)
    # ==========================================================================
    ('org.gnome.settings-daemon.plugins.color', 'night-light-enabled'): {
        'section': 'gamma',
        'option': 'enabled',
        'transform': 'bool'
    },
    ('org.gnome.settings-daemon.plugins.color', 'night-light-temperature'): {
        'section': 'gamma',
        'option': 'temperature',
        'transform': 'int'
    },

}
