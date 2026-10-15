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

from test_dois31 import PROJECT, notes, project_copy, run


class MusicUnchanged(unittest.TestCase):

    def test_every_note_matches_dois_30(self):
        """dois_31 fixes refusals, not music. Nothing an export contains may move."""
        expected = json.loads((PROJECT / 'tests/fixtures/dois_30_notes.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = {p.name.removeprefix('dois_31_'): notes(p)
                      for p in (root / 'mid').glob('*.mid')}
            self.assertEqual(len(actual), 12)
            self.assertEqual(json.loads(json.dumps(actual)), expected)


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
            {"SPAN_RESIDUE_SOURCE = None\n": "SPAN_RESIDUE_SOURCE = (0,)\n"},
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
        import test_dois31
        original = test_dois31.WEATHER
        try:
            test_dois31.WEATHER = __import__('re').compile(r'^NOT_A_SETTING = .*$',
                                                           __import__('re').M)
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(AssertionError):
                    project_copy(tmp, weather={'mod5': '5@0'})
        finally:
            test_dois31.WEATHER = original


if __name__ == '__main__':
    unittest.main()
