"""eight_five, a second piece on the same engine: D on a quintuplet eighth, 8 against 5.

The piece is pieces/eight_five.py laid over config.py. These tests are about the piece:
that it renders and verifies into an eight_five/ folder inside each output folder; that the 8:5 arithmetic comes out as
its settings say; that the residues it pins are what the search derives; and that the
forms hold. They also check that loading a piece leaves config.py's piece alone.
"""
import importlib.util
import itertools
import sys
import math
import re
import tempfile
import unittest

import mido

from test_engine import PROJECT, project_copy, run

UNITS = {'A': 120, 'B': 120, 'C': 120, 'D': 192}
PARITY = 38400


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
        cls.root = project_copy(cls.tmp.name)
        cls.result = run(cls.root, '--piece', 'eight_five')
        assert cls.result.returncode == 0, cls.result.stdout[-3000:] + cls.result.stderr
        cls.out = cls.root / 'mid' / 'eight_five'
        cls.tables = cls.root / 'wavetables' / 'eight_five'

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_it_renders_and_every_set_verifies(self):
        self.assertIn("Piece 'eight_five'", self.result.stdout)
        self.assertEqual(self.result.stdout.count('All checks passed'), 3)
        self.assertIn('wavetables verified', self.result.stdout)
        self.assertIn('tuning verified', self.result.stdout)
        self.assertNotIn('FAILED', self.result.stdout)

    def test_its_files_go_to_their_own_folders(self):
        self.assertEqual(len(list(self.out.glob('eight_five_*.mid'))), 20)
        self.assertEqual(len(list(self.tables.glob('eight_five_*'))), 18)   # 9 tables + sidecars
        self.assertEqual(len(list((self.root / 'presets' / 'eight_five').glob('*.SerumPreset'))), 32)
        self.assertEqual(len(list((self.root / 'tuning' / 'eight_five').glob('eight_five_*'))), 3)
        for kind in ('mid', 'wavetables', 'tuning', 'presets'):
            self.assertEqual([p for p in (self.root / kind).glob('*') if p.is_file()], [], kind)

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
        self.assertEqual(math.lcm(40, 64), 320)          # 8 passes of 40 sixteenths
        self.assertEqual(math.lcm(40, 25), 200)          # 5 passes of 40 quintuplets
        self.assertEqual([m for m in range(1, 64) if math.lcm(40, m) == 320], [])
        self.assertEqual([m for m in range(1, 25) if math.lcm(40, m) == 200], [])

    def test_every_pass_differs_and_every_voice_reaches_every_state(self):
        for voice, unit in UNITS.items():
            steps = PARITY // unit
            v = velocities(self.out / f'eight_five_static_{voice}_prime.mid', unit, steps)
            passes = [tuple(v[i:i + 40]) for i in range(0, steps, 40)]
            self.assertEqual(len(passes), 8 if voice != 'D' else 5)
            self.assertEqual(len(set(passes)), len(passes), voice)
            weakest = min(sum(a != b for a, b in zip(x, y))
                          for x, y in itertools.combinations(passes, 2))
            self.assertGreaterEqual(weakest, 7, voice)
            self.assertEqual(len({x for x in v if x}), 8, voice)

    def test_the_forms(self):
        for mode in ('lattice', 'canon'):
            mid = mido.MidiFile(self.out / f'eight_five_{mode}_form.mid')
            for track in mid.tracks:
                self.assertEqual(sum(msg.time for msg in track), 40 * PARITY)
        self.assertEqual(self.result.stdout.count('all 40 differ'), 2)

    def test_only_d_has_a_sweep_table(self):
        """A, B and C state themselves over 320 steps, more than Serum's 256 frames."""
        for voice in 'ABC':
            self.assertFalse((self.tables / f'eight_five_wavetable_{voice}_sweep.wav').exists())
        self.assertTrue((self.tables / 'eight_five_wavetable_D_sweep.wav').exists())

    def test_ds_drum_is_re_derived_for_its_grid(self):
        """D strikes 2.5 times a second at 8:5: its drum is 80 Hz, ringing 400 ms."""
        sys.path.insert(0, str(PROJECT))
        try:
            import check
            _, patch = check.read_preset(self.root / 'presets' / 'eight_five' / 'dois_46 eight_five kit D accents.SerumPreset')
        finally:
            sys.path.remove(str(PROJECT))
        p = patch['Oscillator0']['plainParams']
        hz = 8.175798915643707 * 2 ** (p['kParamOctave'] + (p['kParamCoarsePit'] + p['kParamFine'] / 100) / 12)
        self.assertAlmostEqual(hz, 80.0, delta=0.05)
        self.assertAlmostEqual(patch['Env0']['plainParams']['kParamDecay'], 0.4, places=9)
        # labelled with the version, so another version's eight_five never shares its folder
        self.assertEqual(patch['Oscillator0']['WTOsc0']['relativePathToWT'], 'sifters/dois_46 eight_five/D.wav')

    def test_an_unknown_piece_is_refused(self):
        result = run(self.root, '--piece', 'no_such_piece')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no piece 'no_such_piece'", result.stderr)


class PinnedResidues(unittest.TestCase):

    def test_the_search_still_derives_what_the_piece_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            piece = root / 'pieces' / 'eight_five.py'
            text = piece.read_text()
            pinned = re.search(r'^SPAN_RESIDUES = \{.*?\}\n', text, re.S | re.M).group(0)
            piece.write_text(text.replace(pinned, 'SPAN_RESIDUES = None\n'))
            result = run(root, '--piece', 'eight_five', '--suggest-span')
            self.assertEqual(result.returncode, 0, result.stderr)
            derived = re.search(r'span residues \(derived\): (\{.*?\}) —', result.stdout).group(1)
            self.assertIn('local search', result.stdout)        # 64 is too large to try all
            self.assertIn('the best of all 100,000 half-full sets', result.stdout)

        spec = importlib.util.spec_from_file_location(
            'eight_five_settings', PROJECT / 'pieces' / 'eight_five.py')
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        import sys
        sys.path.insert(0, str(PROJECT))
        try:
            from span import format_residues
            self.assertEqual(derived, format_residues(settings.SPAN_RESIDUES))
        finally:
            sys.path.remove(str(PROJECT))


if __name__ == '__main__':
    unittest.main()
