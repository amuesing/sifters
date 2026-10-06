"""dois_36: the engine must serve any sieve AND any combination of base durations.

The author's rule (2026-10-03): *"I want the code to be useful for any given sieve, or
combination of base durations."* Every sieve tested before dois_36 used the same units —
sixteenths against one triplet-eighth voice — so the second half had never been tried.
Probing eight combinations found three refused and one impractical, for four distinct
reasons, each fixed here and tested below:

  1. a voice that reaches parity in ONE pass got a span accent of modulus 1, which
     fires on every step and can never be off — half the velocity profile unreachable;
  2. the checker measured a file's length from its last note, so a single-pass voice
     ending on a rest came back a step short and failed on correct music;
  3. units sharing few factors (120 against 180) made the exhaustive span search 64.6
     million candidates — about three hours;
  4. and, from ChatGPT's review of 2026-10-05, a weather that could not give every
     voice the whole profile was used anyway with only a printed warning.

Fixing 1 exposed a fifth: the state ceiling assumed every attack recurs. In one pass
an attack happens once, so a combination met by a single attack can give one velocity,
not two. The ceiling and the weather requirement now count occurrences across passes.
"""
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mido
import numpy as np

from test_dois36 import PROJECT

sys.path.insert(0, str(PROJECT))
import accents          # noqa: E402
import midi             # noqa: E402
import pitch            # noqa: E402
import sieve            # noqa: E402


class SinglePassVoices(unittest.TestCase):
    """Fix 1: an accent that can never be off carries nothing."""

    def test_a_multi_pass_voice_still_gets_the_smallest_modulus(self):
        self.assertEqual(accents.required_modulus(40, 160), 32)
        self.assertEqual(accents.required_modulus(40, 120), 3)

    def test_a_single_pass_voice_gets_a_cycle_that_can_switch(self):
        modulus = accents.required_modulus(40, 40)
        self.assertGreater(modulus, 1, 'modulus 1 fires on every step')
        self.assertEqual(math.lcm(40, modulus), 40,
                         'the voice must still end after exactly one pass')
        # the full layer, not its smallest factor: a 2-step accent is fixed by the
        # 8-step weather and left these voices at 7 of 8
        self.assertEqual(modulus, 40)


class OccurrencesNotCombinations(unittest.TestCase):
    """Fix 5: a combination needs two occurrences to sound with the span off AND on."""

    def setUp(self):
        self.firing = {'w': np.array([1, 1, 0, 0])}
        self.binary = np.array([1, 0, 1, 1])     # meets w=on once, w=off twice

    def test_repeated_passes_give_every_combination_both_states(self):
        self.assertEqual(accents.states_reachable(self.binary, self.firing, ['w'], 2), 4)

    def test_one_pass_gives_a_single_occurrence_one_state(self):
        self.assertEqual(accents.states_reachable(self.binary, self.firing, ['w'], 1), 3)


class EndToEnd(unittest.TestCase):
    """The combinations that were refused or impractical before dois_36, rendered."""

    SCRIPT = """
import sys, tempfile, io, contextlib, re
import config, compose
units = [int(x) for x in sys.argv[1].split(',')]
config.SPAN_RESIDUE_SOURCE = None
config.OUTPUT_DIR = tempfile.mkdtemp()
for cfg, ticks in zip(config.INSTRUMENT_CONFIGS, units):
    cfg.pop('duration', None)
    cfg['step_ticks'] = ticks
out = io.StringIO()
with contextlib.redirect_stdout(out):
    compose.main()
text = out.getvalue()
assert 'All checks passed' in text and 'FAILED' not in text, text[-3000:]
print(re.search(r'ceiling \\(([^)]*)\\)', text).group(1))
"""

    def render(self, units):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'copy'
            shutil.copytree(PROJECT, root,
                            ignore=shutil.ignore_patterns('mid', '__pycache__'))
            result = subprocess.run([sys.executable, '-B', '-c', self.SCRIPT, units],
                                    cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-3000:])
        return result.stdout.strip().splitlines()[-1]

    def test_every_voice_on_the_same_unit(self):
        """One pass each: the case where 'twice the combinations' was a false promise."""
        self.assertEqual(self.render('120,120,120,120'), 'A 8/8, B 8/8, C 8/8, D 8/8')

    def test_one_voice_reaching_parity_in_a_single_pass(self):
        self.assertEqual(self.render('120,120,120,240'), 'A 8/8, B 8/8, C 8/8, D 8/8')

    def test_units_that_share_few_factors(self):
        """120 against 180: 64.6 million candidates exhaustively, a second locally."""
        self.assertEqual(self.render('120,120,180,160'), 'A 8/8, B 8/8, C 8/8, D 8/8')


