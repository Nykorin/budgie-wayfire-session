python = import('python').find_installation('python3')

prefix = get_option('prefix')

libexecdir = join_paths(prefix, 'lib', 'budgie-desktop')
bindir    = join_paths(prefix, 'bin')
datadir   = join_paths(prefix, 'share')

#
# Install Python entry point
#
install_data(
  'wayfire-bridge',
  install_dir: libexecdir
)

#
# Install Python package
#
install_subdir(
  'wayfire_bridge',
  install_dir: libexecdir
)

#
# Configure + install startbudgiewayfire
#
configure_file(
  input: 'startbudgiewayfire.in',
  output: 'startbudgiewayfire',
  configuration: {
    'datadir': datadir,
  },
  install: true,
  install_dir: bindir
)

#
# Install Wayfire config
#
install_data(
  'wayfire.ini',
  install_dir: join_paths(datadir, 'budgie-desktop', 'wayfire')
)

#
# Install Wayland session desktop file
#
install_data(
  'budgie-wayfire.desktop',
  install_dir: join_paths(datadir, 'wayland-sessions')
)
