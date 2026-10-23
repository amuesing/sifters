"""Tests for the engine: the piece as it was, and nothing tied to one sieve.

Two contracts:
  1. the MIDI is note-for-note the drumrack version, dois_23;
  2. a DIFFERENT sieve works. Each such test copies the project to a temporary folder,
     edits config.py there and runs it, which is exactly what you would do yourself.

Nothing here touches mid/.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mido

PROJECT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((PROJECT / 'tests/fixtures/dois_23_baseline.json').read_text())
PSAPPHA = "'(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))'"
# Both settings default to None, so these must match a None assignment as well as a
# written-out one. Until dois_31 they matched only the latter, `re.sub` returned the
# text unchanged, and every override below silently ran the default config instead.
WEATHER = re.compile(r"^WEATHER = (?:None|\{.*?\n\})", re.S | re.M)
SPAN = re.compile(r"^SPAN_RESIDUES = (?:None|\{[^\n]*\})", re.M)


OUTPUTS = ('mid', 'wavetables', 'presets')


def rendered(root):
    """Every rendered file, as {'folder/name': bytes}."""
    return {f"{kind}/{p.name}": p.read_bytes() for kind in OUTPUTS
            for p in sorted((Path(root) / kind).glob('*')) if p.is_file()}


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


def voice_track(path, voice):
    """One voice's notes from a set's file, found by its track's name."""
    names = [next((m.name for m in track if m.type == 'track_name'), None)
             for track in mido.MidiFile(path).tracks]
    return notes(path)[names.index(voice)]


# The snapshots in fixtures/ were taken when every set also had a file per voice and a
# one-track ensemble, copies of the four-track file then named `static_arrangement.mid`
# (and a pitched `lattice_` set, retired in dois_47). Today that file is `<title>.mid`;
# these compare it with its snapshot.
SNAPSHOT = 'static_arrangement.mid'


def snapshot(name):
    """A fixture's four-track static file, keyed as it was named then."""
    data = json.loads((PROJECT / 'tests/fixtures' / name).read_text())
    return {SNAPSHOT: data[SNAPSHOT]}


def set_notes(root):
    """Today's file, keyed as the snapshots name it, as JSON lists."""
    return json.loads(json.dumps({SNAPSHOT: notes(Path(root) / 'mid' / 'dois_47.mid')}))


def run(cwd, *args):
    return subprocess.run([sys.executable, '-B', 'compose.py', *args],
                          cwd=cwd, capture_output=True, text=True)


def project_copy(tmp, sieve=None, weather=None, span=None):
    """A working copy of the project with config.py edited, as a user would edit it.

    Every edit is read back out of the written file before the copy is handed over. A
    `re.sub` that matches nothing returns its input unchanged and raises nothing, so an
    override that stops matching turns the test that asked for it into a second run of
    the default config — passing, and testing something else. That is what happened
    between dois_27, where both settings became None, and dois_31.
    """
    root = Path(tmp) / 'copy'
    shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns(*OUTPUTS, '__pycache__',
                                                                 '.staging-*'))
    (root / 'mid').mkdir()
    text = (root / 'config.py').read_text()
    if sieve:
        start = text.index(PSAPPHA)
        end = text.index("',\n", text.index("'|8@3", start)) + 1
        text = text[:start] + repr(sieve) + text[end:]
    if weather:
        text = WEATHER.sub('WEATHER = ' + repr(weather), text, count=1)
    if span:
        text = SPAN.sub(f'SPAN_RESIDUES = {span!r}', text, count=1)
    elif sieve:
        # config pins the residues the search derives for the PSAPPHA sieve. Another
        # sieve has its own span modulus, so those residues are not its to use: put the
        # setting back to None and let this copy derive its own.
        text = SPAN.sub('SPAN_RESIDUES = None', text, count=1)
    (root / 'config.py').write_text(text)

    written = {}
    exec(compile(text, 'config.py', 'exec'), {'__file__': str(root / 'config.py')}, written)
    if sieve and not span and written['SPAN_RESIDUES'] is not None:
        raise AssertionError('a sieve override must leave the residues to be derived')
    for name, asked in (('WEATHER', weather), ('SPAN_RESIDUES', span)):
        if asked is not None and written[name] != asked:
            raise AssertionError(f'{name} was not applied: config says {written[name]!r}, '
                                 f'the test asked for {asked!r}')
    if sieve and written['INSTRUMENT_CONFIGS'][0]['sieve'] != sieve:
        raise AssertionError('the sieve was not applied')
    return root


