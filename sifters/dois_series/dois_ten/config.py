TITLE = 'dois_ten'
import os as _os
OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mid')
TICKS_PER_QUARTER_NOTE = 480

DURATION_MULTIPLIER_KEY = {
    'Whole Note':         4,
    'Half Note':          2,
    'Quarter Note':       1,
    'Eighth Note':        0.5,
    'Sixteenth Note':     0.25,
    'Thirty-Second Note': 0.125,
}

# Every generated file states the same meter and the same tempo, on every track,
# so no two outputs can disagree about them. 4/4 because it is the only meter all
# four voices can share: a triplet cycle cannot be expressed as any power-of-two
# meter (see CONTEXT.md), so a per-voice meter would have to differ by definition.
TIME_SIGNATURE = (4, 4)
TEMPO_BPM = 120

# Same four voices as dois_three — base sieve, complement, canon, polyrhythm.
# apply_shift removed: each instrument produces only its 40-step prime loop.
INSTRUMENT_CONFIGS = [
    {
        'name': 'A',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
        'accent_dict': {
            'low5':  '5@0|5@1',
            'wide8': '8@0|8@1|8@2|8@5|8@6',
            'mod3':  '3@0|3@1',
        },
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'B',
        'derives_from': 'A',
        'relationship': 'complement',
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'C',
        'derives_from': 'A',
        'relationship': 'shift',
        'shift_amount': 13,
        'accent_dict': {
            'low5':  '5@0|5@1',
            'wide8': '8@0|8@1|8@2|8@5|8@6',
            'mod3':  '3@0|3@1',
        },
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'D',
        'derives_from': ['A', 'C'],
        'relationship': 'intersection',
        'step_ticks': 160,
    },
]

# ---------------------------------------------------------------------------
# Drum Rack pad assignment
# ---------------------------------------------------------------------------
# Each voice plays one pad, derived from its position in INSTRUMENT_CONFIGS rather
# than written out per instrument. One pitch per voice, used by every output — the
# prime clips, the arrangement and the combined drum rack clip all agree by
# construction, so they cannot drift apart. Adding a fifth voice gets pad 5 for free.
# A voice may still pin its own pitch by setting 'root' explicitly above.
DRUM_RACK_BASE = 36  # C1 = Drum Rack pad 1

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('root', DRUM_RACK_BASE + _i)
