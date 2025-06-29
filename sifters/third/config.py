TITLE = 'third'
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

INSTRUMENT_CONFIGS = [
    {
        'name': 'A',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
        'accent_dict': {
            'accent1': '((8@0|8@1|8@7)&(5@1|5@3))',
            'accent2': '((8@0|8@1|8@2)&5@0)',
            'accent3': '((8@5|8@6)&(5@2|5@3|5@4))'
        },
        'duration': 'Thirty-Second Note',
        'note': 36,
        'apply_shift': True,
        'shift_direction': 'both'
    },
    {
        'name': 'B',
        'sieve': '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@6&5@1)|(8@3)|(8@4)|(8@1&5@2))',
        'accent_dict': {
            'accent1': '((8@0|8@1|8@7)&(5@1|5@3))',
            'accent2': '((8@0|8@1|8@2)&5@0)',
            'accent3': '((8@5|8@6)&(5@2|5@3|5@4))',
            'accent4': '(8@6&5@1)',
            'accent5': '(8@3)',
            'accent6': '(8@4)',
            'accent7': '(8@1&5@2)'
        },
        'duration': 'Thirty-Second Note',
        'note': 36,
        'apply_shift': True,
        'shift_direction': 'both'
    },
    # {
    #     'name': 'C',
    #     'sieve': '(8@3)|(8@4)',
    #     'accent_dict': {
    #         'primary': '(8@3)',
    #         'ghost': '(8@4)'
    #     },
    #     'duration': 'Thirty-Second Note',
    #     'note': 36,
    #     'apply_shift': True,
    #     'shift_direction': 'both'
    # },
    # {
    #     'name': 'D',
    #     'sieve': '(8@1&5@2)',
    #     'accent_dict': {
    #         'primary': '5@2',
    #         'ghost': '8@1'
    #     },
    #     'duration': 'Thirty-Second Note',
    #     'note': 36,
    #     'apply_shift': True,
    #     'shift_direction': 'both'
    # },
    # {
    #     'name': 'E',
    #     'sieve': '(8@6&5@1)',
    #     'accent_dict': {
    #         'primary': '5@1',
    #         'ghost': '8@6'
    #     },
    #     'duration': 'Thirty-Second Note',
    #     'note': 36,  # C#1 - rim shot
    #     'apply_shift': True,
    #     'shift_direction': 'both'
    # },
]