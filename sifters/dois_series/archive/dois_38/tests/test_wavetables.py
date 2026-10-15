"""Serum wavetables, as reworked in dois_38.

Per voice, two tables:
  * `_velocity.wav` — 128 frames, one per MIDI velocity, each sounding the accent state
    whose velocity is nearest, so velocity v lands on frame v;
  * `_sweep.wav` — the voice's whole parity statement, one frame per step, closing on
    its first step.

What has to be true, and is tested here:
  * Serum 2's own file format and marker, so it imports without asking;
  * exactly ONE PERIOD of the sieve as harmonics: harmonic h sounds iff h is in the
    voice's sieve, h = 1 .. period, fundamental always — nothing above;
  * velocity bands and the sweep follow the accent states the MIDI uses;
  * identical phases in every frame;
  * the checker refuses a wavetable broken in any of those ways.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from test_dois38 import PROJECT, notes, project_copy, run

FRAME = 2048
MARKER = '<!>2048 11000000 wavetable (www.xferrecords.com)'


def read(path):
    """A third reader, separate from both the writer and the checker."""
    import struct
    blob = Path(path).read_bytes()
    chunks, at = {}, 12
    while at + 8 <= len(blob):
        tag, size = blob[at:at + 4], struct.unpack('<I', blob[at + 4:at + 8])[0]
        chunks[tag] = blob[at + 8:at + 8 + size]
        at += 8 + size + size % 2
    return chunks, np.frombuffer(chunks[b'data'], dtype='<f4')


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
            base[cfg['name']] = binary
        cls.base = base
        sys.path.remove(str(PROJECT))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def table(self, voice, kind):
        chunks, audio = read(self.root / 'mid' / f'dois_38_wavetable_{voice}_{kind}.wav')
        return chunks, audio.reshape(-1, FRAME)

    @staticmethod
    def harmonics(frame, upto=60):
        spectrum = np.abs(np.fft.rfft(frame))[1:upto + 1]
        return spectrum / spectrum.max()

    def test_serum_2_format_and_marker(self):
        """Exactly as Serum 2's own factory tables: format 3, mono, 32-bit, 'clm '."""
        import struct
        for voice in 'ABCD':
            for kind in ('velocity', 'sweep'):
                chunks, _ = self.table(voice, kind)
                tag, channels = struct.unpack('<HH', chunks[b'fmt '][:4])
                bits = struct.unpack('<H', chunks[b'fmt '][14:16])[0]
                self.assertEqual((tag, channels, bits), (3, 1, 32), (voice, kind))
                self.assertEqual(chunks[b'clm '].rstrip(b'\0').decode(), MARKER)

    def test_one_period_of_the_sieve_as_harmonics(self):
        """h sounds iff h is in the sieve, for h = 1..40; the fundamental always; no more."""
        for voice in 'ABCD':
            _, frames = self.table(voice, 'velocity')
            sounding = self.harmonics(frames[1], upto=60) > 1e-4
            expected = [bool(self.base[voice][h % 40]) for h in range(1, 41)]
            expected[0] = True
            self.assertEqual(list(sounding[:40]), expected, voice)
            self.assertFalse(sounding[40:].any(), f'{voice} sounds above one period')

    def test_a_and_b_split_the_period_between_them(self):
        a = self.harmonics(self.table('A', 'velocity')[1][1], 40) > 1e-4
        b = self.harmonics(self.table('B', 'velocity')[1][1], 40) > 1e-4
        self.assertTrue((a | b).all(), 'every harmonic of the period sounds in A or B')
        shared = list(np.nonzero(a & b)[0] + 1)
        self.assertEqual(shared, [1] if not self.base['B'][1] else [],
                         'only the forced fundamental may sound in both')

    def test_velocity_bands_hold_eight_timbres(self):
        for voice in 'ABCD':
            _, frames = self.table(voice, 'velocity')
            self.assertEqual(len(frames), 128)
            distinct = {tuple(np.round(self.harmonics(f, 40), 4)) for f in frames}
            self.assertEqual(len(distinct), 8, voice)
            # each velocity level of the MIDI sits in the middle of its own band
            for level in (1, 19, 37, 55, 73, 91, 109, 127):
                lo, hi = max(0, level - 8), min(127, level + 8)
                np.testing.assert_allclose(frames[lo], frames[level], atol=1e-6)
                np.testing.assert_allclose(frames[hi], frames[level], atol=1e-6)

    def test_the_sweep_is_the_parity_statement_closing_on_itself(self):
        for voice, steps in (('A', 160), ('B', 160), ('C', 160), ('D', 120)):
            _, frames = self.table(voice, 'sweep')
            self.assertEqual(len(frames), steps + 1, voice)
            np.testing.assert_allclose(frames[-1], frames[0], atol=1e-6)

    def test_every_frame_shares_its_phases(self):
        for voice in 'ABCD':
            _, frames = self.table(voice, 'sweep')
            spectra = np.fft.rfft(frames, axis=1)[:, 1:41]
            loud = np.abs(spectra) > 1e-3 * np.abs(spectra).max()
            drift = np.angle(spectra * np.conj(spectra[0]))
            self.assertLess(np.abs(drift[loud]).max(), 1e-3, voice)

    def test_the_midi_did_not_change(self):
        expected = json.loads((PROJECT / 'tests/fixtures/dois_35_notes.json').read_text())
        actual = {p.name.removeprefix('dois_38_'): notes(p)
                  for p in (self.root / 'mid').glob('*.mid')}
        self.assertEqual(json.loads(json.dumps(actual)), expected)


