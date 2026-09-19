"""Independent arithmetic and Claude MIDI fixture, not the writer's pitch helper."""
import contextlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import mido

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import composition as c


def decode(path):
    obj=mido.MidiFile(path);tracks=[]
    for track in obj.tracks:
        tick=0;active={};notes=[]
        for m in track:
            tick+=m.time
            if m.type=='note_on' and m.velocity:
                key=(m.channel,m.note)
                if key in active:raise AssertionError('overlapping note')
                active[key]=(tick,m.velocity)
            elif m.type=='note_off' or (m.type=='note_on' and not m.velocity):
                onset,vel=active.pop((m.channel,m.note))
                notes.append([onset,tick-onset,m.channel,m.note,vel])
        if active:raise AssertionError('hanging note')
        tracks.append((sorted(notes),tick))
    return obj,tracks


class LatticeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
        cls.out=Path(cls.temp.name)
        cls.fixture=json.loads((PROJECT/'tests/fixtures/claude15.json').read_text())
        for mode in ('lattice','moduli'):
            proc=subprocess.run([sys.executable,'-B',str(PROJECT/'composition.py'),'--pitch-mode',mode,
                                 '--output-dir',str(cls.out/mode)],capture_output=True,text=True)
            if proc.returncode:raise AssertionError(proc.stdout+proc.stderr)

    def test_all_twelve_files_match_independent_note_math(self):
        for mode in ('lattice','moduli'):
            expected={}
            for name,unit,cycles in zip('ABCD',(120,120,120,160),(5,8,5,1)):
                notes=[]
                for onset,duration,ch,pitch,vel in self.fixture[name]['notes']:
                    index=onset//unit if mode=='lattice' else onset//(19200//(40*cycles))
                    want=36+(13*index)%40
                    if mode=='lattice':self.assertEqual(want,pitch)
                    notes.append([onset,duration,0,want,vel])
                expected[name]=notes
            paths=list((self.out/mode).glob('*.mid'));self.assertEqual(len(paths),6)
            for path in paths:
                obj,tracks=decode(path);self.assertEqual(obj.ticks_per_beat,480)
                if path.name.endswith('_ensemble.mid'):
                    want=[sorted([n[0],n[1],ch,n[3],n[4]] for ch,name in enumerate('ABCD') for n in expected[name])]
                elif path.name.endswith('_arrangement.mid'):want=list(expected.values())
                else:want=[expected[path.name.split('_')[-2]]]
                self.assertEqual(len(tracks),len(want))
                for (actual,end),notes in zip(tracks,want):
                    self.assertEqual(actual,notes);self.assertEqual(end,19200)

    def test_baseline_partition_and_modular_canon(self):
        a={n[0]//120:n[3] for n in self.fixture['A']['notes'] if n[0]<4800}
        b={n[3] for n in self.fixture['B']['notes']}
        cv={n[0]//120:n[3] for n in self.fixture['C']['notes'] if n[0]<4800}
        self.assertFalse(set(a.values())&b);self.assertEqual(set(a.values())|b,set(range(36,76)))
        intervals=[cv[(i+13)%40]-p for i,p in a.items()]
        self.assertEqual(intervals.count(9),23);self.assertEqual(intervals.count(-31),4)
        self.assertTrue(all(d%40==9 for d in intervals))
        self.assertEqual(set(d%12 for d in intervals),{5,9})

    def test_bijection_and_lattice_multiplier_identity(self):
        self.assertEqual(c.check_pitch_lattice(40),13)
        self.assertEqual({c.lattice_pitch(i,40) for i in range(40)},set(range(36,76)))
        for i in range(-80,161):self.assertEqual(c.lattice_pitch(i,40),36+(13*i)%40)

    def test_invalid_lattice_and_range_rejected_before_publication(self):
        with self.assertRaises(ValueError):c.check_pitch_lattice(80)
        for key,value in [('PITCH_ROOT',89),('PITCH_ROOT',-1),('PITCH_ROOT',36.5),('PITCH_ROW_INTERVAL',6),('PITCH_COL_INTERVAL',True)]:
            with patch.object(c,key,value):
                with self.assertRaises(ValueError):c.check_pitch_lattice(40)
        with tempfile.TemporaryDirectory() as tmp, patch.object(c,'PITCH_ROOT',89):
            out=Path(tmp);marker=out/'dois_15(gpt)_A_prime.mid';marker.write_bytes(b'keep')
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(c.cli(['--output-dir',str(out)]),1)
            self.assertEqual(marker.read_bytes(),b'keep')

    def test_clock_boundaries_closure_and_first_parity(self):
        layers=dict.fromkeys('ABCD',40);units=dict(zip('ABCD',(120,120,120,160)))
        with patch.object(c,'PITCH_MODE','moduli'):
            c.check_pitch_clocks(layers,units,19200)
            for name,cycles in zip('ABCD',(5,8,5,1)):
                step=19200//(40*cycles)
                self.assertEqual(c.pitch_index(step-1,units[name],40,19200,name),0)
                self.assertEqual(c.pitch_index(step,units[name],40,19200,name),1)
                self.assertEqual(c.pitch_index(19200,units[name],40,19200,name),0)
                self.assertEqual(c.pitch_index(19200-1,units[name],40,19200,name),39)
            self.assertEqual(math.lcm(4800,6400,3840,2400,19200),19200)

    def test_invalid_clock_counts_and_fractional_ticks_rejected(self):
        for value in (0,-1,True,2.5,7):
            counts=dict(c.PITCH_CYCLES,A=value)
            with patch.object(c,'PITCH_MODE','moduli'),patch.object(c,'PITCH_CYCLES',counts):
                with self.assertRaises(ValueError):c.check_pitch_clocks(dict.fromkeys('ABCD',40),dict.fromkeys('ABCD',120),19200)

    def test_fingerprint_includes_pitch_gate_and_ignores_runtime_accents(self):
        before=c.config_fingerprint()
        for key,value in [('PITCH_ROOT',37),('PITCH_ROW_INTERVAL',10),('PITCH_COL_INTERVAL',16),('PITCH_MODE','moduli'),('GATE_RATIO',0.5),('PITCH_CYCLES',dict(c.PITCH_CYCLES,A=8))]:
            with patch.object(c,key,value):self.assertNotEqual(c.config_fingerprint(),before)
        configs=[dict(x,accent_dict={'generated':'32@0'}) for x in c.INSTRUMENT_CONFIGS]
        with patch.object(c,'INSTRUMENT_CONFIGS',configs):self.assertEqual(c.config_fingerprint(),before)

    def test_accented_passes_remain_distinct_both_modes(self):
        for mode in ('lattice','moduli'):
            for name,unit in zip('ABCD',(120,120,120,160)):
                path=next((self.out/mode).glob(f'*_{name}_prime.mid'))
                _,tracks=decode(path);grid=[0]*(19200//unit)
                for onset,duration,ch,pitch,vel in tracks[0][0]:grid[onset//unit]=vel
                passes=[tuple(grid[i:i+40]) for i in range(0,len(grid),40)]
                self.assertEqual(len(set(passes)),len(passes))
                for width in range(1,len(grid)):
                    if len(grid)%width==0:self.assertFalse(all(v==grid[i%width] for i,v in enumerate(grid)))

if __name__=='__main__':unittest.main()
