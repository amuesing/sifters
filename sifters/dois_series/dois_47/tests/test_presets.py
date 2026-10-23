"""The Serum presets (dois_47): written without Serum, read back, and held to the rule.

The engine writes Serum 2's preset format itself, CBOR inside a zstd container. These tests
pin the encoder against RFC 8949's own examples, read every preset back with check.py's
reader, and require a broken preset to be refused with nothing moved.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_engine import PROJECT, project_copy, rendered, run

sys.path.insert(0, str(PROJECT))
import check                # noqa: E402
import serum                # noqa: E402


def preset(root, name):
    return check.read_preset(Path(root) / 'presets' / f'{name}.SerumPreset')


def heard_hz(patch, osc='Oscillator0'):
    p = patch[osc]['plainParams']
    return serum.MIDI0_HZ * 2 ** (p['kParamOctave'] + (p['kParamCoarsePit'] + p['kParamFine'] / 100) / 12)


class TheEncoder(unittest.TestCase):
    """RFC 8949, Appendix A: the examples the standard gives, byte for byte."""

    EXAMPLES = [(0, '00'), (1, '01'), (10, '0a'), (23, '17'), (24, '1818'), (25, '1819'),
                (100, '1864'), (1000, '1903e8'), (1000000, '1a000f4240'),
                (1000000000000, '1b000000e8d4a51000'), (-1, '20'), (-10, '29'), (-100, '3863'),
                (-1000, '3903e7'), (1.1, 'fb3ff199999999999a'), (-4.1, 'fbc010666666666666'),
                (1.0e+300, 'fb7e37e43c8800759c'), (False, 'f4'), (True, 'f5'), (None, 'f6'),
                ('', '60'), ('a', '6161'), ('IETF', '6449455446'), ('"\\', '62225c'),
                ('ü', '62c3bc'), ('水', '63e6b0b4'), ([], '80'), ([1, 2, 3], '83010203'),
                ([1, [2, 3], [4, 5]], '8301820203820405'),
                (list(range(1, 26)), '98190102030405060708090a0b0c0d0e0f101112131415161718181819'),
                ({}, 'a0'), ({'a': 1, 'b': [2, 3]}, 'a26161016162820203'),
                (['a', {'b': 'c'}], '826161a161626163')]

    def test_every_example_in_the_standard(self):
        for value, expected in self.EXAMPLES:
            self.assertEqual(serum.cbor(value).hex(), expected, repr(value))

    def test_the_checker_reads_back_what_the_writer_writes(self):
        value = {'a': [1, -2, 3.5, True, None, 'x' * 300], 'b': {'c': list(range(70000, 70003))}}
        decoded, end = check.read_cbor(serum.cbor(value))
        self.assertEqual(decoded, value)
        self.assertEqual(end, len(serum.cbor(value)))


class ThePresets(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = project_copy(cls.tmp.name)
        cls.result = run(cls.root)
        assert cls.result.returncode == 0, cls.result.stdout[-3000:] + cls.result.stderr

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_one_preset_per_track_is_written_and_verified(self):
        self.assertIn('presets verified', self.result.stdout)
        self.assertEqual({p.name for p in (self.root / 'presets').glob('*')},
                         {f'dois_47 {v}.SerumPreset' for v in 'ABCD'})

    def test_they_are_marked_as_sifters(self):
        header, patch = preset(self.root, 'dois_47 B')
        self.assertEqual(header['presetAuthor'], 'sifters')
        self.assertEqual(header['tags'], ['sifters', 'FM pair', 'Percussion', 'Wavetable'])
        self.assertEqual(patch['presetName'], 'dois_47 B')
        self.assertIn('for track B', header['presetDescription'])
        self.assertIn('complement', header['presetDescription'])

    def test_each_drum_comes_from_its_voices_rhythm(self):
        """A and C strike 5.4 times a second (172.8 Hz), B 2.6 (83.2 Hz), D 3.0 (96 Hz)."""
        for voice, hz, decay in (('A', 172.8, 0.125), ('B', 83.2, 0.375), ('C', 172.8, 0.125),
                                 ('D', 96.0, 1 / 3)):
            _, patch = preset(self.root, f'dois_47 {voice}')
            self.assertAlmostEqual(heard_hz(patch), hz, delta=0.05)
            self.assertAlmostEqual(patch['Env0']['plainParams']['kParamDecay'], decay, places=9)
            # the strike: 13/40 of an octave, 390 cents, at ~1.2 semitones per unit
            self.assertAlmostEqual(patch['ModSlot2']['plainParams']['kParamAmount'], 3.25, places=9)

    def test_each_is_modulated_by_its_complement_at_1_to_1(self):
        for voice in 'ABCD':
            _, patch = preset(self.root, f'dois_47 {voice}')
            self.assertEqual(patch['Oscillator0']['WTOsc0']['relativePathToWT'],
                             f'sifters/dois_47/{voice}.wav')
            self.assertEqual(patch['Oscillator1']['WTOsc1']['relativePathToWT'],
                             f'sifters/dois_47/not {voice}.wav')
            self.assertEqual(patch['Oscillator0']['WTOsc0']['plainParams']['kParamWarpMenu'], 'kFM_OSC')
            self.assertEqual(heard_hz(patch, 'Oscillator1'), heard_hz(patch))
            self.assertEqual(patch['ModSlot0']['source'], [16, 0])     # velocity picks the frame
            self.assertEqual(patch['ModSlot3']['source'], [16, 0])     # in both tables

    def test_the_complement_tables_are_complements(self):
        """not A is B's table and not B is A's, byte for byte: they modulate each other."""
        tables = self.root / 'wavetables'
        self.assertEqual((tables / 'dois_47_wavetable_not_A.wav').read_bytes(),
                         (tables / 'dois_47_wavetable_B.wav').read_bytes())
        self.assertEqual((tables / 'dois_47_wavetable_not_B.wav').read_bytes(),
                         (tables / 'dois_47_wavetable_A.wav').read_bytes())

    def test_a_rerender_writes_the_same_bytes(self):
        before = {p.name: p.read_bytes() for p in (self.root / 'presets').glob('*')}
        self.assertEqual(run(self.root).returncode, 0)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.root / 'presets').glob('*')})


class TheCheckerIsNotFooled(unittest.TestCase):
    """Break a preset in the writer; the run must refuse, and nothing may move."""

    SCRIPT = """
