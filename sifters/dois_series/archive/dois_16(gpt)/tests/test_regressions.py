"""Regression tests for GPT's 2026-09-19 review fixes."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
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
                onset,velocity=active.pop((msg.channel,msg.note))
                notes.append([onset,tick-onset,msg.channel,msg.note,velocity])
        if active:raise AssertionError('hanging note')
        tracks.append((sorted(notes),tick))
    return tracks


class RegressionTests(unittest.TestCase):
    def run_render(self,out,setup=''):
        script='import composition as c\nc.OUTPUT_DIR='+repr(str(out))+'\n'+setup+'\nc.main()\n'
        return subprocess.run([sys.executable,'-B','-c',script],cwd=PROJECT,capture_output=True,text=True)

    def test_default_all_six_files_preserve_claude_notes(self):
        fixture=json.loads((PROJECT/'tests/fixtures/claude15.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);result=self.run_render(out);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(len(list(out.glob('*.mid'))),6)
            for path in out.glob('*.mid'):
                if path.name.endswith('_ensemble.mid'):
                    expected=[sorted([o,d,ch,p,v] for ch,name in enumerate('ABCD') for o,d,_,p,v in fixture[name]['notes'])]
                elif path.name.endswith('_arrangement.mid'):expected=[fixture[name]['notes'] for name in 'ABCD']
                else:expected=[fixture[path.name.split('_')[-2]]['notes']]
                self.assertEqual(decode(path),[(notes,19200) for notes in expected])
            self.assertIn('heard +9 x23, -31 x4',result.stdout)

    def test_triplet_c_renders_and_reports_canon_in_local_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);result=self.run_render(out,"c.INSTRUMENT_CONFIGS[2].pop('duration')\nc.INSTRUMENT_CONFIGS[2]['step_ticks']=160")
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('heard +9 x23, -31 x4',result.stdout)
            notes,end=decode(out/'dois_16(gpt)_C_prime.mid')[0]
            self.assertEqual((len(notes),end),(81,19200))
            self.assertTrue(all(n[0]%160==0 for n in notes))

    def test_invalid_pitch_types_preserve_existing_files(self):
        for name,value in [('PITCH_ROOT',36.5),('PITCH_ROOT',True),('PITCH_ROW_INTERVAL',5.0),('PITCH_COL_INTERVAL',False)]:
            with self.subTest(name=name,value=value),tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)
                for suffix in ('A_prime','B_prime','C_prime','D_prime','arrangement','ensemble'):
                    (out/f'dois_16(gpt)_{suffix}.mid').write_bytes(b'previous content')
                before={p.name:p.read_bytes() for p in out.iterdir()}
                result=self.run_render(out,f'c.{name}={value!r}')
                self.assertNotEqual(result.returncode,0)
                self.assertIn(name+' must be an integer',result.stderr)
                self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})

    def test_missing_canon_attack_reports_validation_error(self):
        source=[(0,120,36,90),(120,120,49,90)]
        follower=[(13*160,160,45,90),(14*160,160,58,90)]
        self.assertEqual(c.canon_intervals(source,follower,120,160,40,13),[9,9])
        with self.assertRaisesRegex(ValueError,'missing or unexpected'):
            c.canon_intervals(source,follower[:1],120,160,40,13)
        with self.assertRaisesRegex(ValueError,'off-grid'):
            c.canon_intervals([(1,120,36,90)],follower,120,160,40,13)

if __name__=='__main__':unittest.main()
