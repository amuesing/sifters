"""Serum wavetables, dois_41: every frame states one period of the sieve, cut in its own place.

The rule: frame i reads the sieve from i + 1, as dois_40 did, and sounds it from just above
its cut c = 13 * i mod 40 (the lattice's diagonal): harmonic c + h sounds, at full
strength, when i + h is in the voice's sieve. What has to be true, and is tested here:

  * Serum 2's file format, a marker with no blending and the factory flag clear;
  * 128 frames, so note number or velocity v lands exactly on frame v;
  * every frame follows the rule exactly — the right harmonics, equal strength, in phase,
    nothing outside its period — and states each of the sieve's residues exactly once;
  * the variety the design exists for, measured as the ear hears it: register (spectral
    centroid) spreads across the table and jumps between neighbouring frames, where
    dois_40 moved 0.17 octave across the whole table;
  * one level: every frame the same RMS, the loudest peak at the headroom limit;
  * nothing above harmonic 79, so a fixed-pitch oscillator at middle C stays under 22 kHz;
  * B the complement of A in every frame; the sweep follows the velocities the MIDI plays;
  * the checker refuses tables broken six ways, with nothing reaching mid/;
  * installation finds Serum's own folder and writes Tables/<project>/<version>.
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

from test_engine import PROJECT, notes, project_copy, run

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


def harmonics(frame):
    mag = np.abs(np.fft.rfft(frame))
    return {h for h in range(1, len(mag)) if mag[h] > 1e-3 * mag.max()}


def brightness(frame):
    """Spectral centroid in octaves above the fundamental: what the ear calls bright."""
    mag = np.abs(np.fft.rfft(frame)) ** 2
    h = np.arange(len(mag))
    return np.log2((h * mag).sum() / mag.sum())


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
        chunks, audio = read(self.root / 'mid' / f'dois_45_wavetable_{voice}{suffix}.wav')
        return chunks, audio.reshape(-1, FRAME)

    def rule(self, voice, i):
        sieve = self.base[voice]
        period = len(sieve)
        start = (13 * i) % period
        return {start + h for h in range(1, period + 1) if sieve[(i + h) % period]}

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
        """Frame i sounds exactly one period from its cut, at equal strength."""
        for voice in 'ABCD':
            _, frames = self.table(voice)
            self.assertEqual(len(frames), 128)
            for i, frame in enumerate(frames):
                self.assertEqual(harmonics(frame), self.rule(voice, i), (voice, i))
                mag = np.abs(np.fft.rfft(frame))
                present = sorted(self.rule(voice, i))
                np.testing.assert_allclose(mag[present], mag[present].max(), rtol=1e-3)

    def test_every_frame_states_each_residue_once(self):
        """The period, stated once in frequency: every member of the sieve, exactly once."""
        for voice in 'ABCD':
            sieve = self.base[voice]
            members = {r for r in range(len(sieve)) if sieve[r]}
            _, frames = self.table(voice)
            for i, frame in enumerate(frames):
                start = (13 * i) % 40
                read = sorted((i + m - start) % 40 for m in harmonics(frame))
                self.assertEqual(read, sorted(members), (voice, i))

    def test_nothing_above_two_periods(self):
        """79 at most: 20.7 kHz at middle C, so a fixed-pitch oscillator keeps every frame."""
        for voice in 'ABCD':
            _, frames = self.table(voice)
            self.assertLessEqual(max(max(harmonics(f)) for f in frames), 79, voice)

    def test_register_spreads_and_jumps(self):
        """What the ear hears: brightness moves across the table and between neighbours.

        dois_40 moved 0.17 octave across all 128 frames, and the author heard them as alike.
        Measured on this rule: 1.5 octaves across the table, 0.55 between neighbours.
        """
        for voice in 'ABCD':
            _, frames = self.table(voice)
            bright = np.array([brightness(f) for f in frames])
            self.assertGreater(bright.max() - bright.min(), 1.4, voice)
            self.assertGreater(np.median(np.abs(np.diff(bright))), 0.45, voice)

    def test_every_voice_has_forty_frames_and_eight_velocity_timbres(self):
        """A cut alone gave B only 14 distinct frames; reading from i keeps all 40."""
        for voice in 'ABCD':
            _, frames = self.table(voice)
            self.assertEqual(len({tuple(sorted(harmonics(f))) for f in frames[:40]}), 40, voice)

    def test_one_level_for_the_whole_table(self):
        """Same RMS in every frame, the loudest peak at the headroom limit (ChatGPT, 2026-10-12)."""
        for voice in 'ABCD':
            for sweep in (False, True):
                _, frames = self.table(voice, sweep)
                rms = np.sqrt((frames.astype(float) ** 2).mean(axis=1))
                np.testing.assert_allclose(rms, rms[0], rtol=1e-4, err_msg=voice)
            _, frames = self.table(voice)
            self.assertAlmostEqual(float(np.abs(frames).max()), 0.95, places=6)

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
        """In every frame B holds exactly the harmonics of the period A's frame leaves out."""
        _, a = self.table('A')
        _, b = self.table('B')
        for i in range(128):
            start = (13 * i) % 40
            self.assertEqual(harmonics(a[i]) | harmonics(b[i]), set(range(start + 1, start + 41)), i)
            self.assertEqual(harmonics(a[i]) & harmonics(b[i]), set(), i)

    def test_the_sweep_follows_the_velocities_the_midi_plays(self):
        for voice, unit, steps in (('A', 120, 160), ('B', 120, 160), ('C', 120, 160),
                                   ('D', 160, 120)):
            (track,) = notes(self.root / 'mid' / f'dois_45_static_{voice}_prime.mid')
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
                sidecar = self.root / 'mid' / f'dois_45_wavetable_{voice}{suffix}.txt'
                self.assertEqual(sidecar.read_text(), '[2048]\n[no interp]\n')

    def test_the_midi_is_the_dois_42_snapshot(self):
        expected = json.loads((PROJECT / 'tests/fixtures/dois_42_notes.json').read_text())
        actual = {p.name.removeprefix('dois_45_'): notes(p)
                  for p in (self.root / 'mid').glob('*.mid')
                  if not p.name.startswith('dois_45_canon_')
                  and not p.name.endswith('_form.mid')}
        self.assertEqual(json.loads(json.dumps(actual)), expected)