import sys, io, contextlib
import serum, compose
mode = sys.argv[1]
if mode == 'modulator':
    real = serum.fm_patch
    def wrong(init, title, cfg, numbers):
        data = real(init, title, cfg, numbers)
        data['Oscillator1']['WTOsc1']['relativePathToWT'] = serum.table_path(title, cfg['name'])
        return data
    serum.fm_patch = wrong
elif mode == 'decay':
    real = serum.drum
    serum.drum = lambda binary, step: dict(real(binary, step), decay_s=2 * real(binary, step)['decay_s'])
elif mode == 'ratio':
    real = serum.fm_patch
    def detuned(init, title, cfg, numbers):
        data = real(init, title, cfg, numbers)
        data['Oscillator1']['plainParams']['kParamCoarsePit'] += 0.1
        return data
    serum.fm_patch = detuned
elif mode == 'bytes':
    real = serum.preset_bytes
    def corrupt(*args):
        blob = bytearray(real(*args))
        blob[-1] ^= 1
        return bytes(blob)
    serum.preset_bytes = corrupt
out = io.StringIO()
with contextlib.redirect_stdout(out):
    try:
        compose.main()
    except SystemExit:
        pass
sys.exit(0 if 'presets FAILED' in out.getvalue() else 'a broken preset passed verification')
"""

    def refuse(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = subprocess.run([sys.executable, '-B', '-c', self.SCRIPT, mode],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertEqual(rendered(root), {})

    def test_a_modulator_that_is_not_the_complement_is_caught(self):
        self.refuse('modulator')

    def test_a_decay_that_is_not_the_median_gap_is_caught(self):
        self.refuse('decay')

    def test_a_modulator_off_1_to_1_is_caught(self):
        self.refuse('ratio')

    def test_a_corrupted_file_is_caught(self):
        self.refuse('bytes')


class Installing(unittest.TestCase):

    def test_the_folder_is_presets_user_project_piece(self):
        self.assertEqual(serum.presets_folder('/P'), '/P/Presets/User/sifters/dois_47')

    def test_installing_replaces_its_own_folder_and_nothing_else(self):
        """A preset or table a render no longer makes must not linger beside the new ones."""
        import wavetable
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'out'
            source.mkdir()
            (source / 'new.SerumPreset').write_bytes(b'preset')
            (source / 'dois_47_wavetable_A.wav').write_bytes(b'wav')
            presets = Path(tmp) / 'Presets' / 'User' / 'sifters' / 'dois_47'
            tables = Path(tmp) / 'Tables' / 'sifters' / 'dois_47'
            other = Path(tmp) / 'Presets' / 'User' / 'sifters' / 'dois_45'
            for folder in (presets, tables, other):
                folder.mkdir(parents=True)
            (presets / 'stale.SerumPreset').write_bytes(b'old')
            (tables / 'stale.wav').write_bytes(b'old')
            (other / 'kept.SerumPreset').write_bytes(b'another version')
            serum.install_presets(str(source), ['new.SerumPreset'], str(presets))
            wavetable.install_into_serum(str(source), ['dois_47_wavetable_A.wav'], str(tables))
            self.assertEqual([p.name for p in presets.iterdir()], ['new.SerumPreset'])
            self.assertEqual([p.name for p in tables.iterdir()], ['A.wav'])
            self.assertEqual([p.name for p in other.iterdir()], ['kept.SerumPreset'])

    def test_only_presets_are_copied_and_only_into_that_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'presets'
            source.mkdir()
            (source / 'x.SerumPreset').write_bytes(b'preset')
            target = Path(tmp) / 'Presets' / 'User' / 'sifters' / 'dois_47'
            copied = serum.install_presets(str(source), ['x.SerumPreset', 'y.mid'], str(target))
            self.assertEqual(copied, ['x.SerumPreset'])
            self.assertEqual([p.name for p in target.iterdir()], ['x.SerumPreset'])
            with self.assertRaises(ValueError):
                serum.install_presets(str(source), [], str(Path(tmp) / 'Presets' / 'sifters'))


if __name__ == '__main__':
    unittest.main()