class TrailingSilence(unittest.TestCase):
    """Fix 2: the checker must read the file's true length."""

    def test_a_one_pass_rhythm_ending_on_a_rest_reads_back_whole(self):
        rhythm = [1, 0, 1, 1, 0, 0]                 # ends on two rests
        step = 120
        track = mido.MidiTrack()
        last = 0
        for i, on in enumerate(rhythm):
            if on:
                track.append(mido.Message('note_on', note=36, velocity=90,
                                          time=i * step - last))
                track.append(mido.Message('note_off', note=36, velocity=0, time=step))
                last = (i + 1) * step
        track.append(mido.MetaMessage('end_of_track', time=len(rhythm) * step - last))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'one_pass.mid'
            mid = mido.MidiFile(ticks_per_beat=480)
            mid.tracks.append(track)
            mid.save(path)
            layer, periodic = midi.rhythm_from_file(str(path), step, len(rhythm))
        self.assertTrue(periodic)
        self.assertEqual(list(layer), rhythm)


class TheWeatherRefuses(unittest.TestCase):
    """Fix 4: no silent fallback when the whole profile cannot sound everywhere."""

    def test_a_voice_with_too_few_attacks_refuses_the_run(self):
        # Two accents make four on/off combinations; a voice with three attacks can
        # meet at most three of them, whatever weather is chosen.
        many = np.array([1, 1, 0, 1, 1, 0, 1, 1, 1, 0] * 4)
        few = np.zeros(40, dtype=int)
        few[[0, 11, 27]] = 1
        voices = {'A': many, 'B': few}
        layers = {'A': 40, 'B': 40}
        with self.assertRaises(ValueError) as refused:
            accents.derive_weather(voices, '8@0|8@1|5@0', layers)
        message = str(refused.exception)
        self.assertIn('cannot sound in every voice', message)
        self.assertIn("'B'", message)
        self.assertIn('Nothing was written', message)

    def test_the_current_sieve_still_finds_its_weather(self):
        import config
        base = {}
        for cfg in config.INSTRUMENT_CONFIGS:
            binary, _ = sieve.build_binary(cfg, base)
            base[cfg['name']] = binary
        weather = accents.derive_weather(base, config.INSTRUMENT_CONFIGS[0]['sieve'],
                                         {n: 40 for n in base})
        self.assertEqual(weather, {'mod8': '8@1|8@3|8@4|8@5', 'mod5': '5@1|5@3'})


class OneModulusParser(unittest.TestCase):
    """ChatGPT's point: the lattice and the weather read the moduli one way."""

    SIEVES = ['(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))'
              '|8@3|8@4|(8@1&5@2)|(8@6&5@1)',
              '(7@0|7@1|7@3)&(5@0|5@2|5@3)|7@5|5@1',
              '(11@0|11@2|11@5|11@7)&(3@1|3@2)|11@9',
              '(4@0|4@1)&3@1|4@2']

    def test_both_use_the_same_function(self):
        self.assertIs(accents.sieve_moduli, sieve.sieve_moduli)
        self.assertIs(pitch.sieve_moduli, sieve.sieve_moduli)

    def test_what_it_reads_agrees_with_music21(self):
        import music21
        for expression in self.SIEVES:
            moduli = sieve.sieve_moduli(expression)
            self.assertEqual(math.lcm(*moduli),
                             music21.sieve.Sieve(expression).period(), expression)

    def test_a_disagreement_is_refused_not_trusted(self):
        real = sieve.nominal_period
        sieve.nominal_period = lambda expression: 7
        try:
            with self.assertRaises(ValueError):
                sieve.sieve_moduli('8@0|5@1')
        finally:
            sieve.nominal_period = real


if __name__ == '__main__':
    unittest.main()
