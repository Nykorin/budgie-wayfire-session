"""The session launcher (src/startbudgiewayfire.in), run with stand-in commands."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.helpers import SRC

LAUNCHER = SRC / 'startbudgiewayfire.in'


@unittest.skipUnless(shutil.which('bash'), 'bash not found')
class Launcher(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.bin = self.tmp / 'bin'
        self.bin.mkdir()
        self.state = self.tmp / 'state'

    def tearDown(self):
        self._tmp.cleanup()

    def stub(self, name, script):
        path = self.bin / name
        path.write_text('#!/bin/sh\n' + script + '\n')
        path.chmod(0o755)

    def run_bash(self, script):
        env = {'PATH': f'{self.bin}:/usr/bin:/bin', 'HOME': str(self.tmp),
               'XDG_STATE_HOME': str(self.state), 'WAYFIRE_CONFIG_FILE': '/x/wayfire.ini'}
        return subprocess.run(['bash', '-c', script], env=env, capture_output=True, text=True, timeout=20)

    def section(self, start, end):
        """The launcher's lines from START up to and including END."""
        text = LAUNCHER.read_text()
        match = re.search(re.escape(start) + r'.*?' + re.escape(end), text, re.S)
        self.assertIsNotNone(match, f'{start!r} … {end!r} not found in the launcher')
        return match.group(0)

    def test_syntax(self):
        self.assertEqual(subprocess.run(['bash', '-n', str(LAUNCHER)]).returncode, 0)

    def test_log_file_and_rotation(self):
        self.stub('wayfire', 'echo "started $*"; echo "EE an error" >&2')
        start = self.section("# Log wayfire's output", 'WAYFIRE_PID=$!') + '\nwait $WAYFIRE_PID\n'
        log = self.state / 'budgie-wayfire' / 'wayfire.log'
        self.run_bash(start)
        first = log.read_text()
        self.assertIn('started --config /x/wayfire.ini', first)
        self.assertIn('EE an error', first)  # errors go to the log too
        self.run_bash(start)
        self.assertEqual((log.parent / 'wayfire.log.old').read_text(), first)

    def test_ends_when_wayfire_exits_before_the_session_starts(self):
        # No Budgie session ever appears (pgrep finds nothing) and wayfire
        # quits at once: the launcher must not wait forever
        self.stub('wayfire', 'exit 0')
        self.stub('pgrep', 'exit 1')
        script = (self.section('is_session_running() {', '\n}')
                  + '\n' + self.section('# Start wayfire in the background', '\nexit 0'))
        script = script.replace('sleep 0.5', 'sleep 0.1')
        self.assertEqual(self.run_bash(script).returncode, 0)

    def test_waits_without_pidwait(self):
        # Session running for a moment, no pidwait: the fallback loop waits
        # until the session is gone, then stops wayfire
        marker = self.tmp / 'session-up'
        marker.write_text('')
        self.stub('wayfire', 'sleep 30')
        self.stub('pgrep', f'test -e "{marker}"')
        self.stub('pidwait', 'exit 127')
        script = (self.section('is_session_running() {', '\n}')
                  + '\ncommand() { [ "$2" = pidwait ] && return 1; builtin command "$@"; }\n'
                  + f'( sleep 1.5; rm -f "{marker}" ) &\n'
                  + self.section('# Start wayfire in the background', '\nexit 0'))
        result = self.run_bash(script)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
