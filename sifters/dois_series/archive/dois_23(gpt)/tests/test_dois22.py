"""Tests for dois_23(gpt): one velocity table for every voice, and not tied to one sieve.

Two contracts:
  1. the only thing that changed from dois_21 is voice D's velocities — the shared
     table; no note moves, and A, B and C are untouched;
  2. a DIFFERENT sieve works. Each such test copies the project to a temporary folder,
     edits config.py there and runs it, which is exactly what you would do yourself.

Nothing here touches dois_21/mid.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mido

PROJECT = Path(__file__).resolve().parents[1]
PRIOR = PROJECT / 'tests' / 'fixtures' / 'dois_21'
FILES = ('A_prime', 'B_prime', 'C_prime', 'D_prime', 'arrangement', 'ensemble')
PSAPPHA = "'(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))'"
WEATHER = re.compile(r"WEATHER = \{.*?\n\}", re.S)


def notes(path):
    tracks = []
    for track in mido.MidiFile(path).tracks:
        t, sounding, out = 0, {}, []
        for msg in track:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                sounding[(msg.channel, msg.note)] = (t, msg.velocity)
            elif msg.type in ('note_on', 'note_off') and (msg.channel, msg.note) in sounding:
                onset, vel = sounding.pop((msg.channel, msg.note))
                out.append((onset, t - onset, msg.note, vel, msg.channel))
        tracks.append(sorted(out))
    return tracks


def run(cwd, *args):
    return subprocess.run([sys.executable, '-B', 'compose.py', *args],
                          cwd=cwd, capture_output=True, text=True)


def project_copy(tmp, sieve=None, weather=None, span=None):
    """A working copy of the project with config.py edited, as a user would edit it."""
    root = Path(tmp) / 'copy'
    shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns('mid', '__pycache__'))
    (root / 'mid').mkdir()
    text = (root / 'config.py').read_text()
    if sieve:
        start = text.index(PSAPPHA)
        end = text.index("',\n", text.index("'|8@3", start)) + 1
        text = text[:start] + repr(sieve) + text[end:]
    if weather:
        text = WEATHER.sub('WEATHER = ' + repr(weather), text, count=1)
    if span:
        text = re.sub(r'SPAN_RESIDUE_SOURCE = \([^)]*\)',
                      f'SPAN_RESIDUE_SOURCE = {span!r}', text, count=1)
    (root / 'config.py').write_text(text)
    return root


class SameResult(unittest.TestCase):

    def test_only_voice_d_velocities_changed_from_dois_21(self):
        """No note may move: same onsets, lengths, pitches, channels throughout."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            changed = {}
            for f in FILES:
                fresh = notes(root / 'mid' / f'dois_23(gpt)_{f}.mid')
                prior = notes(PRIOR / f'dois_21_{f}.mid')
                self.assertEqual([[(o, d, p, c) for o, d, p, _, c in tr] for tr in fresh],
                                 [[(o, d, p, c) for o, d, p, _, c in tr] for tr in prior], f)
                changed[f] = sum(a[3] != b[3] for tr_a, tr_b in zip(fresh, prior)
                                 for a, b in zip(tr_a, tr_b))
            self.assertEqual((changed['A_prime'], changed['B_prime'], changed['C_prime']),
                             (0, 0, 0))
            self.assertEqual(changed['D_prime'], 42)          # 42 of D's 60 notes

    def test_one_accent_state_means_one_velocity_everywhere(self):
        """Read from the files: every voice reaching a state gives it the same velocity."""
        weather5, weather8 = {1, 3}, {0, 1, 2, 5, 6}
        spans = {'A': (32, {0, 1, 7}), 'B': (32, {0, 1, 7}),
                 'C': (32, {0, 1, 7}), 'D': (3, {0, 1})}
        units = {'A': 120, 'B': 120, 'C': 120, 'D': 160}
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            table = {}
            for voice, unit in units.items():
                modulus, residues = spans[voice]
                (track,) = notes(root / 'mid' / f'dois_23(gpt)_{voice}_prime.mid')
                for onset, _, _, velocity, _ in track:
                    i = onset // unit
                    state = (i % 5 in weather5, i % 8 in weather8, i % modulus in residues)
                    table.setdefault(state, set()).add(velocity)
            clashes = {s: by for s, by in table.items() if len(by) > 1}
            self.assertEqual(clashes, {})
            self.assertIn('each meaning one velocity in every voice', result.stdout)

    def test_each_voice_sounds_one_static_pitch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            for voice, pitch in (('A', 36), ('B', 37), ('C', 38), ('D', 39)):
                (track,) = notes(root / 'mid' / f'dois_23(gpt)_{voice}_prime.mid')
                self.assertEqual({p for _, _, p, _, _ in track}, {pitch})


