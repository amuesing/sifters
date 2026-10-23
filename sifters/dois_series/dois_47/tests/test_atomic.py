"""mid/ must survive anything that goes wrong after the renders begin.

dois_31 stopped a bad SETTING from replacing the twelve files, by refusing before the
first write. That left the other half: a failure during rendering or verification. Up to
dois_32 each pitch mode was written straight into mid/ and checked afterwards, so a mode
that failed verification had already replaced your files by the time you were told, and a
crash between the two modes left six new files beside six old ones.

dois_33 renders into a staging folder and moves the files into mid/ only once every file
has been written AND verified.
"""
import glob
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_engine import project_copy, rendered, run

# Patch compose's OWN references: it imports these names directly.
BREAK_VERIFY = '''
import compose, sys
real = compose.verify
def failing(*args, **kwargs):
    real(*args, **kwargs)
    return False                   # verified, then reported as failed
compose.verify = failing
try:
    compose.main()
except SystemExit as stop:
    sys.exit(0 if stop.code else 'expected a non-zero exit')
sys.exit('expected SystemExit')
'''

BREAK_WRITE = '''
import compose, sys
def failing(*args, **kwargs):     # the MIDI and the tables are already staged
    raise RuntimeError('disk went away')
compose.write_presets = failing
try:
    compose.main()
except RuntimeError as boom:
    sys.exit(0 if 'disk went away' in str(boom) else f'wrong error: {boom}')
sys.exit('expected RuntimeError')
'''


class MidSurvives(unittest.TestCase):

    def rendered_copy(self, tmp):
        root = project_copy(tmp)
        self.assertEqual(run(root).returncode, 0)
        before = rendered(root)
        self.assertEqual(len(before), 13)      # 1 MIDI, 8 wavetables, 4 presets
        return root, before

    def assert_untouched(self, script):
        with tempfile.TemporaryDirectory() as tmp:
            root, before = self.rendered_copy(tmp)
            result = subprocess.run([sys.executable, '-B', '-c', script], cwd=root,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertEqual(before, rendered(root), 'a failed render changed a file')
            leftovers = glob.glob(os.path.join(root, '.staging-*'))
            self.assertEqual(leftovers, [], 'a staging folder was left behind')
            return result

    def test_a_mode_that_fails_verification_leaves_every_file_alone(self):
        result = self.assert_untouched(BREAK_VERIFY)
        self.assertIn('nothing was moved', result.stdout)

    def test_a_write_that_dies_partway_leaves_every_file_alone(self):
        self.assert_untouched(BREAK_WRITE)

    def test_other_files_in_mid_are_kept_and_reported(self):
        """Only our own names are replaced; dois_eleven once emptied the folder."""
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.rendered_copy(tmp)
            foreign = Path(root) / 'mid' / 'my_own_take.mid'
            foreign.write_bytes(b'not a real midi file, and not ours to touch')
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(foreign.read_bytes(),
                             b'not a real midi file, and not ours to touch')
            self.assertIn('my_own_take.mid', result.stdout)
            self.assertIn('13 file(s) moved into place, every one verified: 1 into mid/, '
                          '8 into wavetables/, 4 into presets/', result.stdout)

    def test_an_emptied_staging_folder_left_by_a_sync_service_is_cleared(self):
        """iCloud put an empty staging skeleton back twice (2026-10-20). The next render
        removes one with no files in it, and leaves one that holds a file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            empty = Path(root) / '.staging-left'
            for kind in ('mid', 'wavetables', 'presets'):
                (empty / kind).mkdir(parents=True)
            holding = Path(root) / '.staging-holding'
            (holding / 'mid').mkdir(parents=True)
            (holding / 'mid' / 'something.mid').write_bytes(b'not provably ours')
            self.assertEqual(run(root).returncode, 0)
            self.assertFalse(empty.exists())
            self.assertEqual((holding / 'mid' / 'something.mid').read_bytes(), b'not provably ours')


if __name__ == '__main__':
    unittest.main()
