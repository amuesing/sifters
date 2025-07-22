TITLE = 'sixty'
OUTPUT_DIR = f'sifters/{TITLE}/mid/'
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

# All Possible Modulo = 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60
# Modulo = 4,5,6
# Indices = 4:[0,1,2,3], 5:[0,1,2,3,4], 6:[0,1,2,3,4,5]

INSTRUMENT_CONFIGS = [
    {
        'name': 'A',
        # 'sieve': '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@6&5@1)|(8@3)|(8@4)|(8@1&5@2))',
        'sieve': '(((6@0|6@1|6@5)&(5@1|5@3))|((6@0|6@1|6@2)&5@0)|((6@5|6@5)&(5@2|5@3|5@4))|(6@5&5@1)|(6@3)|(6@4)|(6@1&5@2))',
        # 'sieve': '((4@1|4@3)&(5@0|5@2))|((4@0|4@2)&(5@1|5@3))',
        # 'sieve': '((10@0&12@2)|(10@1&12@3)|(10&2&12@0)|(10@3&12@1))',
        'accent_dict': {
        },
        'duration': 'Eighth Note',
        'note': 36,
        'apply_shift': True,
        'shift_direction': 'both'
    },
]