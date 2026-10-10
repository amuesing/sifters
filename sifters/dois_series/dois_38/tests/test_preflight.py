"""A bad setting must refuse the run and leave the twelve existing files alone.

dois_31 exists because three defects in dois_30 were found by ChatGPT in
`dois_30(gpt)`, and none of them could have been caught by the suite as it stood:

  1. a weather named in config skipped the static check, so a mod-7 accent replaced
     all twelve files with 134400-tick renders and only THEN failed verification;
  2. explicit residues that left identical passes raised NameError from a refusal
     path that called a function deleted in dois_30;
  3. the helper's overrides silently did nothing, which is why 1 and 2 went unseen.

These tests are the ones that would have caught them. Each renders twelve real files
first, then breaks config.py, and requires every byte of the twelve to survive.
"""
import json
import tempfile
import unittest

from test_dois38 import PROJECT, notes, project_copy, run


class MusicUnchanged(unittest.TestCase):

    def rendered(self, root):
        result = run(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = {p.name.removeprefix('dois_38_'): notes(p)
                  for p in (root / 'mid').glob('*.mid')}
        self.assertEqual(len(actual), 12)
        return json.loads(json.dumps(actual))

    def test_every_event_matches_the_dois_35_snapshot(self):
        expected = json.loads((PROJECT / 'tests/fixtures/dois_35_notes.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.rendered(project_copy(tmp)), expected)

    def test_no_note_has_moved_since_dois_30(self):
        """dois_34 widened the residue search, which moved 124 of 656 VELOCITIES.

        Velocity is the only thing the span accent can touch: the rhythm comes from the
        sieve and the pitch from the mode. So onsets, durations, pitches and channels
        must be exactly what dois_30 wrote, and this asserts it field by field.
        """
        expected = json.loads((PROJECT / 'tests/fixtures/dois_30_notes.json').read_text())

        def without_velocity(tracks):
            return [[[n[0], n[1], n[2], n[4]] for n in track] for track in tracks]

        with tempfile.TemporaryDirectory() as tmp:
            actual = self.rendered(project_copy(tmp))
            self.assertEqual({k: without_velocity(v) for k, v in actual.items()},
                             {k: without_velocity(v) for k, v in expected.items()})
            self.assertNotEqual(actual, expected)      # velocities DID change


class Preflight(unittest.TestCase):

    def assert_files_survive(self, edits, expected_message):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            before = {p.name: p.read_bytes() for p in (root / 'mid').glob('*.mid')}
            self.assertEqual(len(before), 12)

            text = (root / 'config.py').read_text()
            for old, new in edits.items():
                self.assertIn(old, text)
                text = text.replace(old, new)
            (root / 'config.py').write_text(text)

            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(expected_message, result.stderr)
            self.assertNotIn('NameError', result.stderr)   # the dois_30 refusal path
            self.assertNotIn('Saved:', result.stdout)
            self.assertEqual(before, {p.name: p.read_bytes()
                                      for p in (root / 'mid').glob('*.mid')})

    def test_a_weather_that_is_not_static_is_refused_before_writing(self):
        self.assert_files_survive(
            {"WEATHER = None\n":
                "WEATHER = {'mod8': '8@1|8@3|8@4|8@6', 'mod5': '5@1|5@3', 'mod7': '7@0'}\n"},
            'must be static')

    def test_residues_that_leave_identical_passes_say_so_and_write_nothing(self):
        self.assert_files_survive(
            {"SPAN_RESIDUE_SOURCE = (0, 9, 10, 21, 31)\n":
                "SPAN_RESIDUE_SOURCE = (0,)\n"},
            'leaves identical passes')


class OverridesReallyApply(unittest.TestCase):
    """The helper must fail loudly when an override does not land — defect 3."""

    def test_explicit_settings_reach_the_run(self):
        weather = {'mod8': '8@1|8@3|8@4|8@6', 'mod5': '5@1|5@3'}
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, weather=weather, span=(0, 1, 5, 10))
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Weather (from config)', result.stdout)
            self.assertIn('span residues (from config): (0, 1, 5, 10)', result.stdout)

    def test_an_override_that_stops_matching_fails_the_test_that_asked_for_it(self):
        """Rename the setting and the helper must raise, not carry on quietly."""
        import test_dois38
        original = test_dois38.WEATHER
        try:
            test_dois38.WEATHER = __import__('re').compile(r'^NOT_A_SETTING = .*$',
                                                           __import__('re').M)
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(AssertionError):
                    project_copy(tmp, weather={'mod5': '5@0'})
        finally:
            test_dois38.WEATHER = original


if __name__ == '__main__':
    unittest.main()


class ThreeDifferentFailures(unittest.TestCase):
    """First convergence, accent capacity and the bounded search are not one thing.

    ChatGPT asked for these to be distinguished (FOR_CLAUDE.md, 2026-09-30) because
    dois_31 answered all three with the same sentence — one that told the author to
    change the sieve even when the sieve was fine and only a selection rule of mine
    had failed.
    """

    def test_capacity_is_counted_for_every_voice_of_the_current_sieve(self):
        import sys
        sys.path.insert(0, str(PROJECT))
        try:
            import compose, config, sieve as sieve_module
            base, layers = {}, {}
            for cfg in config.INSTRUMENT_CONFIGS:
                binary, period = sieve_module.build_binary(cfg, base)
                base[cfg['name']], layers[cfg['name']] = binary, period
            units = {c['name']: compose.get_step_ticks(c) for c in config.INSTRUMENT_CONFIGS}
            parity = 19200
            capacity = compose.pass_capacity(base, layers, units, parity)
            self.assertEqual({n: (k, passes) for n, (k, passes, _) in capacity.items()},
                             {'A': (27, 4), 'B': (13, 4), 'C': (27, 4), 'D': (20, 3)})
            for name, (attacks, passes, most) in capacity.items():
                self.assertEqual(most, 2 ** attacks)
                self.assertLess(passes, most, name)      # nothing here is over capacity
        finally:
            sys.path.remove(str(PROJECT))

    def test_a_failed_search_does_not_claim_the_sieve_is_at_fault(self):
        """Nothing distinct was found: say the SEARCH failed, and claim nothing more."""
        import sys
        sys.path.insert(0, str(PROJECT))
        try:
            import compose
            message = compose.no_residues_message(None, {'A': 8}, 16, 4)
            self.assertIn('failure of THIS bounded search', message)
            self.assertIn('not a proof that no residues exist', message)
            self.assertNotIn('cannot', message)
        finally:
            sys.path.remove(str(PROJECT))

    def test_a_failed_ceiling_is_reported_as_a_selection_rule_not_a_principle(self):
        """Principle IV was met; only my own ceiling rule was not. Say which."""
        import sys
        sys.path.insert(0, str(PROJECT))
        try:
            import compose
            message = compose.no_residues_message(((0, 1, 5, 10), {'A': 6, 'B': 6}),
                                                  {'A': 8, 'B': 6}, 16, 4)
            self.assertIn('Principle IV is satisfiable', message)
            self.assertIn('SPAN_RESIDUE_SOURCE = (0, 1, 5, 10)', message)
            self.assertIn("{'A': '6/8'}", message)        # only the voice that fell short
            self.assertIn('selection rule, not a principle', message)
        finally:
            sys.path.remove(str(PROJECT))
