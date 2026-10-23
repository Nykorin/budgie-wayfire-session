"""The bridge's entry point (src/wayfire-bridge): the single-instance lock."""
import importlib.machinery
import importlib.util
import logging
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers import SRC

ENTRY_POINT = SRC / 'wayfire-bridge'
LOGGER = 'wayfire_bridge.entry-point-test'


def load_entry_point():
    loader = importlib.machinery.SourceFileLoader('wayfire_bridge_entry', str(ENTRY_POINT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class InstanceLock(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.entry = load_entry_point()

    def tearDown(self):
        self._tmp.cleanup()

    def environment(self, **values):
        env = {k: v for k, v in os.environ.items() if k not in ('XDG_RUNTIME_DIR', 'XDG_CACHE_HOME')}
        env.update(values)
        return mock.patch.dict(os.environ, env, clear=True)

    def acquire_in_another_process(self, env):
        """Whether a separate process (a second bridge) gets the lock."""
        code = ('import importlib.machinery as m, importlib.util as u\n'
                f'loader = m.SourceFileLoader("e", {str(ENTRY_POINT)!r})\n'
                'e = u.module_from_spec(u.spec_from_loader("e", loader)); loader.exec_module(e)\n'
                'print("held" if e.acquire_instance_lock() else "refused")')
        env = dict(env, PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, timeout=20)
        return result.stdout.strip()

    def test_lock_in_the_runtime_directory(self):
        runtime = self.tmp / 'runtime'
        runtime.mkdir(mode=0o700)
        with self.environment(XDG_RUNTIME_DIR=str(runtime)):
            lock = self.entry.acquire_instance_lock()
            self.addCleanup(lock.close)
            self.assertEqual(Path(lock.name), runtime / 'wayfire-bridge.lock')
            self.assertEqual(self.acquire_in_another_process(dict(os.environ)), 'refused')
        lock.close()
        with self.environment(XDG_RUNTIME_DIR=str(runtime)):
            self.assertEqual(self.acquire_in_another_process(dict(os.environ)), 'held')

    def test_without_runtime_directory_the_lock_is_per_user_not_in_tmp(self):
        cache = self.tmp / 'cache'
        with self.environment(XDG_CACHE_HOME=str(cache)):
            lock = self.entry.acquire_instance_lock()
            self.addCleanup(lock.close)
        lock_path = Path(lock.name)
        self.assertEqual(lock_path, cache / 'budgie-wayfire' / 'wayfire-bridge.lock')
        self.assertEqual(oct(lock_path.parent.stat().st_mode & 0o777), '0o700')

    def test_without_runtime_or_cache_variable_the_lock_is_under_home(self):
        with self.environment(HOME=str(self.tmp)):
            lock = self.entry.acquire_instance_lock()
            self.addCleanup(lock.close)
        self.assertEqual(Path(lock.name), self.tmp / '.cache' / 'budgie-wayfire' / 'wayfire-bridge.lock')


class Main(unittest.TestCase):
    """main() with the bridge itself replaced by a stand-in."""

    def setUp(self):
        self.entry = load_entry_point()
        self.started = []
        started = self.started

        class FakeBridge:
            def run(self):
                started.append(True)

        patcher = mock.patch('wayfire_bridge.bridge.WayfireBridge', FakeBridge)
        patcher.start()
        self.addCleanup(patcher.stop)
        argv = mock.patch.object(sys, 'argv', ['wayfire-bridge'])
        argv.start()
        self.addCleanup(argv.stop)
        # main()'s own logger, so the tests can read what it logs
        quiet = mock.patch.object(self.entry, 'setup_logging', return_value=logging.getLogger(LOGGER))
        quiet.start()
        self.addCleanup(quiet.stop)

    def test_runs_without_a_lock_it_cannot_create(self):
        with mock.patch.object(self.entry, 'acquire_instance_lock', side_effect=PermissionError('denied')):
            with self.assertLogs(LOGGER, 'WARNING') as logged:
                self.entry.main()
        self.assertEqual(self.started, [True])
        self.assertIn('running without it', logged.output[0])

    def test_exits_when_another_bridge_holds_the_lock(self):
        with mock.patch.object(self.entry, 'acquire_instance_lock', return_value=None):
            with self.assertRaises(SystemExit) as raised, self.assertLogs(LOGGER, 'WARNING'):
                self.entry.main()
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(self.started, [])


if __name__ == '__main__':
    unittest.main()
