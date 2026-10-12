"""Serum wavetables, dois_40: a frame for every whole number a note or velocity can be.

The rule: frame i sounds harmonic h, at full strength, if i + h is in the voice's sieve,
for h = 1 .. the sieve's period. What has to be true, and is tested here:

  * Serum 2's file format, a marker with no blending and the factory flag clear;
  * 128 frames, so note number or velocity v lands exactly on frame v;
  * every frame follows the rule exactly — the right harmonics, equal strength, in phase,
    nothing above one period;
  * the variety the design exists for: neighbouring frames always differ, the lattice's
    40 notes reach 40 distinct timbres, the 8 velocity levels reach 8;
  * the voices' relationships carry into timbre: B the complement of A, C A's canon;
  * the sweep follows the velocities the MIDI actually plays;
  * the checker refuses tables broken five ways, with nothing reaching mid/;
  * installation finds Serum's own folder and writes `<project> <version>`, never deeper.
"""
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from test_dois40 import PROJECT, notes, project_copy, run

FRAME = 2048
MARKER = '<!>2048 00000000 wavetable (www.xferrecords.com)'
LATTICE_NOTES = range(36, 76)
VELOCITIES = (1, 19, 37, 55, 73, 91, 109, 127)


def read(path):
    """A third reader, separate from both the writer and the checker."""
    blob = Path(path).read_bytes()
    chunks, at = {}, 12
    while at + 8 <= len(blob):
        tag, size = blob[at:at + 4], struct.unpack('<I', blob[at + 4:at + 8])[0]
        chunks[tag] = blob[at + 8:at + 8 + size]
        at += 8 + size + size % 2
    return chunks, np.frombuffer(chunks[b'data'], dtype='<f4')


def harmonics(frame, upto=60):
    mag = np.abs(np.fft.rfft(frame))
    return {h for h in range(1, upto + 1) if mag[h] > 1e-3 * mag.max()}


