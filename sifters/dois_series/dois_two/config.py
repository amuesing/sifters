TITLE = 'dois_two'
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

DURATION_TO_DENOMINATOR = {
    'Whole Note': 1,
    'Half Note': 2,
    'Quarter Note': 4,
    'Eighth Note': 8,
    'Sixteenth Note': 16,
    'Thirty-Second Note': 16  # This stays 16; your code handles halving numerator
}

INSTRUMENT_CONFIGS = [
    {
        # Percussive anchor: same sieve lineage and single-pitch behavior as
        # dois/psappha's "A" instrument. No chord_intervals -> root note only.
        'name': 'A',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
        'accent_dict': {
            'accent1': '((8@0|8@1|8@7)&(5@1|5@3))',
            'accent2': '((8@0|8@1|8@2)&5@0)',
            'accent3': '((8@5|8@6)&(5@2|5@3|5@4))'
        },
        'duration': 'Sixteenth Note',
        'root': 36,
        'apply_shift': True,
        'shift_direction': 'both'
    },
    {
        # Harmonic voice: same base sieve as dois/psappha's "B" instrument,
        # but the accent sieves are now three INDEPENDENT moduli (5, 8, and a
        # fresh 3 not used anywhere in the base sieve) rather than a disjoint
        # partition of the base sieve's own union clauses. The original
        # psappha/dois accent_dict assigns each hit to exactly one disjunct
        # by construction, so overlap count is always 1 -- nothing for chord
        # stacking to express. Independent moduli actually coincide sometimes,
        # so overlap count varies (0-3) and the chord below has something to
        # respond to: 1 accent active -> root; 2 -> root+minor third;
        # 3 -> minor triad.
        'name': 'B',
        'sieve': '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@6&5@1)|(8@3)|(8@4)|(8@1&5@2))',
        'accent_dict': {
            'low5': '5@0|5@1',
            'wide8': '8@0|8@1|8@2|8@5|8@6',
            'mod3': '3@0|3@1'
        },
        'duration': 'Sixteenth Note',
        'root': 60,
        'chord_intervals': {
            1: [0],
            2: [0, 3],
            3: [0, 3, 7],
        },
        'apply_shift': True,
        'shift_direction': 'both'
    },
]
