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

STEP_TICKS_TO_DENOMINATOR = {
    1920: 1,
    960:  2,
    480:  4,
    240:  8,
    120:  16,
    60:   32,
}

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
        'root': 36,
    },
    {
        'name': 'B',
        'derives_from': 'A',
        'relationship': 'complement',
        'duration': 'Sixteenth Note',
        'root': 55,
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
        'root': 48,
    },
    {
        'name': 'D',
        'derives_from': ['A', 'C'],
        'relationship': 'intersection',
        'step_ticks': 160,
        'root': 60,
    },
]
