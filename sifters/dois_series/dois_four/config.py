TITLE = 'dois_four'
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
        # base — the source voice. Canonical psappha sieve (8/5 family).
        # 15 active steps in period 40.
        'name': 'base',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
        'accent_dict': _ACCENT_DICT,
        'duration': 'Sixteenth Note',
        'root': 36,
        'apply_shift': True,
        'shift_direction': 'both',
    },
    {
        # canon9 — helper only (render=False): base rotated by 9 steps. Not
        # its own MIDI file, just a building block for union/divergence/
        # convergence/consensus below.
        'name': 'canon9',
        'derives_from': 'base',
        'relationship': 'shift',
        'shift_amount': 9,
        'render': False,
    },
    {
        # canon23 — second helper: base rotated by 23 steps, used only by
        # consensus's vote.
        'name': 'canon23',
        'derives_from': 'base',
        'relationship': 'shift',
        'shift_amount': 23,
        'render': False,
    },
    {
        # complement — fills every step base doesn't, zero collisions.
        # 25 active steps. Same grid (Sixteenth Note) as base, since
        # complement only means something when both sides share a grid.
        'name': 'complement',
        'derives_from': 'base',
        'relationship': 'complement',
        'duration': 'Sixteenth Note',
        'root': 55,
        'flat_velocity': 64,
        'apply_shift': False,
    },
    {
        # union — union(base, canon9): a thickened, hocket-like merge of the
        # original and its own near-canon. 23 active steps. Slower duration
        # (Eighth Note) gives it a more sustained, padded character against
        # the busier sixteenth-note voices around it.
        'name': 'union',
        'derives_from': ['base', 'canon9'],
        'relationship': 'union',
        'accent_dict': _ACCENT_DICT,
        'duration': 'Eighth Note',
        'root': 43,
        'apply_shift': False,
    },
    {
        # divergence — xor(base, canon9): only the moments where exactly one
        # of base/canon9 plays, never both. 16 active steps. Same grid as
        # base/complement (Sixteenth Note).
        'name': 'divergence',
        'derives_from': ['base', 'canon9'],
        'relationship': 'xor',
        'duration': 'Sixteenth Note',
        'root': 60,
        'flat_velocity': 80,
        'apply_shift': False,
    },
    {
        # convergence — intersection(base, canon9): the rare moments (7 of
        # 40 steps) where base and its near-canon agree. Thirty-Second Note
        # duration turns each convergence point into a quick double-time
        # ornament rather than a sustained hit.
        'name': 'convergence',
        'derives_from': ['base', 'canon9'],
        'relationship': 'intersection',
        'duration': 'Thirty-Second Note',
        'root': 72,
        'flat_velocity': 110,
        'apply_shift': False,
    },
    {
        # consensus — majority([base, canon9, canon23], threshold=2): an
        # emergent voice that plays wherever at least 2 of the 3 rotations
        # agree (13 active steps) — a vote among independent perspectives on
        # the same source sieve, not derivable from any single one of them.
        # Quarter Note duration makes it the slowest, most grounded voice.
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
