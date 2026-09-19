"""Regression tests for the two dois_16 bugs fixed in dois_17 (both found by GPT).

Every render goes into a temporary directory; nothing here touches dois_17/mid.
Run from dois_17:  python3 -B -m unittest discover -s tests -v
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mido

PROJECT = Path(__file__).resolve().parents[1]
DOIS_16 = PROJECT.parent / 'dois_16' / 'mid'
FILES = ('A_prime', 'B_prime', 'C_prime', 'D_prime', 'arrangement', 'ensemble')


def render(out, setup=''):
    """Run composition.main() into `out`, after `setup` lines applied to the module."""
    script = f"import composition as c\nc.OUTPUT_DIR = {str(out)!r}\n{setup}\nc.main()\n"
    return subprocess.run([sys.executable, '-B', '-c', script], cwd=PROJECT,
                          capture_output=True, text=True)


def notes(path):
    """Per track: sorted (onset, length, pitch, velocity, channel)."""
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


class Dois17(unittest.TestCase):

    def test_default_render_matches_dois_16_note_for_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = render(tmp)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            for f in FILES:
                self.assertEqual(notes(Path(tmp) / f'dois_17_{f}.mid'),
                                 notes(DOIS_16 / f'dois_16_{f}.mid'), f)

    def test_bug1_canon_across_different_grids(self):
        """dois_16: C on 160 ticks raised KeyError: 15 after writing."""
        with tempfile.TemporaryDirectory() as tmp:
            result = render(tmp, "c.INSTRUMENT_CONFIGS[2]['step_ticks'] = 160")
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assertIn('(120- and 160-tick grids): +9 mod 40 (exact, as predicted); '
                          'heard +9 x23, -31 x4', result.stdout)
            (c_notes,) = notes(Path(tmp) / 'dois_17_C_prime.mid')
            self.assertEqual(len(c_notes), 81)
            self.assertTrue(all(onset % 160 == 0 for onset, *_ in c_notes))

    def test_bug1_misaligned_canon_is_a_failure_not_a_crash(self):
        """Damage C's file as verify() reads it: the check must report, not raise."""
        drop_first_c_note = (
            "real = c.read_track\n"
            "def damaged(path, *a, **k):\n"
            "    got, hanging, overlaps = real(path, *a, **k)\n"
            "    if path.endswith('_C_prime.mid'):\n"
            "        got = got[1:]\n"
            "    return got, hanging, overlaps\n"
            "c.read_track = damaged\n")
        with tempfile.TemporaryDirectory() as tmp:
            result = render(tmp, drop_first_c_note)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Traceback', result.stderr)
            self.assertIn('canon on A does not line up', result.stdout)

    def test_bug2_bad_pitch_types_leave_previous_files_untouched(self):
        """dois_16: PITCH_ROOT = 36.5 replaced all six files, then failed."""
        cases = [('PITCH_ROOT', 36.5), ('PITCH_ROOT', True),
                 ('PITCH_ROW_INTERVAL', 5.0), ('PITCH_COL_INTERVAL', False)]
        with tempfile.TemporaryDirectory() as tmp:
            first = render(tmp)                      # real previous files, not decoys
            self.assertEqual(first.returncode, 0, first.stderr)
            before = {p.name: p.read_bytes() for p in Path(tmp).iterdir()}
            self.assertEqual(len(before), 6)
            for name, value in cases:
                with self.subTest(name=name, value=value):
                    result = render(tmp, f"c.{name} = {value!r}")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f'{name} must be a whole number', result.stderr)
                    after = {p.name: p.read_bytes() for p in Path(tmp).iterdir()}
                    self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
