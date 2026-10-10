"""Composition settings. Read README.md for the musical meaning of each group."""
TITLE = 'dois_38'
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
# THE ACCENTS — derived from the sieve unless you name them here.
#
# Velocity is a property of the accent STATE, so these two settings are what the whole
# velocity profile is built from. Leaving both None means the profile is derived from
# the sieve itself, for any sieve:
#
#   WEATHER = None   one accent per modulus the sieve uses, firing on the residues that
#                    sieve FAVOURS — count the attacks landing on each residue of m and
#                    take the densest half. The sieve's own bias in that modulus, made
#                    audible. For the psappha sieve this derives mod5 = 5@1|5@3, which
#                    is exactly the accent every version up to dois_26 wrote by hand.
#                    From dois_35 there is a second requirement: every voice's attacks
#                    must meet every on/off combination of these accents, so that the
#                    WHOLE velocity profile can sound in every voice. Among the
#                    candidates that manage it, the densest wins. Taking the densest
#                    half blindly left B unable to reach two of the eight velocities.
#
#   SPAN_RESIDUE_SOURCE = None
#                    the residues are SEARCHED — sets of up to four residues below 16 —
#                    and scored, in this order: no two passes of any voice may be
#                    identical; every voice reaches every accent state its own rhythm
#                    can reach; and among the sets that do both, the one whose two most
#                    similar passes differ at the MOST steps wins. Ties go to the
#                    smaller set, then the lower residues, so the result is
#                    deterministic. If no set qualifies the run refuses and says so; it
#                    does not fall back. (Up to dois_28 it did take the first working
#                    set, which left two of B's passes differing at one step in forty.)
#
# Naming either one explicitly still works and is checked the same way — a composition
# choice, not a hard-coded requirement. Both are checked BEFORE anything is written:
# a weather that is not static within the note layer, or residues that leave two passes
# identical, refuse the run with your existing files untouched.
WEATHER = None

# The residues below are exactly what the search DERIVES for this sieve — pinned only
# so a render does not spend 37 seconds re-deriving them every time.
# `tests/test_derivation.py` runs the full search and fails if it no longer agrees.
#
# IF YOU CHANGE THE SIEVE, set this back to None. These residues belong to the psappha
# sieve; against another one they will either be refused by the preflight or silently
# be the wrong choice. `python3 compose.py --suggest-span` reports how a set is doing.
SPAN_RESIDUE_SOURCE = (0, 9, 10, 21, 31)

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

# SERUM WAVETABLES (dois_37, reworked in dois_38). Per voice, two tables:
#   _velocity.wav  128 frames, one per MIDI velocity: route Velocity -> WT Pos in Serum
#                  and each note's accent state chooses its timbre;
#   _sweep.wav     the voice's whole parity statement, one frame per step: ramp WT Pos
#                  from 0 to 1 across the clip and the timbre follows the accents in time.
# Derived: harmonic h sounds if h is in the voice's sieve, for exactly one period of it
# (40 harmonics here); accents lift the harmonics in their own sieves, by rarity.
WAVETABLES = True
WAVETABLE_SWEEP = True
WAVETABLE_FRAME_SAMPLES = 2048     # Serum's single-cycle frame length
# Choices, not derivations:
WAVETABLE_EMPHASIS = 3.0           # how strongly a firing accent lifts its harmonics;
                                   # 0 makes every frame the plain sieve
WAVETABLE_ROLLOFF = 1.0            # partials fall as 1/h ** this; 1 is a sawtooth's slope

VOICE_PITCH_BASE = 36     # static: C1, one semitone up per voice, in config order

PITCH_ROOT = 36           # lattice: MIDI 36–75; 40 positions spanning 39 semitones
# None derives the interval from the other lattice axis; integers override it.
PITCH_ROW_INTERVAL = None
PITCH_COL_INTERVAL = None

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('pitch', VOICE_PITCH_BASE + _i)
