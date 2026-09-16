"""The complete published sieve and the chosen 4:3:2 realization.

Reference: Besada et al. (2021), doi:10.3389/fpsyg.2020.611316,
opening sieve S, including pulse 22. Reference math below does not call music21
or any planning/velocity helper. Readback checks all three MIDI representations.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

import mido

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('psappha_entry', PROJECT / 'composition.py')
entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
config, engine, midi = entry.components()
PUBLISHED = [0, 1, 3, 4, 6, 8, 10, 11, 12, 13, 14, 16, 17, 19, 20, 22, 23,
             25, 27, 28, 29, 31, 33, 35, 36, 37, 38]


def reference_layers():
    a = [int((n % 8 in (0, 1, 7) and n % 5 in (1, 3))
             or (n % 8 in (0, 1, 2) and n % 5 == 0)
             or (n % 8 in (5, 6) and n % 5 in (2, 3, 4))
             or n % 8 in (3, 4)
             or (n % 8 == 1 and n % 5 == 2)
             or (n % 8 == 6 and n % 5 == 1)) for n in range(40)]
    b = [1 - x for x in a]
    c = [a[(n - 13) % 40] for n in range(40)]
    return [a, b, c, [x & y for x, y in zip(b, c)]]


def reference_notes():
    # Common rarity ordering: none, weather8, weather5, span,
    # both weather, weather8+span, weather5+span, all.
    velocities = [1, 37, 19, 73, 55, 109, 91, 127]
    result = {}
    for name, pitch, layer, unit, modulus in zip('ABCD', range(36, 40), reference_layers(),
                                                (120, 120, 160, 240), (32, 32, 3, 16)):
        notes = []
        for i in range(19200 // unit):
            code = int(i % 5 in (1, 3)) + 2 * int(i % 8 in (0, 1, 2, 5, 6))
            code += 4 * int(i % modulus in tuple(r for r in (0, 1, 7) if r < modulus))
            if layer[i % 40]:
                notes.append((i * unit, unit, 0, pitch, velocities[code]))
        result[name] = notes
    return result


def decode(track):
    tick, active, notes = 0, {}, []
    for msg in track:
        tick += msg.time
        if msg.type == 'note_on' and msg.velocity:
            active[msg.channel, msg.note] = (tick, msg.velocity)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            start, velocity = active.pop((msg.channel, msg.note))
            notes.append((start, tick - start, msg.channel, msg.note, velocity))
    if active:
        raise AssertionError('Unreleased notes')
    return sorted(notes), tick


class FullPsapphaTests(unittest.TestCase):
    def setUp(self):
        self.settings = config.settings()
        self.plan = engine.build_plan(self.settings)

    def test_complete_source_matches_published_attacks(self):
        self.assertEqual([i for i, on in enumerate(reference_layers()[0]) if on], PUBLISHED)
        self.assertEqual([i for i, on in enumerate(self.plan.voices[0].layer) if on], PUBLISHED)
        self.assertEqual(sum(self.plan.voices[0].layer), 27)

    def test_all_voice_derivations_match_independent_math(self):
        for voice, expected in zip(self.plan.voices, reference_layers()):
            self.assertEqual(voice.layer, tuple(expected))
        self.assertEqual([i for i, on in enumerate(self.plan.voices[3].layer) if on], [2, 9, 21, 24, 26, 30, 32])

    def test_first_convergence_and_each_complete_pass(self):
        periods = [len(v.layer) * v.unit for v in self.plan.voices]
        self.assertEqual(periods, [4800, 4800, 6400, 9600])
        self.assertEqual(math.lcm(*periods), 19200)
        self.assertEqual(self.plan.parity, 19200)
        self.assertEqual([len(v.notes) for v in self.plan.voices], [108, 52, 81, 14])
        for voice, count in zip(self.plan.voices, (4, 4, 3, 2)):
            passes = [voice.velocities[i:i + 40] for i in range(0, len(voice.velocities), 40)]
            self.assertEqual(len(passes), count); self.assertEqual(len(set(passes)), count)
            # Exhaustively exclude all smaller divisors, without engine period helper.
            grid = voice.velocities
            self.assertFalse(any(len(grid) % d == 0 and all(x == grid[i % d] for i, x in enumerate(grid))
                                 for d in range(1, len(grid))))

    def test_ab_full_gate_tiles_time_without_collisions(self):
        notes = sorted(self.plan.voices[0].notes + self.plan.voices[1].notes)
        self.assertEqual([n.onset for n in notes], list(range(0, 19200, 120)))
        self.assertTrue(all(n.duration == 120 for n in notes))

    def test_one_fixed_weather_and_identical_state_table(self):
        self.assertEqual(self.settings['ACCENT_PHASE_POLICY'], 'fixed')
        self.assertEqual(self.settings['VELOCITY_POLICY'], 'shared_rarity')
        for v in self.plan.voices:
            self.assertEqual(v.phase, 0)
            self.assertEqual(v.accents[:2], tuple(self.settings['WEATHER'].items()))
            self.assertEqual(dict(v.levels), dict(enumerate([1, 37, 19, 73, 55, 109, 91, 127])))
        self.assertEqual([v.accents[-1][0] for v in self.plan.voices], ['span32', 'span32', 'span3', 'span16'])

    def test_all_notes_and_velocities_against_reference(self):
        expected = reference_notes()
        for voice in self.plan.voices:
            self.assertEqual([(n.onset, n.duration, n.channel, n.pitch, n.velocity) for n in voice.notes], expected[voice.name])
        self.assertEqual({n.velocity for v in self.plan.voices for n in v.notes}, {1, 19, 37, 55, 73, 91, 109, 127})

    def test_readback_of_all_six_files_against_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'mid'; midi.publish(self.plan, output)
            expected = reference_notes()
            for name in 'ABCD':
                notes, end = decode(mido.MidiFile(output / f'{self.plan.title}_{name}_prime.mid').tracks[0])
                self.assertEqual(notes, expected[name]); self.assertEqual(end, 19200)
            arrangement = mido.MidiFile(output / f'{self.plan.title}_arrangement.mid')
            for name, track in zip('ABCD', arrangement.tracks):
                notes, end = decode(track); self.assertEqual(notes, expected[name]); self.assertEqual(end, 19200)
            notes, end = decode(mido.MidiFile(output / f'{self.plan.title}_drumrack.mid').tracks[0])
            self.assertEqual(notes, sorted(n for voice in expected.values() for n in voice)); self.assertEqual(end, 19200)
            self.assertTrue(midi.verify_files(self.plan, output)); self.assertTrue(midi.verify_manifest(self.plan, output))

    def test_table_does_not_depend_on_voice_order_or_note_density(self):
        changed = copy.deepcopy(self.settings)
        changed['INSTRUMENT_CONFIGS'][3]['derives_from'] = ['A', 'C']
        other = engine.build_plan(changed)
        self.assertEqual([v.levels for v in other.voices], [v.levels for v in self.plan.voices])
        changed['INSTRUMENT_CONFIGS'][1], changed['INSTRUMENT_CONFIGS'][2] = changed['INSTRUMENT_CONFIGS'][2], changed['INSTRUMENT_CONFIGS'][1]
        reordered = engine.build_plan(changed)
        self.assertTrue(all(v.levels == self.plan.voices[0].levels for v in reordered.voices))

    def test_single_pass_without_accents_still_honors_unaccented_velocity(self):
        self.settings['WEATHER'] = {}
        self.settings['INSTRUMENT_CONFIGS'] = [
            {'name': 'A', 'sieve': '4@0', 'step_ticks': 120},
            {'name': 'B', 'derives_from': 'A', 'relationship': 'shift', 'shift_amount': 1, 'step_ticks': 240}]
        self.settings['UNACCENTED_VELOCITY'] = 42
        plan = engine.build_plan(self.settings)
        self.assertEqual(plan.voices[1].accents, ())
        self.assertEqual({n.velocity for n in plan.voices[1].notes}, {42})

    def test_diagnostics_identify_rates_and_all_realized_states(self):
        report = engine.diagnostics(self.plan)
        self.assertEqual(report['seconds'], 20)
        self.assertEqual([v['step_ticks'] for v in report['voices']], [120, 120, 160, 240])
        self.assertEqual([v['layer_attacks'] for v in report['voices']], [27, 13, 27, 7])
        self.assertEqual({state['code'] for v in report['voices'] for state in v['realized_states']}, set(range(8)))


if __name__ == '__main__':
    unittest.main()