class AnotherSieve(unittest.TestCase):

    def test_a_different_sieve_renders_and_verifies(self):
        """Moduli 7 and 5 instead of 8 and 5: different period, parity and meter."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp,
                                sieve='(7@0|7@1|7@3)&(5@0|5@2|5@3)|7@5|5@1',
                                weather={'w5': '5@0|5@2|5@3', 'w7': '7@0|7@1|7@3'})
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout[-2500:] + result.stderr)
            self.assertIn('All checks passed', result.stdout)
            self.assertIn('P = LCM = 16800', result.stdout)      # its own parity
            self.assertIn('35/16', result.stdout)                # its own meter
            self.assertEqual(len(list((root / 'mid').glob('*.mid'))), 6)

    def test_a_sieve_the_span_accent_cannot_inflect_is_refused(self):
        """Nothing may be written when passes would come out identical."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, sieve='(4@0|4@1)&3@1|4@2',
                                weather={'w3': '3@0', 'w4': '4@1|4@2'})
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('leaves identical passes', result.stderr)
            self.assertIn('Nothing was written', result.stderr)
            self.assertEqual(list((root / 'mid').glob('*.mid')), [])

    def test_suggest_span_reports_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root, '--suggest-span')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('inflects every pass of every voice', result.stdout)
            self.assertEqual(list((root / 'mid').glob('*.mid')), [])


class VerifierRegressions(unittest.TestCase):

    def corrupted_render(self, root, mode):
        script = """import compose as c
real = c.accent_voicing
def corrupt(binary, bins, profile, pitch):
    notes, velocities = real(binary, bins, profile, pitch)
    if MODE == 'early':
        if pitch == c.INSTRUMENT_CONFIGS[-1]['pitch']:
            i = next(i for i,v in enumerate(velocities) if v)
            velocities[i] = 2 if velocities[i] != 2 else 3
    else:
        velocities[velocities > 0] = 64
    return notes, velocities
c.accent_voicing = corrupt
c.main()
""".replace('MODE', repr(mode))
        return subprocess.run([sys.executable, '-B', '-c', script], cwd=root,
                              capture_output=True, text=True)

    def test_early_wrong_velocity_cannot_be_hidden_by_later_correct_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = self.corrupted_render(root, 'early')
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('inconsistent velocities across occurrences', result.stdout)
            self.assertIn('1 note(s) violate the shared velocity table', result.stdout)
            self.assertNotIn('All checks passed', result.stdout)

    def test_consistently_wrong_velocity_is_not_a_valid_shared_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            # Directly call the verifier on genuine files, replacing the values it
            # reads, so accent preflight doesn't intercept the intentional corruption.
            script = """import compose as c, check as v
from midi import get_step_ticks
base,layers = c.derive_note_layers()
units={cfg['name']:get_step_ticks(cfg) for cfg in c.INSTRUMENT_CONFIGS}
parity=c.parity_point(layers,units)
for cfg in c.INSTRUMENT_CONFIGS:
    cfg['accent_dict']=c.accent_field(cfg,base,layers,units,parity)['accent_dict']
real=v.read_track
def wrong(path):
    notes,hanging,overlaps=real(path)
    return [(o,d,p,64) for o,d,p,vel in notes],hanging,overlaps
v.read_track=wrong
failures=[]
v.check_velocity_table_is_shared(lambda ok,msg: failures.append(msg) if not ok else None,
    [(cfg['name'],None,None,units[cfg['name']]) for cfg in c.INSTRUMENT_CONFIGS],
    {cfg['name']:parity for cfg in c.INSTRUMENT_CONFIGS})
assert any('violate the shared velocity table' in msg for msg in failures), failures
"""
            rendered=run(root)
            self.assertEqual(rendered.returncode,0,rendered.stderr)
            result=subprocess.run([sys.executable,'-B','-c',script],cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