class Rendered(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = project_copy(cls.tmp.name)
        result = run(cls.root)
        assert result.returncode == 0, result.stdout[-3000:] + result.stderr
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

    def table(self, voice, sweep=False):
        suffix = '_sweep' if sweep else ''
        chunks, audio = read(self.root / 'mid' / f'dois_40_wavetable_{voice}{suffix}.wav')
        return chunks, audio.reshape(-1, FRAME)

    def rule(self, voice, i):
        sieve = self.base[voice]
        return {h for h in range(1, len(sieve) + 1) if sieve[(i + h) % len(sieve)]}

    def test_format_and_marker(self):
        for voice in 'ABCD':
            for sweep in (False, True):
                chunks, _ = self.table(voice, sweep)
                tag, channels = struct.unpack('<HH', chunks[b'fmt '][:4])
                bits = struct.unpack('<H', chunks[b'fmt '][14:16])[0]
                self.assertEqual((tag, channels, bits), (3, 1, 32))
                marker = chunks[b'clm '].rstrip(b'\0').decode()
                self.assertEqual(marker, MARKER)
                self.assertEqual(marker[8:10], '00', 'no blending, factory flag clear')

    def test_every_frame_follows_the_rule(self):
        """Frame i sounds exactly {h : i + h in the sieve}, at equal strength."""
        for voice in 'ABCD':
            _, frames = self.table(voice)
            self.assertEqual(len(frames), 128)
            for i, frame in enumerate(frames):
                self.assertEqual(harmonics(frame), self.rule(voice, i), (voice, i))
                mag = np.abs(np.fft.rfft(frame))
                present = sorted(self.rule(voice, i))
                np.testing.assert_allclose(mag[present], mag[present].max(), rtol=1e-3)

    def test_neighbouring_frames_always_differ(self):
        for voice in 'ABCD':
            _, frames = self.table(voice)
            for i in range(127):
                self.assertNotEqual(harmonics(frames[i]), harmonics(frames[i + 1]), (voice, i))

    def test_the_table_repeats_with_the_sieve(self):
        """40 distinct timbres, then again: the sieve's period, not duplication."""
        for voice in 'ABCD':
            _, frames = self.table(voice)
            self.assertEqual(len({tuple(sorted(harmonics(f))) for f in frames}), 40)
            np.testing.assert_allclose(frames[5], frames[45], atol=1e-6)

    def test_the_lattice_notes_reach_every_timbre(self):
        for voice in 'ABCD':
            _, frames = self.table(voice)
            self.assertEqual(len({tuple(sorted(harmonics(frames[n]))) for n in LATTICE_NOTES}), 40)

    def test_the_velocity_levels_reach_eight_timbres(self):
        for voice in 'ABCD':
            _, frames = self.table(voice)
            self.assertEqual(len({tuple(sorted(harmonics(frames[v]))) for v in VELOCITIES}), 8)

    def test_b_is_the_complement_of_a_in_timbre(self):
        _, a = self.table('A')
        _, b = self.table('B')
        for i in range(128):
            self.assertEqual(harmonics(a[i]) | harmonics(b[i]), set(range(1, 41)), i)
            self.assertEqual(harmonics(a[i]) & harmonics(b[i]), set(), i)

    def test_c_is_the_canon_of_a_in_timbre(self):
        """C is A shifted 13 steps, so C's frame i is A's frame i - 13."""
        _, a = self.table('A')
        _, c = self.table('C')
        for i in range(13, 128):
            np.testing.assert_allclose(c[i], a[i - 13], atol=1e-6)

    def test_the_sweep_follows_the_velocities_the_midi_plays(self):
        for voice, unit, steps in (('A', 120, 160), ('B', 120, 160), ('C', 120, 160),
                                   ('D', 160, 120)):
            (track,) = notes(self.root / 'mid' / f'dois_40_static_{voice}_prime.mid')
            velocity = [0] * steps
            for onset, _, _, v, _ in track:
                velocity[onset // unit] = v
            _, sweep = self.table(voice, sweep=True)
            self.assertEqual(len(sweep), steps + 1)
            for k in range(steps):
                self.assertEqual(harmonics(sweep[k]), self.rule(voice, velocity[k]), (voice, k))
            np.testing.assert_allclose(sweep[-1], sweep[0], atol=1e-6)

    def test_every_table_has_its_sidecar(self):
        for voice in 'ABCD':
            for suffix in ('', '_sweep'):
                sidecar = self.root / 'mid' / f'dois_40_wavetable_{voice}{suffix}.txt'
                self.assertEqual(sidecar.read_text(), '[2048]\n[no interp]\n')

    def test_the_midi_did_not_change(self):
        expected = json.loads((PROJECT / 'tests/fixtures/dois_35_notes.json').read_text())
        actual = {p.name.removeprefix('dois_40_'): notes(p)
                  for p in (self.root / 'mid').glob('*.mid')}
        self.assertEqual(json.loads(json.dumps(actual)), expected)


class TheCheckerIsNotFooled(unittest.TestCase):
    """Break a table five ways; each must refuse the run with nothing reaching mid/."""

    SCRIPT = """
import sys, io, contextlib
import numpy as np
import compose, wavetable
mode = sys.argv[1]
if mode == 'factory':
    wavetable.serum_marker = lambda: '<!>2048 01000000 wavetable (www.xferrecords.com)'
elif mode == 'harmonic':
    real = wavetable.harmonics_for
    wavetable.harmonics_for = lambda rhythm, i: real(rhythm, i) + ([41] if i == 7 else [])
elif mode == 'strength':
    real = wavetable.frame_for
    def uneven(rhythm, i):
        frame = real(rhythm, i)
        if i == 9:
            t = 2 * np.pi * np.arange(2048) / 2048
            h = wavetable.harmonics_for(rhythm, i)[0]
            frame = frame + 0.2 * np.sin(h * t)
        return frame
    wavetable.frame_for = uneven
elif mode == 'phase':
    real = wavetable.frame_for
    def shifted(rhythm, i):
        frame = real(rhythm, i)
        return np.roll(frame, 3) if i == 11 else frame
    wavetable.frame_for = shifted
elif mode == 'sweep':
    real = wavetable.sweep_frames
    def swapped(table, velocities):
        frames = real(table, velocities)
        frames[0], frames[1] = frames[1], frames[0]
        return frames
    wavetable.sweep_frames = swapped
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

    def test_the_factory_flag_is_caught(self):
        self.refuse('factory')

    def test_a_harmonic_beyond_the_rule_is_caught(self):
        self.refuse('harmonic')

    def test_unequal_strength_is_caught(self):
        self.refuse('strength')

    def test_a_frame_out_of_phase_is_caught(self):
        self.refuse('phase')

    def test_a_sweep_out_of_step_with_the_midi_is_caught(self):
        self.refuse('sweep')


class InstallingIntoSerum(unittest.TestCase):
    """Against stand-ins: no test writes to Serum's real folders or reads its real prefs."""

    def setUp(self):
        sys.path.insert(0, str(PROJECT))
        self.addCleanup(sys.path.remove, str(PROJECT))
        import wavetable
        self.wavetable = wavetable

    def test_serum_s_own_presets_folder_is_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefs = Path(tmp) / 'Serum2Prefs.json'
            prefs.write_text(json.dumps({'Serum Presets Path': '/Users/x/My Serum/'}))
            self.assertEqual(self.wavetable.serum_presets_folder(str(prefs)), '/Users/x/My Serum')

    def test_without_prefs_it_falls_back_to_the_default(self):
        self.assertEqual(self.wavetable.serum_presets_folder('/nonexistent/prefs.json'),
                         self.wavetable.SERUM_DEFAULT)

    def test_one_folder_per_project_and_version(self):
        folder = self.wavetable.serum_tables_folder('/P')
        self.assertEqual(folder, '/P/Tables/sifters dois_40')

    def test_tables_get_short_names_and_nothing_else_is_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'mid'
            source.mkdir()
            for name in ('dois_40_wavetable_A.wav', 'dois_40_wavetable_A_sweep.wav'):
                (source / name).write_bytes(b'wav')
            (source / 'dois_40_wavetable_A.txt').write_text('[2048]')
            target = Path(tmp) / 'Tables' / 'sifters dois_40'
            copied = self.wavetable.install_into_serum(
                str(source), ['dois_40_wavetable_A.wav', 'dois_40_wavetable_A_sweep.wav',
                              'dois_40_wavetable_A.txt', 'x.mid'], str(target))
            self.assertEqual(sorted(copied), ['A sweep.wav', 'A.wav'])
            self.assertEqual(sorted(p.name for p in target.iterdir()), ['A sweep.wav', 'A.wav'])

    def test_a_folder_serum_would_not_scan_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                self.wavetable.install_into_serum(tmp, [], str(Path(tmp) / 'Tables' / 'a' / 'b'))

    def test_a_plain_render_installs_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(project_copy(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertNotIn('installed in Serum', result.stdout)


if __name__ == '__main__':
    unittest.main()
