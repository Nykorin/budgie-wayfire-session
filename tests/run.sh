#!/bin/sh
# Run the tests. GSettings are kept in memory and every test works on
# temporary files, so the desktop's settings and config are never touched.
# Options go to unittest: tests/run.sh -v, or tests/run.sh -k magnifier
cd "$(dirname "$0")/.." || exit 1
GSETTINGS_BACKEND=memory exec python3 -B -W ignore::DeprecationWarning:gi.events -m unittest discover -s tests -t . "$@"
