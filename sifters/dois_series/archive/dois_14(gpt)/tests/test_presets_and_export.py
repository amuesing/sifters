import copy
from dataclasses import astuple
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_full_psappha import config, engine, midi, entry, PROJECT


class PresetTests(unittest.TestCase):
    def test_reference_matches_claude_do_is_14_fixture(self):
        fixture = json.loads((PROJECT/'tests/fixtures/dois_14_notes.json').read_text())
        plan = engine.build_plan(config.settings('reference'))
        for voice in plan.voices:
            self.assertEqual([list(astuple(n)) for n in voice.notes], fixture[voice.name])

    def test_fixed_weather_changes_only_c_velocities(self):
        before = engine.build_plan(config.settings('reference'))
        after = engine.build_plan(config.settings('fixed-weather'))
        for a,b in zip(before.voices,after.voices):
            self.assertEqual([astuple(n)[:4] for n in a.notes], [astuple(n)[:4] for n in b.notes])
            if a.name != 'C': self.assertEqual(a.notes,b.notes)
            else: self.assertNotEqual(a.notes,b.notes)
            self.assertEqual(b.phase,0)

    def test_shared_weather_changes_only_d_velocities(self):
        before = engine.build_plan(config.settings('fixed-weather'))
        after = engine.build_plan(config.settings('shared-weather'))
        for a,b in zip(before.voices,after.voices):
            self.assertEqual([astuple(n)[:4] for n in a.notes], [astuple(n)[:4] for n in b.notes])
            if a.name != 'D': self.assertEqual(a.notes,b.notes)
            else: self.assertNotEqual(a.notes,b.notes)
            self.assertEqual(b.levels,after.voices[0].levels)

    def test_creative_keeps_ab_and_changes_only_cd(self):
        before=engine.build_plan(config.settings('shared-weather'))
        after=engine.build_plan(config.settings('creative'))
        for a,b in zip(before.voices[:2],after.voices[:2]): self.assertEqual(a.notes,b.notes)
        self.assertEqual([v.unit for v in after.voices],[120,120,160,240])
        self.assertEqual(after.voices[3].layer,tuple(b&c for b,c in zip(after.voices[1].layer,after.voices[2].layer)))

    def test_all_presets_have_distinct_passes_at_first_parity(self):
        for name in config.preset_names:
            with self.subTest(name=name):
                settings=config.settings(name);before=copy.deepcopy(settings)
                plan=engine.build_plan(settings);self.assertEqual(settings,before)
                self.assertEqual(plan.parity,19200)
                for voice in plan.voices: engine.validate_grid(voice.velocities,voice.layer,voice.name)
        with self.assertRaises(ValueError): config.settings('typo')


class OrdinaryExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'mid'
        self.plan=engine.build_plan(config.settings())

    def test_cli_all_presets_are_regular_and_verified(self):
        self.assertEqual(entry.main(['--all','--output-dir',str(self.out)]),0)
        self.assertEqual(len(list(self.out.rglob('*.mid'))),24)
        self.assertFalse(any(p.is_symlink() for p in self.out.rglob('*')))
        self.assertEqual(entry.main(['--all','--verify-only','--output-dir',str(self.out)]),0)
        self.assertEqual(entry.main(['--all','--dry-run','--output-dir',str(self.root/'dry')]),0)
        self.assertFalse((self.root/'dry').exists())
        self.assertEqual(list(self.root.glob('.midi-stage-*')),[])

    def test_existing_folder_and_foreign_files_preserved(self):
        self.out.mkdir();extra=self.out/'my-edit.mid';extra.write_bytes(b'keep')
        midi.publish(self.plan,self.out)
        before={p.name:p.read_bytes() for p in self.out.glob('*.mid')}
        midi.publish(self.plan,self.out)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.glob('*.mid')})
        self.assertEqual(extra.read_bytes(),b'keep');self.assertFalse(self.out.is_symlink())
        self.assertEqual(list(self.root.iterdir()),[self.out])

    def test_staging_failure_preserves_existing_output(self):
        midi.publish(self.plan,self.out)
        before={p.name:p.read_bytes() for p in self.out.iterdir()}
        for function in ('write_files','verify_files','verify_manifest'):
            with self.subTest(function=function),patch.object(midi,function,side_effect=ValueError('failure')):
                with self.assertRaises(ValueError):midi.publish(self.plan,self.out)
            self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.iterdir()})
        self.assertEqual(list(self.root.glob('.midi-stage-*')),[])

    def test_interrupted_replacement_detected_and_repaired_by_rerun(self):
        midi.publish(self.plan,self.out)
        s=config.settings();s['GATE_RATIO']=.5;changed=engine.build_plan(s)
        replace=midi.os.replace;calls=0
        def fail_after_one(source,destination):
            nonlocal calls
            calls+=1
            if calls==2:raise OSError('interrupted')
            return replace(source,destination)
        with patch.object(midi.os,'replace',side_effect=fail_after_one):
            with self.assertRaises(OSError):midi.publish(changed,self.out)
        with self.assertRaises(ValueError):midi.verify_files(changed,self.out)
        midi.publish(changed,self.out)
        self.assertTrue(midi.verify_files(changed,self.out));self.assertTrue(midi.verify_manifest(changed,self.out))

    def test_symlink_output_and_generated_filename_are_rejected(self):
        actual=self.root/'actual';actual.mkdir();self.out.symlink_to(actual,target_is_directory=True)
        with self.assertRaises(ValueError):midi.publish(self.plan,self.out)
        self.out.unlink();self.out.mkdir()
        valuable=self.root/'valuable';valuable.write_bytes(b'keep')
        (self.out/next(iter(midi.expected_files(self.plan)))).symlink_to(valuable)
        with self.assertRaises(ValueError):midi.publish(self.plan,self.out)
        self.assertEqual(valuable.read_bytes(),b'keep')

    def test_invalid_weather_rejected_without_replacing_files(self):
        midi.publish(self.plan,self.out)
        before={p.name:p.read_bytes() for p in self.out.iterdir()}
        s=config.settings();s['WEATHER']['foreign']='7@0|7@1'
        with self.assertRaisesRegex(ValueError,'not static'):engine.build_plan(s)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.iterdir()})


if __name__=='__main__':unittest.main()
