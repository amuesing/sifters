"""Structural checks independent of the pitch solver's chosen contour."""
from collections import Counter
from itertools import product
import json
from pathlib import Path
import unittest
from test_pitch import config,engine,midi,entry,decode,PROJECT
import tempfile
import mido

class GapPitchTests(unittest.TestCase):
    def test_signed_gaps_and_exact_closure_all_presets(self):
        fixture=json.loads((PROJECT/'tests/fixtures/parent_rhythm_velocity.json').read_text())
        for preset in config.preset_names:
            plan=engine.build_plan(config.settings(preset));self.assertEqual(plan.parity,19200)
            a,b,c,d=plan.voices
            for voice in plan.voices:
                self.assertEqual([[n.onset,n.duration,n.velocity] for n in voice.notes],fixture[preset][voice.name])
            for voice in (a,b):
                pos=[i for i,on in enumerate(voice.layer) if on]
                pitches=[voice.pitch_cycle[i] for i in pos]
                diffs=[pitches[(j+1)%len(pos)]-p for j,p in enumerate(pitches)]
                gaps=[(pos[(j+1)%len(pos)]-i)%40 for j,i in enumerate(pos)]
                self.assertEqual(list(map(abs,diffs)),gaps)
                self.assertEqual(sum(diffs),0)
                self.assertTrue(any(x>0 for x in diffs) and any(x<0 for x in diffs))
                self.assertEqual(pitches[0],voice.pitch+pos[0]%12)
                self.assertEqual(len(voice.pitch_cycle),40)
                # Independent subset formulation: upward gaps must total half the period.
                costs={0:0}
                for gap,i in zip(gaps,pos):
                    nxt={}
                    for up_total,cost in costs.items():
                        for up in (False,True):
                            key=up_total+gap*up;value=cost+(up!=bool(c.layer[i]))
                            nxt[key]=min(nxt.get(key,9999),value)
                    costs=nxt
                actual=sum((diff>0)!=bool(c.layer[i]) for diff,i in zip(diffs,pos))
                self.assertEqual(actual,costs[20])
                self.assertEqual(actual,voice.pitch_derivation['direction_reversals'])
            self.assertEqual(c.pitch_cycle,tuple(a.pitch_cycle[(i-13)%40] for i in range(40)))

    def test_anchor_classes_come_from_intersection_frequency(self):
        for preset in config.preset_names:
            d=engine.build_plan(config.settings(preset)).voices[3]
            pos=[i for i,on in enumerate(d.layer) if on];counts=Counter(i%12 for i in pos)
            ranked=sorted(counts,key=lambda pc:(-counts[pc],min(i for i in pos if i%12==pc)))
            for i,pitch in enumerate(d.pitch_cycle):
                self.assertEqual(pitch,d.pitch+ranked[(i//40)%len(ranked)])
            self.assertEqual(len(d.pitch_cycle)*d.unit,19200)

    def test_small_solver_matches_exhaustive_optimum_and_tie_break(self):
        layer=(1,1,0,1,0,0,1,0);direction=(0,1,0,0,0,0,1,0)
        cycle,trace=engine.gap_field(layer,direction,48)
        candidates=[]
        for flips in product((0,1),repeat=4):
            signs=[p*(1-2*f) for p,f in zip(trace['preferred_signs'],flips)]
            if sum(g*s for g,s in zip(trace['gaps'],signs))==0:
                candidates.append((sum(flips),flips))
        best=min(candidates)
        actual=tuple(int(a!=b) for a,b in zip(trace['signs'],trace['preferred_signs']))
        self.assertEqual((sum(actual),actual),best)

    def test_infeasible_closure_and_resource_limit_rejected(self):
        with self.assertRaisesRegex(ValueError,'cannot close'):engine.gap_field((1,0,0),(1,0,0),48)
        with self.assertRaisesRegex(ValueError,'512'):engine.gap_field((1,)*513,(1,)*513,48)

    def test_range_checks_actual_contour(self):
        s=config.settings();s['PITCH_CONFIG']['A']['root']=127
        with self.assertRaisesRegex(ValueError,'MIDI range'):engine.build_plan(s)
        s=config.settings();s['PITCH_CONFIG']['B']['root']=0
        plan=engine.build_plan(s)
        self.assertEqual(min(n.pitch for n in plan.voices[1].notes),1)

    def test_all_new_exports_decode_exactly_and_detect_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            for preset in config.preset_names:
                plan=engine.build_plan(config.settings(preset));out=Path(tmp)/preset;midi.publish(plan,out)
                expected={v.name:[(n.onset,n.duration,v.channel,n.pitch,n.velocity) for n in v.notes] for v in plan.voices}
                for path in out.glob('*.mid'):
                    obj=mido.MidiFile(path)
                    if path.name.endswith('_ensemble.mid'):want=[sorted(n for notes in expected.values() for n in notes)]
                    elif path.name.endswith('_arrangement.mid'):want=list(expected.values())
                    else:want=[expected[path.name.split('_')[-2]]]
                    self.assertEqual(len(obj.tracks),len(want))
                    for track,notes in zip(obj.tracks,want):self.assertEqual(decode(track),(notes,19200))
                self.assertTrue(midi.verify_manifest(plan,out))
                path=out/f'{plan.title}_ensemble.mid';obj=mido.MidiFile(path)
                next(m for m in obj.tracks[0] if m.type=='note_on').note+=1;obj.save(path)
                with self.assertRaises(ValueError):midi.verify_files(plan,out)

    def test_comparison_cli_keeps_outputs_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            self.assertEqual(entry.main(['--initial-pitch','--output-dir',str(out)]),0)
            self.assertEqual(entry.main(['--initial-pitch','--verify-only','--output-dir',str(out)]),0)
            self.assertTrue(list((out/'creative').glob('*_initial_*.mid')) or list((out/'creative').glob('*_initial.mid')))

if __name__=='__main__':unittest.main()
