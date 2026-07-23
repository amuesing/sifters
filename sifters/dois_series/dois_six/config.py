TITLE = 'dois_six'
import os as _os
OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mid')
TICKS_PER_QUARTER_NOTE = 480

DURATION_MULTIPLIER_KEY = {
    'Whole Note': 4,
    'Half Note': 2,
    'Quarter Note': 1,
    'Eighth Note': 0.5,
    'Sixteenth Note': 0.25,
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

_ACCENT_DICT = {
    'low5':  '5@0|5@1',
    'wide8': '8@0|8@1|8@2|8@5|8@6',
    'mod3':  '3@0|3@1',
}

INSTRUMENT_CONFIGS = [
    {
        'name': 'base',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
        'accent_dict': _ACCENT_DICT,
        'duration': 'Sixteenth Note',
        'root': 36,
        'apply_shift': True,
        'shift_direction': 'both',
    },
    {
        'name': 'canon9',
        'derives_from': 'base',
        'relationship': 'shift',
        'shift_amount': 9,
        'render': False,
    },
    {
        'name': 'canon23',
        'derives_from': 'base',
        'relationship': 'shift',
        'shift_amount': 23,
        'render': False,
    },
    {
        'name': 'complement',
        'derives_from': 'base',
        'relationship': 'complement',
        'duration': 'Sixteenth Note',
        'root': 55,
        'flat_velocity': 64,
        'apply_shift': False,
    },
    {
        'name': 'union',
        'derives_from': ['base', 'canon9'],
        'relationship': 'union',
        'accent_dict': _ACCENT_DICT,
        'duration': 'Eighth Note',
        'root': 43,
        'apply_shift': False,
    },
    {
        'name': 'divergence',
        'derives_from': ['base', 'canon9'],
        'relationship': 'xor',
        'duration': 'Sixteenth Note',
        'root': 60,
        'flat_velocity': 80,
        'apply_shift': False,
    },
    {
        'name': 'convergence',
        'derives_from': ['base', 'canon9'],
        'relationship': 'intersection',
        'duration': 'Thirty-Second Note',
        'root': 72,
        'flat_velocity': 110,
        'apply_shift': False,
    },
    {
        'name': 'consensus',
        'derives_from': ['base', 'canon9', 'canon23'],
        'relationship': 'majority',
        'threshold': 2,
        'duration': 'Quarter Note',
        'root': 24,
        'flat_velocity': 70,
        'apply_shift': False,
    },
]

# --- Three-tier fractal form -------------------------------------------
# The same boolean sieve logic that governs which step fires at the note
# level (micro, period~40) is re-evaluated at two coarser scales:
#
#   meso  : z_range = NUM_SECTIONS_PER_MOVEMENT
#            which sections within a movement each instrument occupies
#
#   macro : z_range = NUM_MOVEMENTS
#            which movements each instrument is present across the piece
#
# All three levels are derived from INSTRUMENT_CONFIGS by a single
# function (build_presence_at_scale) — no separate form sieves are
# authored by hand.  Self-similarity is structural: the same operations
# (complement, union, xor, majority…) appear at every scale.
NUM_MOVEMENTS = 3
NUM_SECTIONS_PER_MOVEMENT = 5
