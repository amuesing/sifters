"""How long a note sounds: one step by default, or held until the voice's next attack.

ARTICULATION = 'held' (dois_43) makes the sieve's gaps into durations, for a sustained
patch whose envelopes and wavetable position need time to move.
"""
import sys
import tempfile
import unittest

from test_engine import PROJECT, project_copy, run, voice_track

UNITS = {'A': 120, 'B': 120, 'C': 120, 'D': 160}


class HeldNotes(unittest.TestCase):
    """ARTICULATION = 'held': the sieve's gaps become durations."""

    def test_every_note_lasts_until_its_voice_s_next_attack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            config = root / 'config.py'
            text = config.read_text()
            self.assertIn("ARTICULATION = 'step'", text)
            config.write_text(text.replace("ARTICULATION = 'step'", "ARTICULATION = 'held'"))
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr)
            self.assertNotIn('FAILED', result.stdout)
            for voice, unit in UNITS.items():
                track = voice_track(root / 'mid' / 'dois_47.mid', voice)
                onsets = [o for o, *_ in track]
                ends = onsets[1:] + [19200]
                for (onset, length, *_), end in zip(track, ends):
                    self.assertEqual(onset + length, end, (voice, onset))
            # B's gaps are 2 to 6 steps; its last note stops where its one-statement file
            # ends, so it is judged by the rule above, not by this set.
            b = voice_track(root / 'mid' / 'dois_47.mid', 'B')
            self.assertEqual({length // 120 for _, length, *_ in b[:-1]}, {2, 3, 4, 5, 6})

    def test_the_default_is_still_one_step(self):
        sys.path.insert(0, str(PROJECT))
        try:
            import config
            self.assertEqual(config.ARTICULATION, 'step')
            self.assertEqual(config.GATE_RATIO, 1.0)
        finally:
            sys.path.remove(str(PROJECT))


if __name__ == '__main__':
    unittest.main()
