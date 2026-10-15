"""eight_five: dois_44's engine with D on a quintuplet eighth — 8 against 5.

The engine is dois_44's, unchanged and tested there (110 tests). These tests are about
this piece: that it renders and verifies; that the 8:5 arithmetic comes out as the
README says; that the residues pinned in config.py are what the search derives; and that
the forms hold. Run from this folder: python3 -B -m unittest discover -s tests
"""
import itertools
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mido

PROJECT = Path(__file__).resolve().parents[1]
UNITS = {'A': 120, 'B': 120, 'C': 120, 'D': 192}
PARITY = 38400


def copy(tmp):
    root = Path(tmp) / 'copy'
    shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns('mid', '__pycache__'))
    (root / 'mid').mkdir()
    return root


def run(root, *args):
    return subprocess.run([sys.executable, '-B', 'compose.py', *args], cwd=root,
                          capture_output=True, text=True)


def velocities(path, unit, steps):
    at, t = {}, 0
    for msg in mido.MidiFile(path).tracks[0]:
        t += msg.time
        if msg.type == 'note_on' and msg.velocity:
            at[t // unit] = msg.velocity
    return [at.get(i, 0) for i in range(steps)]


class ThePiece(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = copy(cls.tmp.name)
        cls.result = run(cls.root)
        assert cls.result.returncode == 0, cls.result.stdout[-3000:] + cls.result.stderr

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_it_renders_and_every_set_verifies(self):
        self.assertEqual(self.result.stdout.count('All checks passed'), 3)
        self.assertIn('wavetables verified', self.result.stdout)
        self.assertIn('tuning verified', self.result.stdout)
        self.assertNotIn('FAILED', self.result.stdout)

    def test_eight_against_five(self):
        """4800 and 7680 ticks meet first at 38,400: A, B, C restate 8 times, D 5."""
        out = self.result.stdout
        self.assertIn('D: 40 steps x 192 = 7680 ticks, restated 5x', out)
        self.assertIn('A: 40 steps x 120 = 4800 ticks, restated 8x', out)
        self.assertIn('P = LCM = 38400 ticks', out)
        self.assertEqual([t for t in range(1, PARITY) if t % 4800 == 0 and t % 7680 == 0], [])

    def test_the_span_moduli_are_the_smallest_that_reach_parity(self):
        out = self.result.stdout
        self.assertIn('modulus 64', out)
        self.assertIn('modulus 25', out)
        import math
        self.assertEqual(math.lcm(40, 64), 320)          # 8 passes of 40 sixteenths
        self.assertEqual(math.lcm(40, 25), 200)          # 5 passes of 40 quintuplets
        self.assertEqual([m for m in range(1, 64) if math.lcm(40, m) == 320], [])
        self.assertEqual([m for m in range(1, 25) if math.lcm(40, m) == 200], [])

    def test_every_pass_differs_and_every_voice_reaches_every_state(self):
        for voice, unit in UNITS.items():
            steps = PARITY // unit
            v = velocities(self.root / 'mid' / f'eight_five_static_{voice}_prime.mid',
                           unit, steps)
            passes = [tuple(v[i:i + 40]) for i in range(0, steps, 40)]
            self.assertEqual(len(passes), 8 if voice != 'D' else 5)
            self.assertEqual(len(set(passes)), len(passes), voice)
            weakest = min(sum(a != b for a, b in zip(x, y))
                          for x, y in itertools.combinations(passes, 2))
            self.assertGreaterEqual(weakest, 7, voice)
            self.assertEqual(len({x for x in v if x}), 8, voice)

    def test_the_forms(self):
        for mode in ('lattice', 'canon'):
            mid = mido.MidiFile(self.root / 'mid' / f'eight_five_{mode}_form.mid')
            for track in mid.tracks:
                self.assertEqual(sum(msg.time for msg in track), 40 * PARITY)
        self.assertEqual(self.result.stdout.count('all 40 differ'), 2)

    def test_only_d_has_a_sweep_table(self):
        """A, B and C state themselves over 320 steps, more than Serum's 256 frames."""
        for voice in 'ABC':
            self.assertFalse((self.root / 'mid' / f'eight_five_wavetable_{voice}_sweep.wav').exists())
        self.assertTrue((self.root / 'mid' / 'eight_five_wavetable_D_sweep.wav').exists())


class PinnedResidues(unittest.TestCase):

    def test_the_search_still_derives_what_config_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy(tmp)
            text = (root / 'config.py').read_text()
            pinned = re.search(r'^SPAN_RESIDUES = \{.*?\}\n', text, re.S | re.M).group(0)
            (root / 'config.py').write_text(text.replace(pinned, 'SPAN_RESIDUES = None\n'))
            result = run(root, '--suggest-span')
            self.assertEqual(result.returncode, 0, result.stderr)
            derived = re.search(r'span residues \(derived\): (\{.*?\}) —', result.stdout).group(1)
            sys.path.insert(0, str(PROJECT))
            try:
                import config
                from span import format_residues
                self.assertEqual(derived, format_residues(config.SPAN_RESIDUES))
            finally:
                sys.path.remove(str(PROJECT))
            self.assertIn('local search', result.stdout)        # 64 is too large to try all
            self.assertIn('the best of all 100,000 half-full sets', result.stdout)


if __name__ == '__main__':
    unittest.main()