class SameResult(unittest.TestCase):

    def test_the_midi_keeps_the_drumrack_rhythm_and_pitches(self):
        """Velocity now comes from the derived weather, so only notes are compared."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            # dois_23's four-track file, then named `_arrangement`, is today's set file.
            fresh = notes(root / 'mid' / 'dois_47.mid')
            prior = [[tuple(n) for n in tr] for tr in BASELINE['arrangement']['tracks']]
            self.assertEqual([[(o, d, p, c) for o, d, p, _, c in tr] for tr in fresh],
                             [[(o, d, p, c) for o, d, p, _, c in tr] for tr in prior])

    def test_the_weather_is_derived_from_the_sieve(self):
        """One accent per modulus, on the residues the sieve favours."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Weather (derived from the sieve): '
                          'mod8 = 8@1|8@3|8@4|8@5, mod5 = 5@1|5@3', result.stdout)
            # mod-5 comes out as the hand-written accent of every earlier version.
            # The residues are pinned in config from dois_34 (see test_derivation.py),
            # so what this asserts is the report, which is printed either way.
            self.assertIn('every voice at its ceiling', result.stdout)
            self.assertIn('differ at 8 steps', result.stdout)

    def test_every_voice_uses_every_velocity_state_it_can(self):
        """All states used, as far as each voice's rhythm allows. Evenness is not asked.

        B only lands on three of the four weather combinations, so two of the eight
        states can never sound in it; its ceiling is six, and it must reach six.
        """
        ceilings = {'A': 8, 'B': 8, 'C': 8, 'D': 8}
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            for voice, ceiling in ceilings.items():
                track = voice_track(root / 'mid' / 'dois_47.mid', voice)
                used = {v for _, _, _, v, _ in track}
                self.assertEqual(len(used), ceiling, f'{voice} used {sorted(used)}')
            self.assertIn('A 8/8, B 8/8, C 8/8, D 8/8', result.stdout)
            # 4 in dois_30, when the search stopped at four residues below 16; 6 once
            # dois_34 let it use five below the span accent's own modulus; 8 — B's limit
            # under one binary accent — once dois_42 filled every block halfway.
            self.assertIn('differ at 8 steps', result.stdout)

    def test_the_passes_are_made_as_different_as_the_residues_allow(self):
        """Distinct is not enough — the span accent should distinguish them strongly.

        dois_28 took the first qualifying residue set by number order and left two of
        B's passes differing at a single step out of forty. dois_30 onward maximises the
        weakest pair; dois_42 fills every block halfway, which maximises the total, and
        then maximises every pair from the weakest up. Per voice, measured: A 17-19 of
        its 27 attacks, B 8-9 of 13, C 18, D 12-15.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            units = {'A': 120, 'B': 120, 'C': 120, 'D': 160}
            for voice, unit in units.items():
                track = voice_track(root / 'mid' / 'dois_47.mid', voice)
                at = {o // unit: v for o, _, _, v, _ in track}
                span = max(at) + 1
                passes = [[at.get(i + 40 * p, 0) for i in range(40)]
                          for p in range((span + 39) // 40)]
                weakest = min(sum(1 for a, b in zip(x, y) if a != b)
                              for i, x in enumerate(passes) for y in passes[i + 1:])
                floor = {'A': 17, 'B': 8, 'C': 18, 'D': 12}[voice]
                self.assertGreaterEqual(weakest, floor, f'{voice} passes are too alike')

    def test_three_different_sieves_derive_everything(self):
        """Nothing hand-written: each sieve finds its own canon, weather, residues and meter.

        From dois_41 C's distance is the sieve's own lattice diagonal, so it changes with
        the sieve: 12 for 7 x 5, where it renders with every voice at 8/8, and 14 for
        11 x 3, where D = A & C becomes too sparse for any weather to give every voice the
        whole profile — refused with that reason, nothing written. (At the hand-written 13
        the 11 x 3 sieve rendered.)
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, sieve='(7@0|7@1|7@3)&(5@0|5@2|5@3)|7@5|5@1')
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout[-1500:] + result.stderr)
            self.assertIn('mod7 = 7@0|7@2|7@5, mod5 = 5@0|5@1', result.stdout)
            self.assertIn('35/16', result.stdout)
            self.assertIn('every voice at its ceiling', result.stdout)
            self.assertIn('registers 12 harmonics apart', result.stdout)
            self.assertEqual(len(list((root / 'mid').glob('*.mid'))), 1)
            a = voice_track(root / 'mid' / 'dois_47.mid', 'A')
            c = voice_track(root / 'mid' / 'dois_47.mid', 'C')
            a_steps = {o // 120 % 35 for o, *_ in a}
            c_steps = {o // 120 % 35 for o, *_ in c}
            self.assertEqual(c_steps, {(n + 12) % 35 for n in a_steps})      # the diagonal
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, sieve='(11@0|11@2|11@5|11@7)&(3@1|3@2)|11@9')
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('the whole velocity profile cannot sound in every voice', result.stderr)
            self.assertIn('Nothing was written', result.stderr)
            self.assertEqual(list((root / 'mid').glob('*.mid')), [])

    def test_each_voice_sounds_one_pitch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            for voice, pitch in (('A', 36), ('B', 37), ('C', 38), ('D', 39)):
                track = voice_track(root / 'mid' / 'dois_47.mid', voice)
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
            self.assertEqual(len(list((root / 'mid').glob('*.mid'))), 1)

    def test_a_sieve_that_cannot_have_distinct_passes_is_refused_with_the_count(self):
        """The refusal must PROVE it, not report a search that found nothing.

        D has one attack in its 12-step layer and must restate it three times to reach
        parity. Static weather marks that attack identically every pass, so only the
        binary span accent varies: two possible passes, three needed. ChatGPT's count,
        FOR_CLAUDE.md 2026-09-30. Up to dois_31 this said "no residues found", which
        does not distinguish a sieve that cannot work from a search that gave up.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, sieve='(4@0|4@1)&3@1|4@2',
                                weather={'w3': '3@0', 'w4': '4@1|4@2'})
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('no residue set can change that', result.stderr)
            self.assertIn('D: 1 attack(s) in a 12-step layer, restated 3x', result.stderr)
            self.assertIn('2**1 = 2', result.stderr)
            self.assertIn('First parity itself is fine', result.stderr)   # not (1)
            self.assertIn('COUNT, not a failed search', result.stderr)    # not (3)
            self.assertIn('Principle IV', result.stderr)
            self.assertEqual(list((root / 'mid').glob('*.mid')), [])

    def test_a_sieve_in_three_moduli_renders(self):
        """Refused until dois_46, whose pitch lattice needed exactly two moduli. 8, 5 and 3
        are pairwise coprime, so the lattice diagonal exists (79 mod 120) for C's shift,
        the frame order and the strike."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, sieve='(8@0|8@1)&(5@1|5@3)|3@0')
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout[-2500:] + result.stderr)
            self.assertIn('mod8 = 8@0|8@2|8@3|8@4, mod5 = 5@0|5@1, mod3 = 3@1', result.stdout)
            self.assertIn('All checks passed', result.stdout)
            self.assertIn('registers 79 harmonics apart', result.stdout)
            self.assertEqual(len(rendered(root)), 13)

    def test_a_pitch_midi_cannot_hold_stops_before_anything_is_written(self):
        """The notes are checked before the first file is written, so a bad one leaves
        the last render as it was."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            self.assertEqual(run(root).returncode, 0)
            before = rendered(root)
            self.assertEqual(len(before), 13)      # 1 MIDI, 8 wavetables, 4 presets
            text = (root / 'config.py').read_text()
            self.assertIn('VOICE_PITCH_BASE = 36', text)
            (root / 'config.py').write_text(text.replace('VOICE_PITCH_BASE = 36',
                                                         'VOICE_PITCH_BASE = 126'))
            result = run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('pitch must be a whole number in 0..127, got 128', result.stderr)
            self.assertNotIn('Saved', result.stdout)
            self.assertEqual(before, rendered(root))

    def test_suggest_span_reports_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root, '--suggest-span')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('every pass distinct', result.stdout)
            self.assertEqual(list((root / 'mid').glob('*.mid')), [])


class OneDerivedNumber(unittest.TestCase):
    """dois_41: the lattice's diagonal, derived once, drives the canon, the frame order and
    the drums' strike."""

    def setUp(self):
        sys.path.insert(0, str(PROJECT))
        self.addCleanup(sys.path.remove, str(PROJECT))
        import config
        import sieve
        self.config, self.sieve = config, sieve

    def test_the_diagonal_is_the_sum_of_the_exchanged_moduli(self):
        self.assertEqual(self.sieve.diagonal([8, 5]), 13)
        self.assertEqual(self.sieve.diagonal([7, 5]), 12)
        self.assertEqual(self.sieve.diagonal([3, 5, 7]), 71)     # 35 + 21 + 15
        self.assertIsNone(self.sieve.diagonal([4, 6]))            # no lattice

    def test_the_diagonal_is_what_the_lattice_multiplies_by(self):
        """sum((P/m)(n mod m)) == d*n mod P, for every n: the definition, checked."""
        for moduli in ([8, 5], [7, 5], [3, 5, 7], [11, 3]):
            period = 1
            for m in moduli:
                period *= m
            d = self.sieve.diagonal(moduli)
            for n in range(period):
                self.assertEqual(sum((period // m) * (n % m) for m in moduli) % period,
                                 (d * n) % period, (moduli, n))

    def test_c_is_shifted_by_the_diagonal(self):
        configs = self.config.INSTRUMENT_CONFIGS
        c = next(cfg for cfg in configs if cfg['name'] == 'C')
        self.assertEqual(c['shift_amount'], 'diagonal')
        self.assertEqual(self.sieve.shift_amount(c, configs), 13)
        self.assertEqual(self.sieve.shift_amount(dict(c, shift_amount=7), configs), 7)

    def test_augmentation_spaces_attacks_rather_than_repeating_them(self):
        """dois_40's augmentation was np.repeat: [1,0,1,1] by 2 gave six attacks, not three."""
        import numpy as np
        stretched = self.sieve.stretch_binary(np.array([1, 0, 1, 1]), 2)
        self.assertEqual(stretched.tolist(), [1, 0, 0, 0, 1, 0, 1, 0])
        self.assertEqual(int(stretched.sum()), 3)


class TheCommandLine(unittest.TestCase):

    def test_an_unknown_option_is_refused_and_nothing_written(self):
        """`--install` is the studies' spelling; here it once rendered and installed nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root, '--install')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown option(s) ['--install']", result.stderr)
            self.assertEqual(rendered(root), {})

    def test_the_same_piece_renders_the_same_bytes_in_any_folder(self):
        """The provenance stamp hashes settings, code and libraries, never the folder."""
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            first, second = project_copy(one), project_copy(Path(two) / 'elsewhere')
            self.assertEqual(run(first).returncode, 0)
            self.assertEqual(run(second).returncode, 0)
            self.assertEqual(rendered(first), rendered(second))

    def test_a_render_ends_with_what_to_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(project_copy(tmp))
            self.assertIn('1. drag mid/dois_47.mid in: one track per voice, A, B, C, D',
                          result.stdout)
            self.assertIn("('dois_47 A' ...), under User > sifters > dois_47", result.stdout)


if __name__ == '__main__':
    unittest.main()
