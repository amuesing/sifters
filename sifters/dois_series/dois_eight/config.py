TITLE = 'dois_eight'
import os as _os
OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mid')
TICKS_PER_QUARTER_NOTE = 480

DURATION_MULTIPLIER_KEY = {
    'Whole Note':        4,
    'Half Note':         2,
    'Quarter Note':      1,
    'Eighth Note':       0.5,
    'Sixteenth Note':    0.25,
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

# Four voices ordered by density (densest → sparsest):
#
#   sub      : complement of base  → 62.5%  — always-present sustained bass
#   texture  : union(base, canon9) → ~57.5% — dense mid-range layer
#   base     : raw sieve           → 37.5%  — the rhythmic foundation
#   ornament : intersection        → ~17.5% — sparse high ornament
#
# canon9 is a build-helper (render=False); it exists only to construct
# texture and ornament from the same sieve shifted by 9 steps.
INSTRUMENT_CONFIGS = [
    {
        'name': 'base',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
        'duration': 'Sixteenth Note',
        'root': 36,
        'flat_velocity': 80,
    },
    {
        'name': 'canon9',
        'derives_from': 'base',
        'relationship': 'shift',
        'shift_amount': 9,
        'render': False,
    },
    {
        'name': 'sub',
        'derives_from': 'base',
        'relationship': 'complement',
        'duration': 'Quarter Note',
        'root': 24,
        'flat_velocity': 55,
    },
    {
        'name': 'texture',
        'derives_from': ['base', 'canon9'],
        'relationship': 'union',
        'duration': 'Eighth Note',
        'root': 55,
        'flat_velocity': 68,
    },
    {
        'name': 'ornament',
        'derives_from': ['base', 'canon9'],
        'relationship': 'intersection',
        'duration': 'Thirty-Second Note',
        'root': 79,
        'flat_velocity': 100,
    },
]

# --- Ligeti-style dynamic density envelope ---------------------------------
# The sieve period is 40 steps.  Each step in the sieve becomes one section
# in the piece, so the total form IS the sieve — one step = one section.
# The piece ends when the sieve has expressed itself completely.
#
# At each section i the presence threshold is derived from the base sieve's
# own LOCAL DENSITY in a sliding window of ENVELOPE_WINDOW steps:
#
#   local_density_i  = mean(base_binary[i ± ENVELOPE_WINDOW/2])
#   threshold_i      = DENSITY_HIGH − (DENSITY_HIGH − DENSITY_LOW)
#                        × (local_density_i / max_local_density)
#
# Effect (analogous to Ligeti's density morphing in Atmospheres):
#   dense sieve zone  → low threshold  → more instruments enter
#   sparse sieve zone → high threshold → instruments drop away
#
# Because each instrument is tested against its OWN local density at section i
# (not the base's), the voices enter and exit in density order:
#   sub appears first, ornament last — in both directions.
#
# SECTION_REPETITIONS: sieve cycles per section.
# With multi-duration instruments the section LCM is 40 × 480 = 19 200 ticks.
# Total: 40 sections × 1 rep × 19 200 ticks = 768 000 ticks ≈ 13.3 min at 120 BPM.
ENVELOPE_WINDOW     = 8
DENSITY_HIGH        = 0.50   # threshold at the sieve's sparsest zones
DENSITY_LOW         = 0.05   # threshold at the sieve's densest zone
SECTION_REPETITIONS = 1
