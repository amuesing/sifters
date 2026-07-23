TITLE = 'dois_seven'
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

INSTRUMENT_CONFIGS = [
    {
        'name': 'base',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
        'duration': 'Sixteenth Note',
        'root': 36,
        'flat_velocity': 80,
    },
    {
        'name': 'complement',
        'derives_from': 'base',
        'relationship': 'complement',
        'duration': 'Sixteenth Note',
        'root': 60,
        'flat_velocity': 64,
    },
]

# --- Fractal form ----------------------------------------------------------
# The sieve's natural period is 40 steps.  NUM_MOVEMENTS × NUM_SECTIONS_PER_MOVEMENT
# is set equal to that period so the piece completes exactly one full
# traversal of the sieve at large scale — the ending is determined by the
# sieve's own closure, not by an arbitrary count.
#
# Meso and macro presence maps are produced by window-averaging the micro
# binary.  A window is active if its mean density >= PRESENCE_THRESHOLD.
# Lower values fill more of the form; higher values create more silence.
# Per-instrument override: add 'presence_threshold': 0.x to the config dict.
#
# SECTION_REPETITIONS: how many times each sieve cycle plays per section.
#
# Total duration (at 120 BPM):
#   5 × 8 × 4 × (40 × 120 ticks) / 480 ticks/beat / 120 beats/min ≈ 13.3 min
NUM_MOVEMENTS             = 5   # macro level
NUM_SECTIONS_PER_MOVEMENT = 8   # meso level  (5 × 8 = 40 = sieve period)
SECTION_REPETITIONS       = 4
PRESENCE_THRESHOLD        = 0.3
