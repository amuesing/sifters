"""The three things the author asked for, asserted from the rendered MIDI.

  1. every repeat of every voice has a UNIQUE velocity pattern, even where its rhythm
     and its pitches repeat exactly;
  2. the ENTIRE velocity profile is expressed — all eight levels, in every voice;
  3. the accent profile lasts EXACTLY as long as that voice needs to reach parity with
     the others. Not longer, not shorter.

Requirements 1 and 3 have been enforced since dois_27 and dois_32. Requirement 2 is new
in dois_35: until then the weather was chosen one modulus at a time, which left B unable
to reach two of the eight velocities no matter what the span accent did.
"""
import json
import tempfile
import unittest

from test_dois36 import PROJECT, notes, project_copy, run

PARITY_TICKS = 19200
STEP_TICKS = {'A': 120, 'B': 120, 'C': 120, 'D': 160}
PASSES = {'A': 4, 'B': 4, 'C': 4, 'D': 3}
LAYER = 40


class TheThreeRequirements(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = project_copy(cls.tmp.name)
        result = run(root)
        assert result.returncode == 0, result.stderr
        cls.root, cls.stdout = root, result.stdout

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def velocities_by_step(self, voice, mode='static'):
        (track,) = notes(self.root / 'mid' / f'dois_36_{mode}_{voice}_prime.mid')
        unit = STEP_TICKS[voice]
        return {onset // unit: velocity for onset, _, _, velocity, _ in track}

    def test_1_every_repeat_has_a_unique_velocity_pattern(self):
        for voice, passes in PASSES.items():
            at = self.velocities_by_step(voice)
            patterns = [tuple(at.get(i + LAYER * p, 0) for i in range(LAYER))
                        for p in range(passes)]
            self.assertEqual(len(patterns), passes, voice)
            self.assertEqual(len(set(patterns)), passes,
                             f'{voice} repeats a velocity pattern')

    def test_1b_the_rhythm_really_does_repeat_underneath(self):
        """Otherwise requirement 1 would be trivially satisfied by a changing rhythm."""
        for voice, passes in PASSES.items():
            at = self.velocities_by_step(voice)
            attacks = [tuple(sorted(i for i in range(LAYER) if i + LAYER * p in at))
                       for p in range(passes)]
            self.assertEqual(len(set(attacks)), 1,
                             f"{voice}'s rhythm is not identical on every pass")

    def test_2_every_voice_expresses_the_entire_velocity_profile(self):
        table = sorted(int(v) for v in
                       self.stdout.split('velocity table, shared by every voice: ')[1]
                       .splitlines()[0].split())
        self.assertEqual(len(table), 8)
        for voice in PASSES:
            used = sorted(set(self.velocities_by_step(voice).values()))
            self.assertEqual(used, table,
                             f'{voice} is missing {sorted(set(table) - set(used))}')

    def test_3_the_accent_profile_is_exactly_the_parity_duration(self):
        for voice, passes in PASSES.items():
            at = self.velocities_by_step(voice)
            span_steps = max(at) + 1
            self.assertLessEqual(span_steps, passes * LAYER, voice)
            self.assertEqual(passes * LAYER * STEP_TICKS[voice], PARITY_TICKS, voice)
            # and the profile does not close sooner than that, which would mean the
            # accents repeat inside the parity span
            patterns = [tuple(at.get(i + LAYER * p, 0) for i in range(LAYER))
                        for p in range(passes)]
            for shorter in range(1, passes):
                if passes % shorter:
                    continue
                self.assertNotEqual(patterns, patterns[:shorter] * (passes // shorter),
                                    f'{voice} closes after {shorter} pass(es), '
                                    f'not the {passes} parity costs')

    def test_the_velocities_are_the_same_in_both_pitch_modes(self):
        for voice in PASSES:
            self.assertEqual(self.velocities_by_step(voice, 'static'),
                             self.velocities_by_step(voice, 'lattice'), voice)


class TheWeatherIsWhatMakesRequirementTwoPossible(unittest.TestCase):

    def test_the_blind_choice_of_dois_34_could_not_satisfy_it(self):
        """Pin the weather dois_34 derived and B falls two velocities short.

        This is the test that gives dois_35 its reason to exist. If the densest half
        per modulus had been good enough, this would pass with eight.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, weather={'mod8': '8@1|8@3|8@4|8@6',
                                              'mod5': '5@1|5@3'})
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            used = {v: len(set(
                velocity for _, _, _, velocity, _ in
                notes(root / 'mid' / f'dois_36_static_{v}_prime.mid')[0]))
                for v in PASSES}
            self.assertEqual(used['B'], 6, 'B should be short under the blind weather')
            self.assertEqual([used['A'], used['C'], used['D']], [8, 8, 8])

    def test_the_derived_weather_satisfies_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertIn('mod8 = 8@1|8@3|8@4|8@5, mod5 = 5@1|5@3', result.stdout)
            self.assertIn('A 8/8, B 8/8, C 8/8, D 8/8', result.stdout)


if __name__ == '__main__':
    unittest.main()


class ParityIsTheMinimum(unittest.TestCase):
    """The accents must reach parity at the EARLIEST moment it is possible, not later.

    The author's wording: *"the accent sieves should achieve the exact minimum duration
    for all voices to achieve parity... and by parity I mean that voices of different
    durations (because of base durational values of rhythms) end at the exact same
    time."*

    Three separate claims hide in that, and each is tested here:

      1. the parity point is the SMALLEST tick count at which every voice ends together;
      2. every voice's accent profile is exactly that long — not a multiple of it;
      3. each voice's span accent uses the SMALLEST modulus that gets it there, since a
         larger one would reach parity too and overshoot on the way. (A voice that
         reaches parity in ONE pass is the exception from dois_36: its smallest is 1,
         an accent that never switches, so it takes its own layer — which still ends
         it after exactly one pass. This piece has no such voice.)

    `compose.parity_point` computes an LCM, which is minimal by construction, and
    `require_first_parity` asserts the voices land on it. Neither of those would notice
    if the definition itself drifted — if the LCM were replaced by some multiple, or the
    modulus chosen loosely. These tests pin the definition, not the arithmetic.
    """

    def setUp(self):
        import math
        import sys
        sys.path.insert(0, str(PROJECT))
        import config, compose
        from sieve import build_binary
        self.math = math
        base, layers = {}, {}
        for cfg in config.INSTRUMENT_CONFIGS:
            binary, period = build_binary(cfg, base)
            base[cfg['name']], layers[cfg['name']] = binary, period
        self.base, self.layers = base, layers
        self.units = {c['name']: compose.get_step_ticks(c)
                      for c in config.INSTRUMENT_CONFIGS}
        self.raw = {n: layers[n] * self.units[n] for n in layers}
        self.parity = math.lcm(*self.raw.values())
        self.addCleanup(sys.path.remove, str(PROJECT))

    def test_1_no_shorter_duration_lets_every_voice_end_together(self):
        """Brute force, not an LCM: check every tick count below the parity point."""
        self.assertEqual(self.parity, PARITY_TICKS)
        earlier = [t for t in range(1, self.parity)
                   if all(t % raw == 0 for raw in self.raw.values())]
        self.assertEqual(earlier, [], 'a shorter shared ending exists')
        # and it IS an ending for every voice, not merely the smallest candidate
        for name, raw in self.raw.items():
            self.assertEqual(self.parity % raw, 0, name)

    def test_2_each_accent_profile_is_exactly_that_long(self):
        for voice, passes in PASSES.items():
            ticks = passes * LAYER * STEP_TICKS[voice]
            self.assertEqual(ticks, self.parity,
                             f'{voice} runs {ticks} ticks, parity is {self.parity}')

    def test_3_the_span_modulus_is_the_smallest_that_reaches_parity(self):
        import sys
        from accents import required_modulus
        for voice, layer in self.layers.items():
            target = self.parity // self.units[voice]
            chosen = required_modulus(layer, target)
            self.assertIsNotNone(chosen, voice)
            self.assertEqual(self.math.lcm(layer, chosen), target, voice)
            smaller = [k for k in range(1, chosen)
                       if self.math.lcm(layer, k) == target]
            self.assertEqual(smaller, [],
                             f'{voice} could have used modulus {smaller} instead '
                             f'of {chosen}')

    def test_4_the_weather_never_extends_the_profile(self):
        """A weather accent whose period did not divide the layer would push past it."""
        from accents import derive_weather
        from sieve import true_period
        import config
        weather = config.WEATHER or derive_weather(
            self.base, config.INSTRUMENT_CONFIGS[0]['sieve'], self.layers, quiet=True)
        for label, expression in weather.items():
            period = true_period(expression, quiet=True)
            for voice, layer in self.layers.items():
                self.assertEqual(layer % period, 0,
                                 f'{label} (period {period}) does not divide '
                                 f"{voice}'s {layer}-step layer")
