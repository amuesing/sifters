"""Composition settings. Read README.md for the musical meaning of each group."""
TITLE = 'dois_26(gpt)'
import os as _os
OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mid')
TICKS_PER_QUARTER_NOTE = 480

# Named durations in quarter-note units; triplets use step_ticks.
DURATION_MULTIPLIER_KEY = {
    'Whole Note':         4,
    'Half Note':          2,
    'Quarter Note':       1,
    'Eighth Note':        0.5,
    'Sixteenth Note':     0.25,
    'Thirty-Second Note': 0.125,
}

# Velocity is a synth-control value. Zero would mean note-off.
MIN_VELOCITY = 1
MAX_VELOCITY = 127

# 1.0 fills each step. Adjust only if desired for instrument articulation.
GATE_RATIO = 1.0

TIME_SIGNATURE = (4, 4)           # fallback only, if no meter fits a period
MAX_METER_NUMERATOR = 99          # Ableton's limit
TEMPO_BPM = 120

# Shared accent sieves, sampled at each voice’s own step index.
WEATHER = {
    'sieve5': '5@1|5@3',                 # clause 1's mod-5, verbatim
    'sieve8': '8@0|8@1|8@2|8@5|8@6',     # clauses 2+3's mod-8, verbatim
}

# A compositional choice: residues retained below the derived span modulus.
SPAN_RESIDUE_SOURCE = (0, 1, 7)   # clause 1's mod-8 residues

# A is the source; B its complement; C its shift; D their intersection.
INSTRUMENT_CONFIGS = [
    {
        'name': 'A',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))'
                 '|8@3|8@4|(8@1&5@2)|(8@6&5@1)',
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'B',
        'derives_from': 'A',
        'relationship': 'complement',
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'C',
        'derives_from': 'A',
        'relationship': 'shift',
        'shift_amount': 13,
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'D',
        'derives_from': ['A', 'C'],
        'relationship': 'intersection',
        'step_ticks': 160,          # triplet 8th — no named duration can express it
    },
]

# Both modes share timing and velocities. Lattice requires two coprime moduli.
PITCH_MODES = ('static', 'lattice')

VOICE_PITCH_BASE = 36     # static: C1, one semitone up per voice, in config order

PITCH_ROOT = 36           # lattice: MIDI 36–75; 40 positions spanning 39 semitones
# None derives the interval from the other lattice axis; integers override it.
PITCH_ROW_INTERVAL = None
PITCH_COL_INTERVAL = None

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('pitch', VOICE_PITCH_BASE + _i)
