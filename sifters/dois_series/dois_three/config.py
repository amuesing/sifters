TITLE = 'dois_three'
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

# Maps step_ticks directly to the MIDI time_signature denominator value.
# Non-standard step sizes (e.g. triplet eighths = 160 ticks) fall back to 16
# in generate_time_signature since Ableton ignores embedded time signatures
# for session-view clips anyway.
STEP_TICKS_TO_DENOMINATOR = {
    1920: 1,
    960:  2,
    480:  4,
    240:  8,
    120:  16,
    60:   32,
}

INSTRUMENT_CONFIGS = [
    {
        # A — the base voice. Canonical psappha sieve (8/5 family).
        # 15 active steps in period 40. Three independent accent layers
        # (mod 5, 8, 3) produce 0/1/2/3-way overlaps for velocity variation.
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
    },
    {
        # B — complement of A. Plays exactly where A rests; together A and B
        # fill every sixteenth-note position with no gaps and no collisions.
        # 25 active steps (40 - 15 = 25). No accent layers — flat velocity.
        'name': 'B',
        'derives_from': 'A',
        'relationship': 'complement',
        'duration': 'Sixteenth Note',
        'root': 55,
        'apply_shift': False,
    },
    {
        # C — rhythmic canon of A, entering 13 steps later. Same accent layers
        # as A, rolled by 13 so the dynamic contour follows the shifted pattern.
        # Pitched a minor seventh above A (36 + 12 = 48, C3) so the two voices
        # are in the same harmonic space but registrally distinct.
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
    },
    {
        # D — intersection of A and C. Plays only at the 6 moments per cycle
        # where both the base voice and its canon agree simultaneously.
        # step_ticks=160 (triplet eighth notes) puts D in a 3:4 polyrhythm
        # against A/B/C (sixteenth notes = 120 ticks). They resync every
        # LCM(120, 160) = 480 ticks = one quarter note, but because D's cycle
        # is 6 * 160 = 960 ticks and A/B/C cycle is 40 * 120 = 4800 ticks,
        # the full ensemble realigns every LCM(960, 4800) = 4800 ticks.
        'name': 'D',
        'derives_from': ['A', 'C'],
        'relationship': 'intersection',
        'step_ticks': 160,
        'root': 60,
        'apply_shift': False,
    },
]
