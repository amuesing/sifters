"""The form (from dois_44): the sieve read again, one section per step of its period.

Section s is one parity statement. A voice plays in it exactly when its note layer has an
attack at step s, and it reads the lattice s steps further on, so every section differs.
Tested from the written files: presence, the statement inside each section, the
transposition, that nothing repeats, the length, and that a broken form is refused.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mido

from test_engine import PROJECT, notes, project_copy, run

PARITY = 19200
SECTIONS = 40
UNITS = {'A': 120, 'B': 120, 'C': 120, 'D': 160}


class Rendered(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = project_copy(cls.tmp.name)
        cls.result = run(cls.root)
        assert cls.result.returncode == 0, cls.result.stdout[-3000:] + cls.result.stderr
        sys.path.insert(0, str(PROJECT))
        import config
        from sieve import build_binary
        base = {}
        for cfg in config.INSTRUMENT_CONFIGS:
            binary, _ = build_binary(cfg, base)
            base[cfg['name']] = [int(x) for x in binary]
        cls.base = base
        sys.path.remove(str(PROJECT))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def form(self, mode):
        tracks = notes(self.root / 'mid' / f'dois_45_{mode}_form.mid')
        return dict(zip('ABCD', tracks))

    def sections_played(self, track):
        return sorted({onset // PARITY for onset, *_ in track})

    def test_a_form_for_each_pitched_set_and_none_for_static(self):
        self.assertTrue((self.root / 'mid' / 'dois_45_lattice_form.mid').exists())
        self.assertTrue((self.root / 'mid' / 'dois_45_canon_form.mid').exists())
        self.assertFalse((self.root / 'mid' / 'dois_45_static_form.mid').exists())

    def test_forty_sections_of_one_statement_each(self):
        mid = mido.MidiFile(self.root / 'mid' / 'dois_45_lattice_form.mid')
        for track in mid.tracks:
            self.assertEqual(sum(msg.time for msg in track), SECTIONS * PARITY)

    def test_each_voice_plays_where_its_layer_has_an_attack(self):
        for mode in ('lattice', 'canon'):
            form = self.form(mode)
            for voice, track in form.items():
                wanted = [s for s in range(SECTIONS) if self.base[voice][s]]
                self.assertEqual(self.sections_played(track), wanted, (mode, voice))

    def test_a_and_b_never_share_a_section_and_one_always_plays(self):
        form = self.form('lattice')
        a, b = set(self.sections_played(form['A'])), set(self.sections_played(form['B']))
        self.assertEqual(a & b, set())
        self.assertEqual(a | b, set(range(SECTIONS)))

    def test_each_section_is_the_statement_read_s_steps_on(self):
        """Onsets, lengths and velocities from the statement; pitch 36 + 13(n + s) mod 40."""
        form = self.form('lattice')
        for voice, track in form.items():
            (statement,) = notes(self.root / 'mid' / f'dois_45_lattice_{voice}_prime.mid')
            unit = UNITS[voice]
            for section in self.sections_played(track):
                inside = [(o - section * PARITY, d, p, v) for o, d, p, v, _ in track
                          if o // PARITY == section]
                self.assertEqual([(o, d, v) for o, d, _, v in inside],
                                 [(o, d, v) for o, d, _, v, _ in statement], (voice, section))
                for onset, _, pitch, _ in inside:
                    self.assertEqual(pitch, 36 + (13 * (onset // unit + section)) % 40,
                                     (voice, section, onset))

    def test_no_two_sections_are_alike(self):
        for mode in ('lattice', 'canon'):
            form = self.form(mode)
            signatures = set()
            for section in range(SECTIONS):
                signatures.add(tuple(sorted(
                    (voice, o - section * PARITY, p, v) for voice, track in form.items()
                    for o, _, p, v, _ in track if o // PARITY == section)))
            self.assertEqual(len(signatures), SECTIONS, mode)

    def test_the_canon_form_keeps_the_canon(self):
        """In every section C plays A's melody 13 steps later, as in the canon set."""
        form = self.form('canon')
        a = {o: p for o, _, p, _, _ in form['A']}
        for onset, _, pitch, _, _ in form['C']:
            section, local = divmod(onset, PARITY)
            source = section * PARITY + ((local // 120 - 13) % 160) * 120
            if source in a:
                self.assertEqual(pitch, a[source], onset)


class TheCheckerIsNotFooled(unittest.TestCase):

    SCRIPT = """
import sys, io, contextlib
import compose, form
real = form.notes_for_steps
def untransposed(velocities, note_at):
    # write_form passes `lambda step, s=section: note_at(step + s)`; undo the + s, so
    # every section reads the lattice at step n alone and sections repeat
    section = note_at.__defaults__[0]
    return real(velocities, lambda step: note_at(step - section))
form.notes_for_steps = untransposed
out = io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        compose.main()
except SystemExit as stop:
    text = out.getvalue()
    assert stop.code and 'form FAILED' in text, text[-2000:]
    print('REFUSED'); sys.exit(0)
sys.exit('a form whose sections repeat passed verification')
"""

    def test_a_form_without_its_transposition_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'copy'
            shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns('mid', '__pycache__'))
            result = subprocess.run([sys.executable, '-B', '-c', self.SCRIPT],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertEqual(list((root / 'mid').glob('*')), [])


if __name__ == '__main__':
    unittest.main()
