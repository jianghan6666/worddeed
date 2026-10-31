import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from replication.executables import resolve_executable
from replication import reproduce, continue_stata


class ExecutableTests(unittest.TestCase):
    def test_path_lookup_does_not_turn_a_command_into_a_cwd_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / ('stata-mp.exe' if os.name == 'nt' else 'stata-mp')
            exe.write_text('fixture executable')
            exe.chmod(0o755)
            with patch.dict(os.environ, {'PATH': tmp}):
                self.assertEqual(resolve_executable(exe.name), str(exe.resolve()))

    def test_explicit_path_with_spaces_and_relative_path(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            exe = Path(tmp) / 'Stata MP.exe'
            exe.write_text('fixture executable')
            for value in [str(exe), os.path.relpath(exe)]:
                self.assertEqual(resolve_executable(value), str(exe.resolve()))

    def test_directory_is_not_an_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(FileNotFoundError, 'not an application directory'):
                resolve_executable(tmp)

    def test_both_drivers_reject_missing_stata_before_creating_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = str(root / 'missing-stata')
            for module, inputs in [(reproduce, ['--downloads', str(root / 'downloads')]),
                                   (continue_stata, ['--handoff', str(root / 'handoff'),
                                                     '--packages', str(root / 'packages')])]:
                out = root / module.__name__
                with self.subTest(driver=module.__name__), patch('sys.argv', [
                        'driver', *inputs, '--out', str(out), '--stata', missing]):
                    with self.assertRaisesRegex(FileNotFoundError, 'executable not found'):
                        module.main()
                    self.assertFalse(out.exists())