class TheCheckerIsNotFooled(unittest.TestCase):
    """Break a table four ways; each must refuse the run with nothing reaching mid/."""

    SCRIPT = """
import sys, io, contextlib
import numpy as np
import compose, wavetable, config
mode = sys.argv[1]
if mode == 'marker':
    wavetable.serum_marker = lambda: '<!>2048 00000000 wavetable (sifters)'
elif mode == 'band':
    real = wavetable.velocity_frames
    def broken(state_frame, levels):
        frames = real(state_frame, levels)
        frames[55], frames[91] = frames[91], frames[55]     # two velocities swapped
        return frames
    wavetable.velocity_frames = broken
elif mode == 'period':
    real = wavetable.spectrum
    wavetable.spectrum = lambda *a: np.concatenate([real(*a), [0.01]])   # harmonic 41
elif mode == 'phase':
    real = wavetable.synthesise
    calls = []
    def shifted(amplitudes):
        calls.append(1)
        if len(calls) == 3:
            wavetable.phases = lambda n: np.full(n, 0.5)
        return real(amplitudes)
    wavetable.synthesise = shifted
out = io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        compose.main()
except SystemExit as stop:
    text = out.getvalue()
    assert stop.code and 'wavetables FAILED' in text, text[-2000:]
    print('REFUSED'); sys.exit(0)
sys.exit('a broken wavetable passed verification')
"""

    def refuse(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'copy'
            shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns('mid', '__pycache__'))
            result = subprocess.run([sys.executable, '-B', '-c', self.SCRIPT, mode],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertEqual(list((root / 'mid').glob('*.wav')), [])

    def test_the_wrong_marker_is_caught(self):
        self.refuse('marker')

    def test_velocities_in_the_wrong_band_are_caught(self):
        self.refuse('band')

    def test_more_than_one_period_is_caught(self):
        self.refuse('period')

    def test_frames_with_different_phases_are_caught(self):
        self.refuse('phase')


class Choices(unittest.TestCase):

    def test_emphasis_zero_makes_every_frame_the_plain_sieve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            text = (root / 'config.py').read_text().replace(
                'WAVETABLE_EMPHASIS = 3.0', 'WAVETABLE_EMPHASIS = 0.0')
            (root / 'config.py').write_text(text)
            self.assertEqual(run(root).returncode, 0)
            _, audio = read(root / 'mid' / 'dois_38_wavetable_A_velocity.wav')
            frames = audio.reshape(-1, FRAME)
            for frame in frames[1:]:
                np.testing.assert_allclose(frame, frames[0], atol=1e-6)


if __name__ == '__main__':
    unittest.main()
