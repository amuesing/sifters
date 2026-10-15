"""Independent pitch-class arithmetic and unchanged-parent-stream regressions."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import mido

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
import composition as c


def decode(path):
    midi=mido.MidiFile(path);tracks=[]
    for track in midi.tracks:
        tick=0;active={};notes=[]
        for msg in track:
            tick+=msg.time
            if msg.type=='note_on' and msg.velocity:
                key=(msg.channel,msg.note)
                if key in active:raise AssertionError('overlap')
                active[key]=(tick,msg.velocity)
            elif msg.type=='note_off' or (msg.type=='note_on' and not msg.velocity):
                onset,vel=active.pop((msg.channel,msg.note))
                notes.append([onset,tick-onset,msg.channel,msg.note,vel])
        if active:raise AssertionError('hanging note')
        tracks.append((sorted(notes),tick))
    return tracks


def render(out,setup=''):
    return subprocess.run([sys.executable,'-B','-c',f'import composition as c\nc.OUTPUT_DIR={str(out)!r}\n{setup}\nc.main()'],cwd=PROJECT,capture_output=True,text=True)


class PitchClassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.out=Path(cls.tmp.name)
        cls.result=render(cls.out)
        if cls.result.returncode:raise AssertionError(cls.result.stdout+cls.result.stderr)
        cls.fixture=json.loads((PROJECT/'tests/fixtures/claude_baseline.json').read_text())

    def test_six_files_preserve_parent_streams_and_exact_pitch_formula(self):
        expected={}
        for name,unit in zip('ABCD',(120,120,120,160)):
            expected[name]=[[o,d,ch,36+3*((o//unit)%4),v] for o,d,ch,p,v in self.fixture[name]['notes']]
        paths=list(self.out.glob('*.mid'));self.assertEqual(len(paths),6)
        for p in paths:
            if p.name.endswith('_ensemble.mid'):
                want=[sorted([o,d,ch,pitch,v] for ch,name in enumerate('ABCD') for o,d,_,pitch,v in expected[name])]
            elif p.name.endswith('_arrangement.mid'):want=list(expected.values())
            else:want=[expected[p.name.split('_')[-2]]]
            self.assertEqual(decode(p),[(notes,19200) for notes in want])

    def test_maximal_image_and_axis_closure_are_derived(self):
        self.assertEqual(c.pitch_axis_intervals(),(3,0))
        self.assertEqual(c.check_pitch_lattice(dict.fromkeys('ABCD',40)),3)
        allowed=[(a,b) for a in range(12) for b in range(12) if 8*a%12==0 and 5*b%12==0]
        self.assertEqual(allowed,[(0,0),(3,0),(6,0),(9,0)])
        self.assertEqual({c.lattice_pitch(n,40)%12 for n in range(40)},{0,3,6,9})
        for n in range(-40,81):self.assertEqual(c.lattice_pitch(n,40),36+(3*n)%12)
        for x in range(40):
            for y in range(40):
                self.assertEqual((c.lattice_pitch(x,40)+c.lattice_pitch(y,40)-72)%12,
                                 (c.lattice_pitch((x+y)%40,40)-36)%12)

    def test_canon_is_three_semitones_modulo_twelve(self):
        notes={name:decode(self.out/f'{c.TITLE}_{name}_prime.mid')[0][0] for name in 'AC'}
        a={n[0]//120:n[3] for n in notes['A'] if n[0]<4800}
        cv={n[0]//120:n[3] for n in notes['C'] if n[0]<4800}
        intervals=[cv[(i+13)%40]-p for i,p in a.items()]
        self.assertEqual(intervals.count(3),20);self.assertEqual(intervals.count(-9),7)
        self.assertEqual({i%12 for i in intervals},{3})
        self.assertIn('+3 mod 12 (exact, as predicted)',self.result.stdout)

    def test_unequal_clock_canon(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=render(tmp,"c.INSTRUMENT_CONFIGS[2]['step_ticks']=160")
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('+3 mod 12 (exact, as predicted)',result.stdout)
            notes,end=decode(Path(tmp)/f'{c.TITLE}_C_prime.mid')[0]
            self.assertEqual((len(notes),end),(81,19200))

    def test_bad_root_rejected_before_replacing_real_midi(self):
        before={p.name:p.read_bytes() for p in self.out.iterdir()}
        for value in (36.5,True,-1,119):
            result=render(self.out,f'c.PITCH_ROOT={value!r}')
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.iterdir()})
        with patch.object(c,'PITCH_ROOT',118):c.check_pitch_lattice(dict.fromkeys('ABCD',40))

    def test_rhythm_accents_still_supply_full_period_and_distinct_passes(self):
        for name,unit in zip('ABCD',(120,120,120,160)):
            grid=[0]*(19200//unit)
            for o,d,ch,p,v in decode(self.out/f'{c.TITLE}_{name}_prime.mid')[0][0]:grid[o//unit]=v
            self.assertEqual(c.minimal_period(grid),len(grid))
            passes=[tuple(grid[i:i+40]) for i in range(0,len(grid),40)]
            self.assertEqual(len(set(passes)),len(passes))

    def test_wrong_written_pitch_is_detected(self):
        setup="real=c.lattice_pitch\ndef wrong(n,p):\n    return real(n,p)+1\nc.lattice_pitch=wrong"
        with tempfile.TemporaryDirectory() as tmp:
            result=render(tmp,setup)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Lattice and additive pitch-class forms disagree',result.stderr)
            self.assertFalse(list(Path(tmp).glob('*.mid')))

if __name__=='__main__':unittest.main()
