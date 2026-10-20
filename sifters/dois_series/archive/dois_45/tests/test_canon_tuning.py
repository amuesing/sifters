"""dois_43: the canon set, the lattice's period as an octave, and held notes.

  * `canon` — each voice reads the lattice at the step its note descends from, so C
    plays A's melody 13 steps later and, where the two meet, a fixed interval (31) where
    `lattice` gave a unison every time;
  * the tuning files — the 40-step period as one octave, root at its usual pitch;
  * ARTICULATION = 'held' — every note held until its voice's next attack;
  * the checker refuses a canon that is not one and a tuning file that is wrong.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_engine import PROJECT, notes, project_copy, rendered, run

UNITS = {'A': 120, 'B': 120, 'C': 120, 'D': 160}


class Rendered(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = project_copy(cls.tmp.name)
        cls.result = run(cls.root)
        assert cls.result.returncode == 0, cls.result.stdout[-3000:] + cls.result.stderr

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def pitches(self, mode, voice):
        (track,) = notes(self.root / 'mid' / f'dois_45_{mode}_{voice}_prime.mid')
        return {onset: pitch for onset, _, pitch, _, _ in track}

    # ---------------------------------------------------------------- the canon set

    def test_c_plays_a_s_melody_thirteen_steps_later(self):
        a, c = self.pitches('canon', 'A'), self.pitches('canon', 'C')
        span = 160
        for onset, pitch in c.items():
            source = ((onset // 120 - 13) % span) * 120
            self.assertEqual(pitch, a[source], onset)

    def test_where_a_and_c_meet_they_never_sound_a_unison(self):
        """In `lattice` all 80 meetings are unisons; in `canon` none is, and all are 31."""
        for mode, expected in (('lattice', {0}), ('canon', {31})):
            a, c = self.pitches(mode, 'A'), self.pitches(mode, 'C')
            shared = set(a) & set(c)
            self.assertEqual(len(shared), 80)
            self.assertEqual({(c[t] - a[t]) % 40 for t in shared}, expected, mode)

    def test_only_the_canon_voice_reads_elsewhere(self):
        for voice in 'ABD':
            self.assertEqual(self.pitches('canon', voice), self.pitches('lattice', voice), voice)
        self.assertNotEqual(self.pitches('canon', 'C'), self.pitches('lattice', 'C'))

    def test_every_canon_pitch_is_on_the_lattice(self):
        for voice in 'ABCD':
            for onset, pitch in self.pitches('canon', voice).items():
                self.assertTrue(36 <= pitch <= 75, (voice, onset))

    # ------------------------------------------------------------------ the tuning

    def tun(self):
        text = (self.root / 'tuning' / 'dois_45_tuning.tun').read_text()
        rounded = dict(map(int, m) for m in re.findall(r'^note (\d+)=(-?\d+)$', text, re.M))
        exact = {int(n): float(v) for n, v in
                 re.findall(r'^note (\d+)=(-?\d+\.\d+)$', text, re.M)}
        return rounded, exact

    def test_the_period_is_an_octave_and_the_root_keeps_its_pitch(self):
        rounded, exact = self.tun()
        self.assertEqual(sorted(rounded), list(range(128)))
        self.assertEqual(sorted(exact), list(range(128)))
        self.assertEqual(rounded[36], 3600)                  # 12-TET C2, 65.41 Hz
        self.assertEqual(rounded[76] - rounded[36], 1200)    # 40 steps: one octave
        for n in range(127):
            self.assertAlmostEqual(exact[n + 1] - exact[n], 30.0, places=6)

    def test_the_lattice_s_moves_land_near_simple_ratios(self):
        """x13 = 390 cents (5/4 is 386), +9 = 270 (7/6, 267), 31 = 930 (12/7, 933)."""
        import math
        rounded, _ = self.tun()
        for steps, ratio in ((13, 5 / 4), (9, 7 / 6), (31, 12 / 7)):
            cents = rounded[36 + steps] - rounded[36]
            self.assertLess(abs(cents - 1200 * math.log2(ratio)), 4, steps)

    def test_scala_files_for_mts_esp(self):
        scl = [x.strip() for x in (self.root / 'tuning' / 'dois_45_tuning.scl').read_text()
               .splitlines() if not x.startswith('!')]
        self.assertEqual(int(scl[1]), 40)
        self.assertEqual(scl[2:][-1], '2/1')
        self.assertEqual([float(x) for x in scl[2:-1]], [30.0 * k for k in range(1, 40)])
        kbm = [x.strip() for x in (self.root / 'tuning' / 'dois_45_tuning.kbm').read_text()
               .splitlines() if not x.startswith('!')]
        self.assertEqual(kbm[:5], ['0', '0', '127', '36', '36'])
        self.assertAlmostEqual(float(kbm[5]), 65.406391, places=5)
        self.assertEqual(kbm[6], '40')


class HeldNotes(unittest.TestCase):
    """ARTICULATION = 'held': the sieve's gaps become durations."""

    def test_every_note_lasts_until_its_voice_s_next_attack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            config = root / 'config.py'
            text = config.read_text()
            self.assertIn("ARTICULATION = 'step'", text)
            config.write_text(text.replace("ARTICULATION = 'step'", "ARTICULATION = 'held'"))
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertNotIn('FAILED', result.stdout)
            for voice, unit in UNITS.items():
                (track,) = notes(root / 'mid' / f'dois_45_static_{voice}_prime.mid')
                onsets = [o for o, *_ in track]
                ends = onsets[1:] + [19200]
                for (onset, length, *_), end in zip(track, ends):
                    self.assertEqual(onset + length, end, (voice, onset))
            # B's gaps are 2 to 6 steps; its last note stops where its one-statement file
            # ends, so it is judged by the rule above, not by this set.
            (b,) = notes(root / 'mid' / 'dois_45_static_B_prime.mid')
            self.assertEqual({length // 120 for _, length, *_ in b[:-1]}, {2, 3, 4, 5, 6})

    def test_the_default_is_still_one_step(self):
        sys.path.insert(0, str(PROJECT))
        try:
            import config
            self.assertEqual(config.ARTICULATION, 'step')
            self.assertEqual(config.GATE_RATIO, 1.0)
        finally:
            sys.path.remove(str(PROJECT))


class TheCheckerIsNotFooled(unittest.TestCase):

    SCRIPT = """
import sys, io, contextlib
import compose, pitch, tuning
mode = sys.argv[1]
if mode == 'canon':
    compose.MODES['canon'] = (pitch.lattice_notes, pitch.check_canon)   # no imitation
elif mode == 'tuning':
    real = tuning.tun_text
    tuning.tun_text = lambda title: real(title).replace('note 40=3720', 'note 40=3721', 1)
    compose.write_tuning.__globals__['tun_text'] = tuning.tun_text
out = io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        compose.main()
except SystemExit as stop:
    assert stop.code and 'FAILED' in out.getvalue(), out.getvalue()[-2000:]
    print('REFUSED'); sys.exit(0)
sys.exit('a broken render passed verification')
"""

    def refuse(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'copy'
            shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns('mid', 'wavetables', 'tuning', '__pycache__'))
            result = subprocess.run([sys.executable, '-B', '-c', self.SCRIPT, mode],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertEqual(rendered(root), {})

    def test_a_canon_set_that_is_not_a_canon_is_caught(self):
        self.refuse('canon')

    def test_a_mistuned_note_is_caught(self):
        self.refuse('tuning')


if __name__ == '__main__':
    unittest.main()
