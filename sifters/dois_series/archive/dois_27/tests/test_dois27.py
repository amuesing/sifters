"""Tests for dois_27: two pitch modes from one rhythm, and not tied to one sieve.

Two contracts:
  1. `static` is note-for-note the drumrack version, dois_23;
  2. `lattice` shares its rhythm and velocities exactly — only pitch differs;
  2. a DIFFERENT sieve works. Each such test copies the project to a temporary folder,
     edits config.py there and runs it, which is exactly what you would do yourself.

Nothing here touches dois_27/mid.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mido

PROJECT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((PROJECT / 'tests/fixtures/dois_23_baseline.json').read_text())
FILES = ('A_prime', 'B_prime', 'C_prime', 'D_prime', 'arrangement', 'ensemble')
PSAPPHA = "'(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))'"
WEATHER = re.compile(r"WEATHER = \{.*?\n\}", re.S)


def notes(path):
    tracks = []
    for track in mido.MidiFile(path).tracks:
        t, sounding, out = 0, {}, []
        for msg in track:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                sounding[(msg.channel, msg.note)] = (t, msg.velocity)
            elif msg.type in ('note_on', 'note_off') and (msg.channel, msg.note) in sounding:
                onset, vel = sounding.pop((msg.channel, msg.note))
                out.append((onset, t - onset, msg.note, vel, msg.channel))
        tracks.append(sorted(out))
    return tracks


def run(cwd, *args):
    return subprocess.run([sys.executable, '-B', 'compose.py', *args],
                          cwd=cwd, capture_output=True, text=True)


def project_copy(tmp, sieve=None, weather=None, span=None):
    """A working copy of the project with config.py edited, as a user would edit it."""
    root = Path(tmp) / 'copy'
    shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns('mid', '__pycache__'))
    (root / 'mid').mkdir()
    text = (root / 'config.py').read_text()
    if sieve:
        start = text.index(PSAPPHA)
        end = text.index("',\n", text.index("'|8@3", start)) + 1
        text = text[:start] + repr(sieve) + text[end:]
    if weather:
        text = WEATHER.sub('WEATHER = ' + repr(weather), text, count=1)
    if span:
        text = re.sub(r'SPAN_RESIDUE_SOURCE = \([^)]*\)',
                      f'SPAN_RESIDUE_SOURCE = {span!r}', text, count=1)
    (root / 'config.py').write_text(text)
    return root


class SameResult(unittest.TestCase):

    def test_static_mode_keeps_the_drumrack_rhythm_and_pitches(self):
        """Velocity now comes from the derived weather, so only notes are compared."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            for f in FILES:
                fresh = notes(root / 'mid' / f'dois_27_static_{f}.mid')
                prior = [[tuple(n) for n in tr] for tr in BASELINE[f]['tracks']]
                self.assertEqual([[(o, d, p, c) for o, d, p, _, c in tr] for tr in fresh],
                                 [[(o, d, p, c) for o, d, p, _, c in tr] for tr in prior], f)

    def test_the_weather_is_derived_from_the_sieve(self):
        """One accent per modulus, on the residues the sieve favours."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Weather (derived from the sieve): '
                          'mod8 = 8@1|8@3|8@4|8@6, mod5 = 5@1|5@3', result.stdout)
            # mod-5 comes out as the hand-written accent of every earlier version
            self.assertIn('span residues (derived)', result.stdout)
            self.assertIn('all 8 accent states reached', result.stdout)

    def test_three_different_sieves_derive_everything(self):
        """Nothing hand-written: each sieve finds its own weather, residues and meter."""
        cases = [('(7@0|7@1|7@3)&(5@0|5@2|5@3)|7@5|5@1', 'mod7 = 7@0|7@1|7@5', '35/16'),
                 ('(11@0|11@2|11@5|11@7)&(3@1|3@2)|11@9', 'mod11 = ', '33/16')]
        for sieve, weather, meter in cases:
            with self.subTest(sieve=sieve), tempfile.TemporaryDirectory() as tmp:
                root = project_copy(tmp, sieve=sieve)
                result = run(root)
                self.assertEqual(result.returncode, 0, result.stdout[-1500:] + result.stderr)
                self.assertIn(weather, result.stdout)
                self.assertIn(meter, result.stdout)
                self.assertIn('all 8 accent states reached', result.stdout)
                self.assertEqual(len(list((root / 'mid').glob('*.mid'))), 12)

    def test_lattice_shares_the_rhythm_and_velocities_of_static(self):
        """Only pitch may differ between modes; the sieve's rhythm is one thing."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            for f in FILES:
                a = notes(root / 'mid' / f'dois_27_static_{f}.mid')
                b = notes(root / 'mid' / f'dois_27_lattice_{f}.mid')
                self.assertEqual([[(o, d, v, c) for o, d, _, v, c in tr] for tr in a],
                                 [[(o, d, v, c) for o, d, _, v, c in tr] for tr in b], f)

    def test_lattice_pitches_and_canon(self):
        """Every note on the grid, and the canon a transposition of +9 MODULO 40."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            at = {}
            for voice in 'ABCD':
                (track,) = notes(root / 'mid' / f'dois_27_lattice_{voice}_prime.mid')
                unit = 160 if voice == 'D' else 120
                at[voice] = {o // unit: p for o, _, p, _, _ in track}
                for step, pitch in at[voice].items():
                    self.assertEqual(pitch, 36 + (13 * step) % 40, (voice, step))
            moves = [at['C'][(i + 13) % 160] - at['A'][i] for i in at['A']]
            self.assertEqual({m % 40 for m in moves}, {9})        # exact, modulo 40
            self.assertEqual(sorted(set(moves)), [-31, 9])        # not a heard constant

    def test_each_voice_sounds_one_static_pitch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            for voice, pitch in (('A', 36), ('B', 37), ('C', 38), ('D', 39)):
                (track,) = notes(root / 'mid' / f'dois_27_static_{voice}_prime.mid')
                self.assertEqual({p for _, _, p, _, _ in track}, {pitch})


class AnotherSieve(unittest.TestCase):

    def test_a_different_sieve_renders_and_verifies(self):
        """Moduli 7 and 5 instead of 8 and 5: different period, parity and meter."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp,
                                sieve='(7@0|7@1|7@3)&(5@0|5@2|5@3)|7@5|5@1',
                                weather={'w5': '5@0|5@2|5@3', 'w7': '7@0|7@1|7@3'})
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout[-2500:] + result.stderr)
            self.assertIn('All checks passed', result.stdout)
            self.assertIn('P = LCM = 16800', result.stdout)      # its own parity
            self.assertIn('35/16', result.stdout)                # its own meter
            self.assertEqual(len(list((root / 'mid').glob('*.mid'))), 12)

    def test_a_sieve_the_span_accent_cannot_inflect_is_refused(self):
        """Nothing may be written when passes would come out identical."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, sieve='(4@0|4@1)&3@1|4@2',
                                weather={'w3': '3@0', 'w4': '4@1|4@2'})
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('no span-accent residues', result.stderr)
            self.assertIn('Principle IV', result.stderr)
            self.assertEqual(list((root / 'mid').glob('*.mid')), [])

    def test_a_mode_that_cannot_render_stops_before_anything_is_written(self):
        """All pitch modes are checked before any of them writes.

        dois_24 rendered them in turn, so a mode that could not render left the
        earlier modes' files already replaced and died on an exception.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            before = {p.name: p.read_bytes() for p in (root / 'mid').iterdir()}
            self.assertEqual(len(before), 12)
            # three moduli: the rhythm is fine, but the lattice needs exactly two
            text = (root / 'config.py').read_text()
            start = text.index(PSAPPHA)
            end = text.index("',\n", text.index("'|8@3", start)) + 1
            (root / 'config.py').write_text(
                text[:start] + repr('(8@0|8@1)&(5@1|5@3)|3@0') + text[end:])
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('exactly two coprime moduli', result.stderr)
            self.assertNotIn('Saved', result.stdout)
            self.assertEqual(before,
                             {p.name: p.read_bytes() for p in (root / 'mid').iterdir()})

    def test_suggest_span_reports_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root, '--suggest-span')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('every pass distinct', result.stdout)
            self.assertEqual(list((root / 'mid').glob('*.mid')), [])


if __name__ == '__main__':
    unittest.main()
