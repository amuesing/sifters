"""Independent pitch arithmetic and MIDI identity tests for the pitched iteration."""
from dataclasses import astuple, replace
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import mido

PROJECT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pitch_entry',PROJECT/'composition.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
config,engine,midi=entry.components()
POOL=[0,1,3,4,6,8,10,11,12,13,14,16,17,19,20,22,23,25,27,28,29,31,33,35,36,37,38]


def expected_pitch(name,step,span):
    if name=='A':return 48+POOL[(step%40)*27//40]
    if name=='B':return 48+POOL[26-(step%40)*27//40]
    if name=='C':return 48+POOL[((step-13)%40)*27//40]
    return 36+POOL[(step%span)*27//span]


def decode(track):
    tick=0;active={};notes=[]
    for msg in track:
        tick+=msg.time
        if msg.type=='note_on' and msg.velocity:
            key=(msg.channel,msg.note)
            if key in active:raise AssertionError('overlap')
            active[key]=(tick,msg.velocity)
        elif msg.type=='note_off' or (msg.type=='note_on' and not msg.velocity):
            onset,velocity=active.pop((msg.channel,msg.note))
            notes.append((onset,tick-onset,msg.channel,msg.note,velocity))
    if active:raise AssertionError('hanging')
    return sorted(notes),tick


class PitchTests(unittest.TestCase):
    def setUp(self):
        self.s=config.initial_pitch_settings();self.plan=engine.build_plan(self.s)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name)/'mid'

    def test_all_presets_preserve_parent_rhythm_velocity_and_gates(self):
        fixture=json.loads((PROJECT/'tests/fixtures/parent_rhythm_velocity.json').read_text())
        for preset in config.preset_names:
            plan=engine.build_plan(config.initial_pitch_settings(preset));self.assertEqual(plan.parity,19200)
            for voice in plan.voices:
                self.assertEqual([[n.onset,n.duration,n.velocity] for n in voice.notes],fixture[preset][voice.name])

    def test_complete_source_and_every_pitch_match_independent_reference(self):
        for preset in config.preset_names:
            plan=engine.build_plan(config.initial_pitch_settings(preset))
            self.assertEqual([i for i,on in enumerate(plan.voices[0].layer) if on],POOL)
            for channel,voice in enumerate(plan.voices):
                for n in voice.notes:
                    self.assertEqual(n.pitch,expected_pitch(voice.name,n.onset//voice.unit,len(voice.velocities)))
                    self.assertEqual(n.channel,channel)
                    self.assertIn(n.pitch-voice.pitch,POOL)

    def test_pitch_field_moves_during_rests(self):
        a=self.plan.voices[0]
        # This reference uses the absolute grid index, not the ordinal attack count.
        pitches=[n.pitch for n in a.notes[:27]]
        ordinal=[48+POOL[i] for i in range(27)]
        self.assertNotEqual(pitches,ordinal)
        self.assertEqual(len(a.pitch_cycle),40)

    def test_c_is_pitch_canon_even_under_fixed_weather(self):
        a,_,c,_=self.plan.voices
        self.assertEqual(c.phase,0)
        self.assertEqual(c.pitch_cycle,tuple(a.pitch_cycle[(i-13)%40] for i in range(40)))

    def test_d_slow_field_closes_at_first_parity(self):
        for preset in config.preset_names:
            d=engine.build_plan(config.initial_pitch_settings(preset)).voices[3]
            self.assertEqual(len(d.pitch_cycle)*d.unit,19200)
            self.assertEqual(engine.minimal_period(d.pitch_cycle),len(d.pitch_cycle))
            self.assertLess(d.pitch,min(v.pitch for v in self.plan.voices[:3]))

    def test_combined_period_and_pass_distinctness_are_measured(self):
        for v in self.plan.voices:
            grid=[None]*len(v.velocities)
            for n in v.notes:grid[n.onset//v.unit]=(n.pitch,n.velocity,n.duration)
            for d in range(1,len(grid)):
                if len(grid)%d==0:self.assertFalse(all(x==grid[i%d] for i,x in enumerate(grid)))
            passes=[tuple(grid[i:i+40]) for i in range(0,len(grid),40)]
            self.assertEqual(len(set(passes)),len(passes))

    def test_24_files_against_independent_pitch_math(self):
        for preset in config.preset_names:
            plan=engine.build_plan(config.initial_pitch_settings(preset));output=self.out/preset;midi.publish(plan,output)
            expected={v.name:[(n.onset,n.duration,i,expected_pitch(v.name,n.onset//v.unit,len(v.velocities)),n.velocity)
                              for n in v.notes] for i,v in enumerate(plan.voices)}
            self.assertEqual(len(list(output.glob('*.mid'))),6)
            self.assertFalse(any(p.is_symlink() for p in output.iterdir()))
            for path in output.glob('*.mid'):
                obj=mido.MidiFile(path);self.assertEqual(obj.ticks_per_beat,480)
                if path.name.endswith('_ensemble.mid'):want=[sorted(n for notes in expected.values() for n in notes)]
                elif path.name.endswith('_arrangement.mid'):want=list(expected.values())
                else:want=[expected[path.name.split('_')[-2]]]
                self.assertEqual(len(obj.tracks),len(want))
                for track,notes in zip(obj.tracks,want):
                    actual,end=decode(track);self.assertEqual(actual,notes);self.assertEqual(end,19200)
            self.assertTrue(midi.verify_manifest(plan,output));self.assertTrue(midi.verify_files(plan,output))

    def test_wrong_pitch_or_channel_rejected_in_every_output(self):
        for suffix in ('A_prime','arrangement','ensemble'):
            for field in ('note','channel'):
                midi.publish(self.plan,self.out)
                path=self.out/f'{self.plan.title}_{suffix}.mid';obj=mido.MidiFile(path)
                msg=next(m for m in obj.tracks[0] if m.type=='note_on')
                setattr(msg,field,getattr(msg,field)+1);obj.save(path)
                with self.assertRaises(ValueError):midi.verify_files(self.plan,self.out)

    def test_shared_pitches_on_separate_channels_are_safe(self):
        midi.publish(self.plan,self.out)
        notes,_=decode(mido.MidiFile(self.out/f'{self.plan.title}_ensemble.mid').tracks[0])
        self.assertEqual(len(notes),255)
        self.assertTrue(set(n.pitch for n in self.plan.voices[0].notes)&set(n.pitch for n in self.plan.voices[2].notes))
        self.assertEqual({n[2] for n in notes},{0,1,2,3})

    def test_pitch_out_of_range_rejected_without_output(self):
        self.s['PITCH_CONFIG']['A']['root']=100
        with self.assertRaisesRegex(ValueError,'exceeds MIDI'):engine.build_plan(self.s)
        self.assertFalse(self.out.exists())

    def test_pitch_config_unknown_missing_and_invalid_values_rejected(self):
        cases=[lambda s:s['PITCH_CONFIG']['A'].update(motion='random'),
               lambda s:s['PITCH_CONFIG']['A'].update(chanel=1),
               lambda s:s['PITCH_CONFIG'].pop('D'),
               lambda s:s['PITCH_CONFIG']['D'].update(channel=1),
               lambda s:s['PITCH_CONFIG']['D'].update(channel=10),
               lambda s:s['PITCH_CONFIG']['D'].update(root=36.5),
               lambda s:s['PITCH_CONFIG']['D'].update(motion='canon')]
        for change in cases:
            s=config.initial_pitch_settings();change(s)
            with self.assertRaises(ValueError):engine.build_plan(s)

    def test_pitch_settings_affect_fingerprint_and_input_is_immutable(self):
        before=copy.deepcopy(self.s);engine.build_plan(self.s);self.assertEqual(before,self.s)
        for key,value in [('root',49),('motion','descending'),('channel',5)]:
            s=config.initial_pitch_settings();s['PITCH_CONFIG']['A'][key]=value
            self.assertNotEqual(engine.build_plan(s).fingerprint,self.plan.fingerprint)

    def test_nonclosing_pitch_field_is_rejected(self):
        v=replace(self.plan.voices[0],pitch_cycle=self.plan.voices[0].pitch_cycle[:39])
        with self.assertRaisesRegex(ValueError,'does not close'):engine.validate_pitched_voice(v,19200)

    def test_pitch_does_not_license_repeated_velocity_passes(self):
        # Prior 15-hit source with fixed weather has identical C passes.
        self.s['INSTRUMENT_CONFIGS'][0]['sieve']='(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))'
        self.s['INSTRUMENT_CONFIGS'][2]['step_ticks']=120
        self.s['INSTRUMENT_CONFIGS'][3]['derives_from']=['A','C']
        self.s['INSTRUMENT_CONFIGS'][3].pop('duration');self.s['INSTRUMENT_CONFIGS'][3]['step_ticks']=160
        with self.assertRaisesRegex(ValueError,'repeated complete rhythm passes'):engine.build_plan(self.s)

    def test_manifest_contains_resolved_pitch_fields(self):
        midi.publish(self.plan,self.out);path=self.out/'render.json'
        data=json.loads(path.read_text())
        self.assertEqual(data['configuration']['PITCH_CONFIG'],self.s['PITCH_CONFIG'])
        self.assertEqual(data['voices'][0]['pitch_cycle'],list(self.plan.voices[0].pitch_cycle))
        data['voices'][0]['pitch_root']=99;path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):midi.verify_manifest(self.plan,self.out)

    def test_rhythm_guards_still_apply(self):
        for change in [lambda s:s.update(GATE_RATIO=0),lambda s:s.update(GATE_RATO=.5),
                       lambda s:s['WEATHER'].update(extra='7@0'),lambda s:s.update(MAX_STEPS=10),
                       lambda s:s['INSTRUMENT_CONFIGS'][2].update(shift_amount=40)]:
            s=config.initial_pitch_settings();change(s)
            with self.assertRaises(ValueError):engine.build_plan(s)

    def test_regular_exports_preserve_extras_and_staging_failure_preserves_files(self):
        self.out.mkdir();(self.out/'user.mid').write_bytes(b'keep');midi.publish(self.plan,self.out)
        before={p.name:p.read_bytes() for p in self.out.iterdir()}
        with patch.object(midi,'verify_files',side_effect=ValueError('injected')):
            with self.assertRaises(ValueError):midi.publish(self.plan,self.out)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.iterdir()})
        self.assertFalse(self.out.is_symlink())

    def test_cli_default_and_dry_run(self):
        self.assertEqual(entry.main(['--dry-run','--output-dir',str(self.out)]),0)
        self.assertFalse(self.out.exists())
        self.assertEqual(entry.main(['--output-dir',str(self.out)]),0)
        self.assertEqual(entry.main(['--verify-only','--output-dir',str(self.out)]),0)
        self.assertEqual(len(list((self.out/'creative').glob('*.mid'))),6)

if __name__=='__main__':unittest.main()
