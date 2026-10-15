"""Composition settings. Read README.md for the musical meaning of each group."""
TITLE = 'dois_42'
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
#   SPAN_RESIDUES = None
#                    one residue set PER SPAN MODULUS (dois_42), derived from what the
#                    passes need. Pass k of a voice reads the accent at (k * layer + i) mod
#                    the modulus, so each layer step cycles through one block of positions,
#                    as many as there are passes. Making the passes differ as much as
#                    possible in total fills every block exactly halfway — the accent takes
#                    half its modulus, as the weather does. Among the half-full sets the
#                    winner keeps the closest passes furthest apart, then the next closest,
#                    and so on; ties go to the lowest residues. Exhaustive up to two million
#                    sets per modulus (1.7 million for 32, under a second); beyond that a
#                    local search that says so. Single-pass voices keep the search of
#                    dois_30-dois_41: the smallest set of up to five that completes the
#                    velocity profile. If no set qualifies the run refuses and says so.
#
# Naming either one explicitly still works and is checked the same way — a composition
# choice, not a hard-coded requirement. Both are checked BEFORE anything is written:
# a weather that is not static within the note layer, or residues that leave two passes
# identical, refuse the run with your existing files untouched.
WEATHER = None

# The residues below are exactly what the search DERIVES for this sieve — pinned so a
# render does not repeat the search. `tests/test_derivation.py` runs it and fails if it
# no longer agrees.
#
# IF YOU CHANGE THE SIEVE OR A BASIC UNIT, set this back to None. These belong to psappha
# at these units; against others they will be refused by the preflight or silently be
# the wrong choice. `python3 compose.py --suggest-span` reports how a set is doing.
SPAN_RESIDUES = {32: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 18, 20, 22, 27, 31), 3: (0,)}

# A is the source; B its complement; C its shift; D their intersection.
#
# C's shift is 'diagonal': the lattice's own diagonal, sum(P/m) over the sieve's moduli —
# 5 + 8 = 13 for psappha, the distance every version since dois_03 wrote by hand, and the
# multiplier the pitch lattice and the wavetables' frame order already use. A number
# still works; 'diagonal' just means the sieve chooses it.
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
        'shift_amount': 'diagonal',     # 13 for psappha
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

# SERUM WAVETABLES (dois_37; rebuilt in dois_40 and dois_41). Per voice, two tables:
#   _wavetable_A.wav        128 frames, one for every whole number 0-127. Frame i reads one
#                           period of the voice's sieve from i + 1 (as dois_40 did) and sounds
#                           it from just above its CUT c = 13 * i mod 40, the lattice's
#                           diagonal: harmonic c + h sounds when i + h is in the sieve. The
#                           reading gives 40 different frames, the cut gives each its own
#                           register. Route NOTE (pitch tracking off) or VELO to WT POS: each
#                           note or velocity lands exactly on its own frame.
#   _wavetable_A_sweep.wav  the parity statement, each step at its velocity's frame.
# Equal strength, one starting phase and one gain for the whole table, so frames differ in
# colour and register, never level. Harmonics stop at 79 (two periods).
WAVETABLES = True
WAVETABLE_SWEEP = True
WAVETABLE_FRAME_SAMPLES = 2048     # Serum's single-cycle frame length

# `python3 compose.py --install-serum` copies the tables into Serum's own Tables folder —
# found from Serum's preferences, not assumed — as `<SERUM_PROJECT>/<TITLE>`, e.g.
# Tables/sifters/dois_42: one sifters folder in Serum's menu, a folder per version inside.
# A plain render never writes outside the project.
SERUM_PROJECT = 'sifters'

VOICE_PITCH_BASE = 36     # static: C1, one semitone up per voice, in config order

PITCH_ROOT = 36           # lattice: MIDI 36–75; 40 positions spanning 39 semitones
# None derives the interval from the other lattice axis; integers override it.
PITCH_ROW_INTERVAL = None
PITCH_COL_INTERVAL = None

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('pitch', VOICE_PITCH_BASE + _i)
