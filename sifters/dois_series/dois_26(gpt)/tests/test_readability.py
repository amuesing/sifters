"""Refactoring must preserve the music, settings, and independent velocity checks."""
import json
import subprocess
import sys
import tempfile
import unittest

from test_dois26 import PROJECT, notes, project_copy, run


class ReadabilityContracts(unittest.TestCase):
    def test_all_twelve_exports_match_dois25(self):
        baseline = json.loads((PROJECT / 'tests/fixtures/dois_25_notes.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = {p.name.removeprefix('dois_26(gpt)_'): notes(p)
                      for p in (root / 'mid').glob('*.mid')}
            self.assertEqual(json.loads(json.dumps(actual)), baseline)

    def test_settings_stay_unchanged_and_velocity_errors_are_detected(self):
        # Exercise the complete composition pipeline and its independent checker.
        script = '''
import contextlib
import copy
import io
from pathlib import Path
import config
import compose
import check
import mido

before = copy.deepcopy(config.INSTRUMENT_CONFIGS)
captured = []
original_verify = compose.verify

def capture(*args):
    captured.append(args)
    return original_verify(*args)

compose.verify = capture
with contextlib.redirect_stdout(io.StringIO()):
    compose.main()
assert config.INSTRUMENT_CONFIGS == before, "render mutated composition settings"
voices, periods, _, _, _, prefix, _ = captured[0]
assert all(v.accents and v.step_ticks > 0 for v in voices)

# A wrong early note must not be hidden by later notes in the same accent state.
path = Path(config.OUTPUT_DIR) / f"{prefix}_D_prime.mid"
original = path.read_bytes()
mid = mido.MidiFile(path)
first = next(m for m in mid.tracks[0] if m.type == 'note_on' and m.velocity)
first.velocity = 2
mid.save(path)
failures = []
check.check_every_velocity(lambda ok, message: failures.append(message) if not ok else None,
                           voices, periods, prefix)
assert failures and '1 note(s)' in failures[0], failures
path.write_bytes(original)

# Agreement between all voices is insufficient when they share a wrong table.
for voice in voices:
    path = Path(config.OUTPUT_DIR) / f"{prefix}_{voice.name}_prime.mid"
    mid = mido.MidiFile(path)
    for message in mid.tracks[0]:
        if message.type == 'note_on' and message.velocity:
            message.velocity = 64
    mid.save(path)
failures = []
check.check_every_velocity(lambda ok, message: failures.append(message) if not ok else None,
                           voices, periods, prefix)
assert failures and '328 note(s)' in failures[0], failures
'''
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = subprocess.run([sys.executable, '-B', '-c', script], cwd=root,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
