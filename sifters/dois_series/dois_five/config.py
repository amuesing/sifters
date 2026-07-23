TITLE = 'dois_five'
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

# --- Macro-form: a "sieve of sieves" -----------------------------------
# The same boolean sieve logic that decides which sixteenth note fires is
# applied again here, one level up, to decide which section each instrument
# is present in. NUM_SECTIONS is the Z-range each form sieve is evaluated
# over (section index 0..NUM_SECTIONS-1), exactly like period is the
# Z-range each instrument's rhythm sieve is evaluated over.
#
# The resulting shape is a deliberate build/breakdown arc:
#   0: base alone
#   1: + complement      (rhythm completes)
#   2: + union            (texture thickens)
#   3: + divergence        (tension rises)
#   4: + convergence        (climax ornaments appear)
#   5: + consensus            (full ensemble)
#   6: base + consensus only (drone outro, everything else drops out)
NUM_SECTIONS = 7

FORM_SIEVES = {
    'base':        '1@0',
    'complement':  '7@1|7@2|7@3|7@4|7@5',
    'union':       '7@2|7@3|7@4|7@5',
    'divergence':  '7@3|7@4|7@5',
    'convergence': '7@4|7@5',
    'consensus':   '7@5|7@6',
}
