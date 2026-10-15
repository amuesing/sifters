from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_full_psappha import config,engine,midi,entry

class BrowserExportTests(unittest.TestCase):
    def test_regular_files_update_and_preserve_extras(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'mid';dest=root/'mid-files'
            plan=engine.build_plan(config.settings());midi.publish(plan,source)
            midi.export_browser_files(plan,source,dest)
            self.assertFalse(dest.is_symlink())
            for name in midi.expected_files(plan):
                self.assertFalse((dest/name).is_symlink())
                self.assertEqual((dest/name).read_bytes(),(source/name).read_bytes())
            extra=dest/'my-edit.mid';extra.write_bytes(b'keep')
            s=config.settings();s['GATE_RATIO']=.5;changed=engine.build_plan(s)
            midi.publish(changed,source);midi.export_browser_files(changed,source,dest)
            self.assertTrue(midi.verify_files(changed,dest));self.assertEqual(extra.read_bytes(),b'keep')

    def test_bad_source_does_not_change_browser_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'mid';dest=root/'mid-files'
            plan=engine.build_plan(config.settings());midi.publish(plan,source)
            midi.export_browser_files(plan,source,dest)
            before={p.name:p.read_bytes() for p in dest.iterdir()}
            (source/next(iter(midi.expected_files(plan)))).write_bytes(b'bad')
            with self.assertRaises(ValueError):midi.export_browser_files(plan,source,dest)
            self.assertEqual(before,{p.name:p.read_bytes() for p in dest.iterdir()})

    def test_rejects_symlink_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'mid';dest=root/'mid-files'
            plan=engine.build_plan(config.settings());midi.publish(plan,source)
            dest.symlink_to(source,target_is_directory=True)
            with self.assertRaises(ValueError):midi.export_browser_files(plan,source,dest)

    def test_cli_exports_regular_folder_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.assertEqual(entry.main(['--output-dir',str(root/'mid')]),0)
            self.assertEqual(len(list((root/'mid-files').glob('*.mid'))),6)
            self.assertEqual(entry.main(['--dry-run','--output-dir',str(root/'dry')]),0)
            self.assertFalse((root/'dry-files').exists())