class TheCheckerIsNotFooled(unittest.TestCase):
    """Break a table six ways; each must refuse the run with nothing reaching mid/."""

    SCRIPT = """
import sys, io, contextlib
import numpy as np
import compose, wavetable
mode = sys.argv[1]
if mode == 'factory':
    wavetable.serum_marker = lambda: '<!>2048 01000000 wavetable (www.xferrecords.com)'
elif mode == 'harmonic':
    real = wavetable.harmonics_for
    wavetable.harmonics_for = lambda rhythm, order, i: (
        real(rhythm, order, i) + ([120] if i == 7 else []))
elif mode == 'strength':
    real = wavetable.frame_for
    def uneven(rhythm, order, i):
        frame = real(rhythm, order, i)
        if i == 9:
            t = 2 * np.pi * np.arange(2048) / 2048
            h = wavetable.harmonics_for(rhythm, order, i)[0]
            frame = frame + 0.2 * np.sin(h * t)
        return frame
    wavetable.frame_for = uneven
elif mode == 'phase':
    real = wavetable.frame_for
    def shifted(rhythm, order, i):
        frame = real(rhythm, order, i)
        return np.roll(frame, 3) if i == 11 else frame
    wavetable.frame_for = shifted
elif mode == 'level':
    real = wavetable.integer_frames
    def drifting(rhythm, order):
        frames = real(rhythm, order)
        frames[13] = 0.9 * frames[13]          # what per-frame normalising used to do
        return frames
    wavetable.integer_frames = drifting
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

    def test_a_frame_at_another_level_is_caught(self):
        self.refuse('level')


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

    def test_one_project_folder_with_a_folder_per_version(self):
        folder = self.wavetable.serum_tables_folder('/P')
        self.assertEqual(folder, '/P/Tables/sifters/dois_45')

    def test_tables_get_short_names_and_nothing_else_is_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'mid'
            source.mkdir()
            for name in ('dois_45_wavetable_A.wav', 'dois_45_wavetable_A_sweep.wav'):
                (source / name).write_bytes(b'wav')
            (source / 'dois_45_wavetable_A.txt').write_text('[2048]')
            target = Path(tmp) / 'Tables' / 'sifters' / 'dois_45'
            copied = self.wavetable.install_into_serum(
                str(source), ['dois_45_wavetable_A.wav', 'dois_45_wavetable_A_sweep.wav',
                              'dois_45_wavetable_A.txt', 'x.mid'], str(target))
            self.assertEqual(sorted(copied), ['A sweep.wav', 'A.wav'])
            self.assertEqual(sorted(p.name for p in target.iterdir()), ['A sweep.wav', 'A.wav'])

    def test_a_folder_outside_the_scheme_is_refused(self):
        """Deeper than Serum's own tables go, or the old top-level `sifters dois_40` name."""
        with tempfile.TemporaryDirectory() as tmp:
            for wrong in (Path(tmp) / 'Tables' / 'a' / 'b' / 'c',
                          Path(tmp) / 'Tables' / 'sifters dois_45'):
                with self.assertRaises(ValueError, msg=str(wrong)):
                    self.wavetable.install_into_serum(tmp, [], str(wrong))

    def test_a_plain_render_installs_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(project_copy(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertNotIn('installed in Serum', result.stdout)


if __name__ == '__main__':
    unittest.main()
