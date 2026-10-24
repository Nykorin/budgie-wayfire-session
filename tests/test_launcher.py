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

    def test_names_the_desktop_for_wayfire_and_systemd(self):
        imported = self.tmp / 'imported'
        self.stub('systemctl', f'echo "$* $XDG_CURRENT_DESKTOP" > "{imported}"')
        script = self.section('# Name the desktop', '\nfi') + '\necho "$XDG_CURRENT_DESKTOP"'
        result = self.run_bash('XDG_CURRENT_DESKTOP=GNOME\n' + script)
        self.assertEqual(result.stdout.strip(), 'Budgie:wayfire:wlroots')
        self.assertEqual(imported.read_text().strip(),
                         '--user import-environment XDG_CURRENT_DESKTOP Budgie:wayfire:wlroots')

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


    def test_session_check_and_wait_count_only_this_users_processes(self):
        # Record how pgrep and pidwait are called; the session "runs" until
        # pidwait returns, then wayfire is stopped
        calls = self.tmp / 'calls'
        self.stub('wayfire', 'sleep 30')
        self.stub('pgrep', f'echo "pgrep $*" >> "{calls}"; exit 0')
        self.stub('pidwait', f'echo "pidwait $*" >> "{calls}"; exit 0')
        script = (self.section('is_session_running() {', '\n}')
                  + '\n' + self.section('# Start wayfire in the background', '\nexit 0'))
        self.assertEqual(self.run_bash(script.replace('sleep 0.5', 'sleep 0.1')).returncode, 0)
        uid = str(os.getuid())
        recorded = calls.read_text().splitlines()
        self.assertIn(f'pgrep -u {uid} -f budgie-session-binary', recorded)
        self.assertIn(f'pidwait -u {uid} -f budgie-session-binary', recorded)

    def test_session_check_still_finds_our_own_session(self):
        # With the real pgrep: a process of ours named budgie-session-binary
        # counts as the session
        process = subprocess.Popen(['bash', '-c', 'exec -a budgie-session-binary sleep 30'])
        self.addCleanup(process.kill)
        script = self.section('is_session_running() {', '\n}') + '\nis_session_running'
        result = subprocess.run(['bash', '-c', script], capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0)


@unittest.skipUnless(shutil.which('bash') and shutil.which('stat'), 'bash or stat not found')
class RuntimeDirectory(unittest.TestCase):
    """The launcher only starts with a runtime directory that is ours and private."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.bin = self.tmp / 'bin'
        self.bin.mkdir()
        (self.bin / 'logger').write_text('#!/bin/sh\nexit 0\n')
        (self.bin / 'logger').chmod(0o755)
        text = LAUNCHER.read_text()
        match = re.search(r'# Set the XDG_RUNTIME_DIR.*?not starting"\n    exit 1\nfi\n', text, re.S)
        self.assertIsNotNone(match, 'runtime directory block not found in the launcher')
        self.block = match.group(0)

    def tearDown(self):
        for path in self.tmp.rglob('*'):
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o700)
        self._tmp.cleanup()

    def run_block(self, runtime_dir=None, block=None):
        env = {'PATH': f'{self.bin}:/usr/bin:/bin', 'HOME': str(self.tmp), 'USER': 'tester'}
        if runtime_dir is not None:
            env['XDG_RUNTIME_DIR'] = str(runtime_dir)
        script = (block or self.block) + 'echo "STARTED $XDG_RUNTIME_DIR"\n'
        return subprocess.run(['bash', '-c', script], env=env, capture_output=True, text=True, timeout=20)

    def assertStarts(self, result, runtime_dir):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'STARTED {runtime_dir}', result.stdout)

    def assertRefused(self, result):
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('STARTED', result.stdout)

    def test_missing_directory_is_created_private(self):
        runtime = self.tmp / 'runtime'
        self.assertStarts(self.run_block(runtime), runtime)
        self.assertEqual(oct(runtime.stat().st_mode & 0o777), '0o700')

    def test_existing_private_directory_is_used(self):
        runtime = self.tmp / 'runtime'
        runtime.mkdir(mode=0o700)
        self.assertStarts(self.run_block(runtime), runtime)

    def test_directory_others_can_use_is_refused(self):
        runtime = self.tmp / 'runtime'
        runtime.mkdir()
        for mode in (0o777, 0o755, 0o770):
            runtime.chmod(mode)
            with self.subTest(oct(mode)):
                self.assertRefused(self.run_block(runtime))

    def test_symlink_is_refused(self):
        target = self.tmp / 'target'
        target.mkdir(mode=0o700)
        link = self.tmp / 'runtime'
        link.symlink_to(target)
        self.assertRefused(self.run_block(link))

    def test_file_is_refused(self):
        runtime = self.tmp / 'runtime'
        runtime.write_text('')
        self.assertRefused(self.run_block(runtime))

    def test_tmp_fallback_made_by_someone_else_is_refused(self):
        # A system without /run/user: the launcher falls back to
        # /tmp/$USER-runtime (here inside the test folder). Another user who
        # created it first leaves it world-writable
        fallback_root = self.tmp / 'tmp'
        fallback_root.mkdir()
        block = (self.block.replace('"/run/user"', '"/nonexistent/run/user"')
                           .replace('"/var/run/user"', '"/nonexistent/var/run/user"')
                           .replace('/tmp/${USER}-runtime', f'{fallback_root}/${{USER}}-runtime'))
        self.assertNotEqual(block, self.block)
        planted = fallback_root / 'tester-runtime'
        planted.mkdir()
        planted.chmod(0o777)
        self.assertRefused(self.run_block(block=block))

        planted.rmdir()
        result = self.run_block(block=block)
        self.assertStarts(result, planted)
        self.assertEqual(oct(planted.stat().st_mode & 0o777), '0o700')


if __name__ == '__main__':
    unittest.main()
