"""Regression tests for dois_20: static pitch, and everything else unchanged.

Every render goes into a temporary directory; nothing here touches dois_20/mid.
Run from dois_20:  python3 -B -m unittest discover -s tests -v
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mido

PROJECT = Path(__file__).resolve().parents[1]
PARENT = PROJECT.parent / 'dois_18' / 'mid'          # the version this pares down
FILES = ('A_prime', 'B_prime', 'C_prime', 'D_prime', 'arrangement', 'ensemble')
PITCH = {'A': 36, 'B': 37, 'C': 38, 'D': 39}


def render(out, setup=''):
    script = f"import composition as c\nc.OUTPUT_DIR = {str(out)!r}\n{setup}\nc.main()\n"
    return subprocess.run([sys.executable, '-B', '-c', script], cwd=PROJECT,
                          capture_output=True, text=True)


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


class Dois20(unittest.TestCase):

    def test_rhythm_and_velocity_are_exactly_dois_18(self):
        """Only the pitch of each note may differ from the version this pares down."""
        with tempfile.TemporaryDirectory() as tmp:
            result = render(tmp)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            for f in FILES:
                fresh = notes(Path(tmp) / f'dois_20_{f}.mid')
                prior = notes(PARENT / f'dois_18_{f}.mid')
                self.assertEqual([[(o, d, v, c) for o, d, _, v, c in tr] for tr in fresh],
                                 [[(o, d, v, c) for o, d, _, v, c in tr] for tr in prior], f)

    def test_each_voice_sounds_one_static_pitch(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(render(tmp).returncode, 0)
            for voice, pitch in PITCH.items():
                (track,) = notes(Path(tmp) / f'dois_20_{voice}_prime.mid')
                self.assertEqual({p for _, _, p, _, _ in track}, {pitch}, voice)

    def test_one_weather_voices_on_a_grid_agree(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = render(tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            at = {v: {o // 120: vel for o, _, _, vel, _ in
                      notes(Path(tmp) / f'dois_20_{v}_prime.mid')[0]} for v in 'ABC'}
            for one, other, expected in (('A', 'C', 80), ('B', 'C', 28)):
                shared = set(at[one]) & set(at[other])
                self.assertEqual(len(shared), expected)
                self.assertEqual([t for t in shared if at[one][t] != at[other][t]], [])

    def test_bad_pitch_config_leaves_previous_files_untouched(self):
        cases = [("c.INSTRUMENT_CONFIGS[0]['pitch'] = 36.5", 'whole number'),
                 ("c.INSTRUMENT_CONFIGS[0]['pitch'] = 200", 'whole number'),
                 ("c.INSTRUMENT_CONFIGS[0]['pitch'] = True", 'whole number'),
                 ("c.INSTRUMENT_CONFIGS[1]['pitch'] = 36", 'share a pitch')]
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(render(tmp).returncode, 0)
            before = {p.name: p.read_bytes() for p in Path(tmp).iterdir()}
            self.assertEqual(len(before), 6)
            for setup, message in cases:
                with self.subTest(setup=setup):
                    result = render(tmp, setup)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertEqual(before, {p.name: p.read_bytes()
                                              for p in Path(tmp).iterdir()})

    def test_c_on_a_different_grid_still_renders(self):
        """The dois_16 canon crash must stay fixed even with no pitch canon to report."""
        with tempfile.TemporaryDirectory() as tmp:
            result = render(tmp, "c.INSTRUMENT_CONFIGS[2]['step_ticks'] = 160")
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            (track,) = notes(Path(tmp) / 'dois_20_C_prime.mid')
            self.assertEqual(len(track), 81)


if __name__ == '__main__':
    unittest.main()
