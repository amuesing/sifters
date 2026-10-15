"""Regressions based on the original audit's concrete counterexamples."""
import copy
from dataclasses import astuple
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import mido
import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gpt_entry', PROJECT / 'composition.py')
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
config, engine, midi = entry.components()


def legacy_settings():
    """Historical 15-hit inputs are explicit; they are not the new musical default."""
    return json.loads((PROJECT / 'tests/fixtures/dois_12_settings.json').read_text())


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.settings = legacy_settings()
        self.plan = engine.build_plan(self.settings)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'mid'

    def render(self):
        midi.publish(self.plan, self.output)

    def change_midi(self, suffix, transform):
        path = self.output / f'{self.plan.title}_{suffix}.mid'
        obj = mido.MidiFile(path)
        transform(obj)
        obj.save(path)

    def hashes(self):
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.output.glob('*.mid')}

    def test_baseline_matches_independent_original_fixture(self):
        fixture = json.loads((PROJECT / 'tests/fixtures/dois_12_notes.json').read_text())
        self.render()
        self.assertEqual(self.plan.parity, 19200)
        self.assertEqual(self.plan.meter, (40, 16))
        for voice in self.plan.voices:
            self.assertEqual([list(astuple(n)) for n in voice.notes], fixture[voice.name])
        self.assertTrue(midi.verify_files(self.plan, self.output))
        self.assertTrue(midi.verify_manifest(self.plan, self.output))

    def test_plan_does_not_mutate_input(self):
        before = copy.deepcopy(self.settings)
        engine.build_plan(self.settings)
        self.assertEqual(self.settings, before)
        self.assertNotIn('root', config.INSTRUMENT_CONFIGS[0])

    def test_missing_final_pass_in_all_outputs_rejected(self):
        self.render()
        def remove(obj):
            for track in obj.tracks:
                tick = previous = 0; kept = []
                for msg in track:
                    tick += msg.time
                    if msg.type in ('note_on', 'note_off') and msg.note == 36 and (
                        msg.type == 'note_on' and tick >= 14400 or msg.type == 'note_off' and tick > 14400):
                        continue
                    kept.append(msg.copy(time=tick - previous)); previous = tick
                track[:] = kept
        for suffix in ('A_prime', 'arrangement', 'drumrack'):
            self.change_midi(suffix, remove)
        with self.assertRaisesRegex(ValueError, 'rendered notes differ'):
            midi.verify_files(self.plan, self.output)

    def test_duplicate_pass_in_all_outputs_rejected(self):
        self.render()
        def duplicate(obj):
            first = {}
            for track in obj.tracks:
                tick = 0
                for msg in track:
                    tick += msg.time
                    if msg.type == 'note_on' and msg.velocity and msg.note == 36:
                        if tick < 4800:
                            first[tick] = msg.velocity
                        elif tick >= 14400:
                            msg.velocity = first[tick % 4800]
        for suffix in ('A_prime', 'arrangement', 'drumrack'):
            self.change_midi(suffix, duplicate)
        with self.assertRaises(ValueError):
            midi.verify_files(self.plan, self.output)

    def test_wrong_release_channels_rejected(self):
        self.render()
        def corrupt(obj):
            for msg in obj.tracks[0]:
                if msg.type == 'note_off':
                    msg.channel = 1
        self.change_midi('drumrack', corrupt)
        with self.assertRaisesRegex(ValueError, 'orphan|hanging|overlapping'):
            midi.verify_files(self.plan, self.output)

    def test_ensemble_tempo_and_ppq_rejected(self):
        for corruption in ('tempo', 'ppq'):
            with self.subTest(corruption=corruption):
                self.render()
                def corrupt(obj):
                    if corruption == 'ppq':
                        obj.ticks_per_beat = 960
                    else:
                        for msg in obj.tracks[0]:
                            if msg.type == 'set_tempo':
                                msg.tempo = 1000000
                self.change_midi('drumrack', corrupt)
                with self.assertRaises(ValueError):
                    midi.verify_files(self.plan, self.output)

    def test_extra_pad_and_track_rejected(self):
        for corruption in ('pad', 'track'):
            with self.subTest(corruption=corruption):
                self.render()
                def corrupt(obj):
                    if corruption == 'track':
                        obj.tracks.append(obj.tracks[0].copy())
                    else:
                        obj.tracks[0].insert(4, mido.Message('note_on', note=99, velocity=64))
                        obj.tracks[0].insert(5, mido.Message('note_off', note=99, time=1))
                self.change_midi('drumrack', corrupt)
                with self.assertRaises(ValueError):
                    midi.verify_files(self.plan, self.output)

    def test_first_parity_overshoot_rejected_before_publication(self):
        self.render(); before = self.hashes(); link = os.readlink(self.output)
        self.settings['WEATHER']['foreign'] = '7@0|7@1'
        with self.assertRaisesRegex(ValueError, 'not static'):
            engine.build_plan(self.settings)
        self.assertEqual(self.hashes(), before)
        self.assertEqual(os.readlink(self.output), link)

    def test_augmentation_applied_once(self):
        source = np.array([1, 0, 0])
        result = engine.transformations.apply('augmentation', [source], {'factor': 2})
        self.assertEqual(result.tolist(), [1, 1, 0, 0, 0, 0])
        self.assertEqual(engine.tile(tuple(result), 12), (1, 1, 0, 0, 0, 0) * 2)
        # A complete feasible augmented composition, not just a shape test.
        self.settings['WEATHER'] = {}
        self.settings['SPAN_RESIDUE_SOURCE'] = (0,)
        self.settings['INSTRUMENT_CONFIGS'] = [
            {'name': 'A', 'sieve': '3@0', 'step_ticks': 120},
            {'name': 'B', 'derives_from': 'A', 'relationship': 'augmentation', 'factor': 2, 'step_ticks': 120},
        ]
        plan = engine.build_plan(self.settings)
        self.assertEqual(plan.parity, 720)
        self.assertEqual(plan.voices[1].layer, (1, 1, 0, 0, 0, 0))
        self.assertEqual(len(plan.voices[1].velocities), 6)
        midi.publish(plan, self.output)
        self.assertTrue(midi.verify_files(plan, self.output))

    def test_single_pass_trailing_rests_preserved(self):
        self.settings['WEATHER'] = {}
        self.settings['INSTRUMENT_CONFIGS'] = [{'name': 'A', 'sieve': '4@0', 'step_ticks': 120}]
        plan = engine.build_plan(self.settings)
        self.assertEqual(len(plan.voices[0].velocities), 4)
        self.assertEqual(plan.voices[0].velocities[1:], (0, 0, 0))
        midi.publish(plan, self.output)
        self.assertTrue(midi.verify_files(plan, self.output))

    def test_invalid_config_does_not_replace_previous_output(self):
        self.render(); before = self.hashes()
        cases = [('root', 128), ('step_ticks', 0), ('step_ticks', 120.5)]
        for key, value in cases:
            s = legacy_settings()
            if key == 'step_ticks':
                del s['INSTRUMENT_CONFIGS'][0]['duration']
            s['INSTRUMENT_CONFIGS'][0][key] = value
            with self.assertRaises(ValueError):
                engine.build_plan(s)
        for ratio in (-1, 0, 2, float('nan')):
            s = legacy_settings(); s['GATE_RATIO'] = ratio
            with self.assertRaises(ValueError):
                engine.build_plan(s)
        self.assertEqual(self.hashes(), before)

    def test_arity_names_pads_and_forward_refs_validated(self):
        for change in (
            lambda s: s['INSTRUMENT_CONFIGS'][1].update(derives_from=['A', 'C']),
            lambda s: s['INSTRUMENT_CONFIGS'][1].update(name='A'),
            lambda s: s['INSTRUMENT_CONFIGS'][1].update(root=36),
            lambda s: s['INSTRUMENT_CONFIGS'][1].update(derives_from='C'),
            lambda s: s['INSTRUMENT_CONFIGS'][2].update(shift_amount=40),
        ):
            s = legacy_settings(); change(s)
            with self.assertRaises(ValueError):
                engine.build_plan(s)

    def test_staging_write_and_verify_failures_preserve_previous_generation(self):
        self.render(); before = self.hashes(); link = os.readlink(self.output)
        for target in ('write_files', 'verify_files', 'verify_manifest'):
            with self.subTest(target=target), patch.object(midi, target, side_effect=ValueError('injected failure')):
                with self.assertRaises(ValueError):
                    midi.publish(self.plan, self.output)
            self.assertEqual(os.readlink(self.output), link)
            self.assertEqual(self.hashes(), before)

    def test_pointer_failure_preserves_previous_generation(self):
        self.render(); link = os.readlink(self.output); before = self.hashes()
        changed = legacy_settings(); changed['GATE_RATIO'] = .5
        self.plan = engine.build_plan(changed)
        with patch.object(midi.os, 'replace', side_effect=OSError('injected pointer failure')):
            with self.assertRaises(OSError):
                midi.publish(self.plan, self.output)
        self.assertEqual(os.readlink(self.output), link)
        self.assertEqual(self.hashes(), before)

    def test_foreign_files_and_prior_generation_survive(self):
        self.render(); previous = self.output.resolve()
        (self.output / 'my-edit.mid').write_bytes(b'user data')
        changed = legacy_settings(); changed['GATE_RATIO'] = .5
        self.plan = engine.build_plan(changed)
        self.render()
        self.assertTrue(previous.is_dir())
        self.assertNotEqual(self.output.resolve(), previous)
        self.assertEqual((self.output / 'my-edit.mid').read_bytes(), b'user data')

    def test_real_directory_is_not_overwritten(self):
        self.output.mkdir(); (self.output / 'valuable.txt').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'real directory'):
            self.render()
        self.assertEqual((self.output / 'valuable.txt').read_text(), 'keep')

    def test_changed_knobs_and_sources_change_fingerprint(self):
        baseline = engine.config_fingerprint(self.settings)
        for key, value in [('GATE_RATIO', .5), ('MIN_VELOCITY', 24), ('MAX_VELOCITY', 100),
                           ('MAX_METER_NUMERATOR', 39), ('METER_OVERRIDE', (4, 4)),
                           ('ACCENT_PHASE_POLICY', 'fixed')]:
            s = legacy_settings(); s[key] = value
            self.assertNotEqual(engine.config_fingerprint(s), baseline)
        s = legacy_settings(); s['INSTRUMENT_CONFIGS'][3]['derives_from'] = ['A', 'B']
        self.assertNotEqual(engine.config_fingerprint(s), baseline)

    def test_explicit_meter_override_and_gate(self):
        self.settings['METER_OVERRIDE'] = (4, 4); self.settings['GATE_RATIO'] = .5
        plan = engine.build_plan(self.settings)
        self.assertEqual(plan.meter, (4, 4)); self.assertEqual(plan.parity, 19200)
        self.assertEqual(plan.voices[0].notes[0].duration, 60)
        midi.publish(plan, self.output)
        self.assertTrue(midi.verify_files(plan, self.output))
        self.settings['METER_OVERRIDE'] = (3, 4)
        with self.assertRaises(ValueError):
            engine.build_plan(self.settings)

    def test_deterministic_midi_and_manifest_provenance(self):
        self.render(); before = self.hashes(); self.render()
        self.assertEqual(self.hashes(), before)
        data = json.loads((self.output / 'render.json').read_text())
        self.assertEqual(data['configuration_sha256'], self.plan.fingerprint)
        self.assertEqual(set(data['dependencies']), {'numpy', 'mido', 'music21'})
        self.assertIn('engine.py', data['engine_source_sha256'])

    def test_resource_limits_and_reducible_sieve(self):
        self.assertEqual(engine.sieve_layer('4@0|4@2', 100), (1, 0))
        self.settings['MAX_STEPS'] = 80
        with self.assertRaises(ValueError):
            engine.build_plan(self.settings)
        with self.assertRaises(ValueError):
            engine.sieve_layer('100003@0|100019@1', 100000)

    def test_concurrent_publisher_is_rejected(self):
        self.render(); before = os.readlink(self.output)
        with (self.root / '.mid-render.lock').open('a') as stream:
            midi.fcntl.flock(stream, midi.fcntl.LOCK_EX | midi.fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, 'Another render'):
                midi.publish(self.plan, self.output)
        self.assertEqual(os.readlink(self.output), before)

    def test_bare_config_module_cannot_contaminate_imports(self):
        with patch.dict(sys.modules, {'config': object(), 'transformations': object()}):
            own_config, own_engine, _ = entry.components()
            self.assertEqual(own_engine.build_plan(own_config.settings()).parity, 19200)

    def test_fixed_weather_policy_is_explicit(self):
        self.settings['ACCENT_PHASE_POLICY'] = 'fixed'
        # The original residue policy cannot distinguish C's passes when fixed.
        # Reject this change rather than quietly relaxing non-repetition.
        with self.assertRaisesRegex(ValueError, 'repeated complete rhythm passes'):
            engine.build_plan(self.settings)

    def test_unaccented_velocity_without_span_extension(self):
        self.settings['WEATHER'] = {}
        self.settings['SPAN_RESIDUE_SOURCE'] = (7,)
        self.settings['INSTRUMENT_CONFIGS'] = [{'name': 'A', 'sieve': '4@0', 'step_ticks': 120}]
        for velocity in (32, 64, 127):
            self.settings['UNACCENTED_VELOCITY'] = velocity
            plan = engine.build_plan(self.settings)
            self.assertEqual({n.velocity for n in plan.voices[0].notes}, {velocity})
            self.assertEqual(plan.voices[0].accents, ())
            midi.publish(plan, self.output)
            self.assertTrue(midi.verify_files(plan, self.output))

    def test_single_pass_keeps_weather_without_dummy_span(self):
        self.settings['WEATHER'] = {'weather': '4@0'}
        self.settings['INSTRUMENT_CONFIGS'] = [{'name': 'A', 'sieve': '4@0|4@1', 'step_ticks': 120}]
        plan = engine.build_plan(self.settings)
        self.assertEqual(plan.voices[0].accents, (('weather', '4@0'),))
        self.assertEqual([n.velocity for n in plan.voices[0].notes], [127, 1])

    def test_unknown_and_missing_settings_rejected(self):
        self.settings['GATE_RATO'] = .5
        with self.assertRaisesRegex(ValueError, 'GATE_RATO'):
            engine.build_plan(self.settings)
        del self.settings['GATE_RATO']; del self.settings['GATE_RATIO']
        with self.assertRaisesRegex(ValueError, 'GATE_RATIO'):
            engine.build_plan(self.settings)

    def test_manifest_all_provenance_fields_checked(self):
        self.render(); path = self.output / 'render.json'
        original = json.loads(path.read_text())
        for key, value in [('voices', []), ('engine_source_sha256', {}), ('engine_version', 'wrong'),
                           ('dependencies', {}), ('rendered_at_utc', 'yesterday')]:
            with self.subTest(key=key):
                changed = copy.deepcopy(original); changed[key] = value
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    midi.verify_manifest(self.plan, self.output)
        path.write_text(json.dumps(original)); self.assertTrue(midi.verify_manifest(self.plan, self.output))

    def test_identical_render_reuses_generation(self):
        self.render(); previous = self.output.resolve()
        (self.output / 'my-edit.mid').write_bytes(b'user data')
        manifest_bytes = (self.output / 'render.json').read_bytes()
        self.render()
        self.assertEqual(self.output.resolve(), previous)
        self.assertEqual(len(list((self.root / '.mid-renders').iterdir())), 1)
        self.assertEqual((self.output / 'render.json').read_bytes(), manifest_bytes)
        self.assertEqual((self.output / 'my-edit.mid').read_bytes(), b'user data')

    def test_identical_config_repairs_corrupt_generation(self):
        self.render(); previous = self.output.resolve()
        (self.output / f'{self.plan.title}_A_prime.mid').write_bytes(b'broken')
        self.render()
        self.assertNotEqual(self.output.resolve(), previous)
        self.assertTrue(midi.verify_files(self.plan, self.output))

    def test_diagnostics_counts_match_sounding_notes(self):
        report = engine.diagnostics(self.plan)
        for row, voice in zip(report['voices'], self.plan.voices):
            self.assertEqual(row['passes'], row['distinct_passes'])
            self.assertEqual(sum(row['velocity_histogram'].values()), len(voice.notes))
            self.assertEqual(sum(state['notes'] for state in row['realized_states']), len(voice.notes))
            self.assertTrue(all(state['velocity'] in [n.velocity for n in voice.notes]
                                for state in row['realized_states']))


if __name__ == '__main__':
    unittest.main()
