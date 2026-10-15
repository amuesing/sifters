"""Tests for dois_21: same result as dois_20, and not tied to one sieve.

Two contracts:
  1. the output is note-for-note what dois_20 produced — the reorganisation changed
     how the code reads, not what it makes;
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
DOIS_20 = PROJECT.parent / 'dois_20' / 'mid'
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

    def test_output_is_note_for_note_dois_20(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            for f in FILES:
                self.assertEqual(notes(root / 'mid' / f'dois_21_{f}.mid'),
                                 notes(DOIS_20 / f'dois_20_{f}.mid'), f)

    def test_each_voice_sounds_one_static_pitch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            for voice, pitch in (('A', 36), ('B', 37), ('C', 38), ('D', 39)):
                (track,) = notes(root / 'mid' / f'dois_21_{voice}_prime.mid')
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


if __name__ == '__main__':
    unittest.main()
