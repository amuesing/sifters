"""Protect existing renders from invalid manual accent settings."""
import json
import tempfile
import unittest

from test_dois30 import PROJECT, notes, project_copy, run


class Preflight(unittest.TestCase):
    def test_default_exports_match_claude30(self):
        expected = json.loads((PROJECT / 'tests/fixtures/dois_30_notes.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = {p.name.removeprefix('dois_30(gpt)_'): notes(p)
                      for p in (root / 'mid').glob('*.mid')}
            self.assertEqual(json.loads(json.dumps(actual)), expected)

    def test_explicit_settings_are_really_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            weather = {'w5': '5@1|5@3', 'w8': '8@1|8@3|8@4|8@6'}
            root = project_copy(tmp, weather=weather, span=(0, 1, 5, 10))
            settings = {}
            exec(compile((root / 'config.py').read_text(), 'config.py', 'exec'),
                 {'__file__': str(root / 'config.py')}, settings)
            self.assertEqual(settings['WEATHER'], weather)
            self.assertEqual(settings['SPAN_RESIDUE_SOURCE'], (0, 1, 5, 10))
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Weather (from config)', result.stdout)
            self.assertIn('span residues (from config)', result.stdout)

    def assert_preserved(self, replacement, message):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            before = {p.name: p.read_bytes() for p in (root / 'mid').glob('*.mid')}
            self.assertEqual(len(before), 12)
            path = root / 'config.py'
            text = path.read_text()
            for old, new in replacement.items():
                self.assertIn(old, text)
                text = text.replace(old, new)
            path.write_text(text)
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(message, result.stderr)
            self.assertNotIn('NameError', result.stderr)
            self.assertNotIn('Saved:', result.stdout)
            self.assertEqual(before, {p.name: p.read_bytes()
                                     for p in (root / 'mid').glob('*.mid')})

    def test_nonstatic_weather_preserves_all_previous_files(self):
        self.assert_preserved({
            'WEATHER = None\n': "WEATHER = {'w8':'8@1|8@3|8@4|8@6', 'w5':'5@1|5@3', 'w7':'7@0'}\n",
            'SPAN_RESIDUE_SOURCE = None\n': 'SPAN_RESIDUE_SOURCE = (0, 1, 5, 10)\n',
        }, 'Weather must be static')

    def test_duplicate_passes_give_actionable_error_and_preserve_files(self):
        self.assert_preserved({
            'SPAN_RESIDUE_SOURCE = None\n': 'SPAN_RESIDUE_SOURCE = (0,)\n',
        }, 'Set SPAN_RESIDUE_SOURCE = None')
