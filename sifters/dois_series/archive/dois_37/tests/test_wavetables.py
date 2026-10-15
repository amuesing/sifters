"""Serum wavetables (dois_37): one frame per accent state, in velocity order.

What has to be true for "route velocity to wavetable position" to mean anything:

  * one file per voice, eight frames of 2048 samples, with Serum's frame-size marker;
  * frame k belongs to the state whose velocity is the k-th level, so the velocity a
    note carries in the MIDI is the frame it selects;
  * each frame's harmonics are the voice's own rhythm, with the accents firing in that
    state lifting the harmonics they mark;
  * the checker catches it when any of that is broken — tested by breaking it.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from test_dois37 import PROJECT, notes, project_copy, run

FRAME = 2048


class Rendered(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = project_copy(cls.tmp.name)
        cls.result = run(cls.root)
        assert cls.result.returncode == 0, cls.result.stdout[-3000:] + cls.result.stderr
        sys.path.insert(0, str(cls.root))
        from wavetable import read_wav
        cls.read_wav = staticmethod(read_wav)

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(str(cls.root))
        cls.tmp.cleanup()

    def frames(self, voice):
        audio, meta = self.read_wav(self.root / 'mid' / f'dois_37_wavetable_{voice}.wav')
        return audio.reshape(-1, FRAME), meta

    def harmonics(self, frame, count=40):
        spectrum = np.abs(np.fft.rfft(frame))[1:count + 1]
        return spectrum / spectrum.max()

    def test_one_file_per_voice_eight_frames_with_the_marker(self):
        for voice in 'ABCD':
            frames, meta = self.frames(voice)
            self.assertEqual(frames.shape, (8, FRAME), voice)
            self.assertEqual((meta['channels'], meta['bits']), (1, 24), voice)
            self.assertTrue(meta['marker'].startswith('<!>2048'), meta['marker'])

    def test_every_frame_is_different(self):
        for voice in 'ABCD':
            frames, _ = self.frames(voice)
            spectra = [tuple(np.round(self.harmonics(f), 3)) for f in frames]
            self.assertEqual(len(set(spectra)), 8, f'{voice} repeats a frame')

    def test_the_spectrum_is_the_rhythm(self):
        """A rest is a missing harmonic; the fundamental always sounds."""
        sys.path.insert(0, str(PROJECT))
        import config
        from sieve import build_binary
        base = {}
        for cfg in config.INSTRUMENT_CONFIGS:
            binary, _ = build_binary(cfg, base)
            base[cfg['name']] = binary
        for voice in 'ABCD':
            frames, _ = self.frames(voice)
            present = self.harmonics(frames[0]) > 1e-3
            expected = base[voice].astype(bool).copy()
            expected[0] = True
            self.assertEqual(list(present), list(expected), voice)

    def test_a_and_b_are_complementary_timbres(self):
        """Complementary rhythms: between them, every harmonic sounds once."""
        a = self.harmonics(self.frames('A')[0][0]) > 1e-3
        b = self.harmonics(self.frames('B')[0][0]) > 1e-3
        both = a & b
        self.assertEqual(list(np.nonzero(both)[0] + 1), [1], 'only the fundamental is shared')
        self.assertTrue((a | b).all())

    def test_the_midi_did_not_change(self):
        import json
        expected = json.loads((PROJECT / 'tests/fixtures/dois_35_notes.json').read_text())
        actual = {p.name.removeprefix('dois_37_'): notes(p)
                  for p in (self.root / 'mid').glob('*.mid')}
        self.assertEqual(json.loads(json.dumps(actual)), expected)


class TheCheckerIsNotFooled(unittest.TestCase):
    """Break a wavetable in two ways and require verification to fail."""

    SCRIPT = """
import sys, io, contextlib
import compose, wavetable
mode = sys.argv[1]
real = wavetable.voice_frames
def broken(field, rhythm, weights, order):
    frames = real(field, rhythm, weights, order)
    if mode == 'swap':
        frames[2], frames[5] = frames[5], frames[2]      # two states out of order
    else:
        frames[4] = frames[4] * 0.0 + frames[3]          # one state lost
    return frames
wavetable.voice_frames = broken
out = io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        compose.main()
except SystemExit as stop:
    text = out.getvalue()
    assert stop.code and 'wavetables FAILED' in text, text[-2000:]
    assert 'wavetable frame' in text, text[-2000:]
    print('REFUSED')
    sys.exit(0)
sys.exit('a broken wavetable passed verification')
"""

    def refuse(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'copy'
            shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns('mid', '__pycache__'))
            result = subprocess.run([sys.executable, '-B', '-c', self.SCRIPT, mode],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertEqual(list((root / 'mid').glob('*.wav')), [],
                             'a failed wavetable must not reach mid/')

    def test_frames_out_of_velocity_order_are_caught(self):
        self.refuse('swap')

    def test_a_missing_state_is_caught(self):
        self.refuse('drop')


class NoEmphasisMeansNoDifference(unittest.TestCase):

    def test_emphasis_zero_makes_every_frame_the_plain_rhythm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            text = (root / 'config.py').read_text().replace(
                'WAVETABLE_EMPHASIS = 3.0', 'WAVETABLE_EMPHASIS = 0.0')
            (root / 'config.py').write_text(text)
            self.assertEqual(run(root).returncode, 0)
            sys.path.insert(0, str(root))
            try:
                from wavetable import read_wav
                audio, _ = read_wav(root / 'mid' / 'dois_37_wavetable_A.wav')
            finally:
                sys.path.remove(str(root))
            frames = audio.reshape(8, FRAME)
            for frame in frames[1:]:
                np.testing.assert_allclose(frame, frames[0], atol=1e-6)


if __name__ == '__main__':
    unittest.main()
