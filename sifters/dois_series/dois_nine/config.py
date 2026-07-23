TITLE = 'dois_nine'
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

# Instruments are identical to dois_three.  Each adds a per-instrument
# presence_threshold that controls how densely it occupies the form:
#
#   B  (complement, 62.5% density) threshold 0.50 → near-constant ground
#   A  (base sieve, 37.5% density) threshold 0.30 → active ~60% of sections
#   C  (canon +13, 37.5% density)  threshold 0.30 → active ~50% of sections
#   D  (intersection, 15% density) threshold 0.15 → rare polyrhythmic cameo
#
# The sieve period is 40.  NUM_MOVEMENTS × NUM_SECTIONS_PER_MOVEMENT = 40
# so the piece ends on the sieve's own completion.
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
        'apply_shift': True,
        'shift_direction': 'both',
        'presence_threshold': 0.30,
    },
    {
        'name': 'B',
        'derives_from': 'A',
        'relationship': 'complement',
        'duration': 'Sixteenth Note',
        'root': 55,
        'presence_threshold': 0.50,
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
        'apply_shift': False,
        'presence_threshold': 0.30,
    },
    {
        'name': 'D',
        'derives_from': ['A', 'C'],
        'relationship': 'intersection',
        'step_ticks': 160,
        'root': 60,
        'apply_shift': False,
        'presence_threshold': 0.15,
    },
]

# --- Form ---------------------------------------------------------------
# Window-average downsampling: each instrument's micro binary is divided
# into z_range equal windows; a window is active when its mean density
# meets the instrument's presence_threshold.
#
# 5 movements × 8 sections = 40 = sieve period → intentional ending.
# SECTION_REPETITIONS: full ensemble cycles per section.
# Section LCM = lcm(A/B/C cycle, D cycle) = lcm(40×120, 40×160) = 19 200 ticks.
# Total: 5 × 8 × 2 × 19 200 = 1 536 000 ticks ≈ 26.7 min at 120 BPM.
NUM_MOVEMENTS             = 5
NUM_SECTIONS_PER_MOVEMENT = 8
SECTION_REPETITIONS       = 2
PRESENCE_THRESHOLD        = 0.30   # default; overridden per-instrument above
