TITLE = 'dois_18'
import os as _os
OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mid')
TICKS_PER_QUARTER_NOTE = 480

# Named durations, as a fraction of a quarter note. Looked up STRICTLY — an unknown
# name raises rather than silently yielding a sixteenth. There is deliberately no
# triplet entry: a triplet is not a power-of-two subdivision and cannot be named here,
# so a triplet voice states `step_ticks` directly. That absence is the point.
DURATION_MULTIPLIER_KEY = {
    'Whole Note':         4,
    'Half Note':          2,
    'Quarter Note':       1,
    'Eighth Note':        0.5,
    'Sixteenth Note':     0.25,
    'Thirty-Second Note': 0.125,
}

# The velocity range, used whole. MIN is 1, not 0: MIDI reads a note-on of velocity 0
# as a note-off, so 0 would delete the note rather than sound it faintly.
#
# The full range is used because velocity is NOT volume here — these parts drive
# software synths where velocity may be mapped to filter cutoff, envelope times, or
# sample layer. A low velocity is a different sound, not a quiet one.
MIN_VELOCITY = 1
MAX_VELOCITY = 127
UNACCENTED_VELOCITY = 64          # a voice with no accent layer at all

# How much of its step a note sounds for.
#
# 1.0 — a note fills its step, so each note-off lands on the tick the next note-on
# begins. This is the DEFAULT and the structurally truthful reading: A and B are
# complements, and only at a full gate do they tile time continuously between them,
# every tick of the cycle covered by exactly one of the pair.
#
# It is also consistent with how Ableton's own factory content is written — its clips
# hold notes for a fixed length that abuts the next at quarter-note spacing — and it
# plays correctly through samplers, which was verified: the same file that failed on a
# hardware synth articulates properly in Ableton with samples.
#
# The caveat, and why this is a knob rather than a constant: the MIDI specification
# leaves it to the DEVICE whether a Note On for a pitch already sounding retriggers or
# is absorbed. A zero-length gap is therefore legal but not guaranteed to re-articulate.
# Some hardware synths absorb it and consecutive notes are heard as one.
#
# If that happens, drop this to 0.5 — the classic analogue step-sequencer gate, the
# TB-303 convention — which leaves half of every step silent and will retrigger on
# anything. Ableton's Note Length MIDI effect is the other route: it overrides note
# durations per track at playback, leaving the file structurally intact.
GATE_RATIO = 1.0

TIME_SIGNATURE = (4, 4)           # fallback only, if no meter fits a period
MAX_METER_NUMERATOR = 99          # Ableton's limit
TEMPO_BPM = 120

# ---------------------------------------------------------------------------
# THE WEATHER — shared by every voice, without exception
# ---------------------------------------------------------------------------
# The accent field is not per-voice character. It is the weather the notes and rhythms
# fall under, and every voice falls under the same weather.
#
#   The psappha sieve, clause by clause:
#     clause 1   (8@0|8@1|8@7) & (5@1|5@3)      mod-8 {0,1,7}   mod-5 {1,3}
#     clause 2   (8@0|8@1|8@2) & 5@0            mod-8 {0,1,2}   mod-5 {0}
#     clause 3   (8@5|8@6) & (5@2|5@3|5@4)      mod-8 {5,6}     mod-5 {2,3,4}
#     clause 4   8@3                            mod-8 {3}       unconditioned
#     clause 5   8@4                            mod-8 {4}       unconditioned
#     clause 6   8@1 & 5@2                      mod-8 {1}       mod-5 {2}
#     clause 7   8@6 & 5@1                      mod-8 {6}       mod-5 {1}
#
# Both are drawn verbatim from clauses 1-3, and both are STATIC: their moduli are the
# sieve's own, so they necessarily divide its period and land the same way on every
# pass. They colour the rhythm; they never vary it, and they never lengthen the piece.
#
# NOTE, as an open question rather than a defect: clauses 4-7 arrived with the dois_14
# correction and the weather was deliberately NOT redesigned around them, so that the
# only difference from dois_12 is the sieve itself. One consequence is that mod-8
# residues 3 and 4 now carry notes but are named by neither the weather nor the span
# accent. Folding them in is a compositional decision, not a correction, and is left
# open.
WEATHER = {
    'sieve5': '5@1|5@3',                 # clause 1's mod-5, verbatim
    'sieve8': '8@0|8@1|8@2|8@5|8@6',     # clauses 2+3's mod-8, verbatim
}

# ---------------------------------------------------------------------------
# THE SPAN ACCENT — derived entirely, modulus AND residues
# ---------------------------------------------------------------------------
# Nothing here is chosen. PARITY is the first moment every voice converges on a common
# end point: P = LCM over voices of (note layer x basic unit). Reaching it forces each
# voice to restate its rhythm P / (layer x unit) times, and the span accent must be
# exactly long enough to inflect those restatements — no longer, or it over-runs the
# convergence and repeats something; no shorter, or a repetition goes unjustified.
#
#   required span (steps) = P / unit
#   required modulus      = the smallest M with LCM(layer, M) = that span
#
# dois_eleven hardcoded the answers for a 40-step layer (32 and 3). They are correct
# for that layer and silently wrong for any other — the last hand-picked numbers in the
# system. composition.py now computes them.
#
# The RESIDUES are derived too: clause 1's mod-8 residues, kept where they fall below
# the derived modulus. sieve8 is clauses 2+3, so clause 1 is a clause the weather omits
# — which is what makes the span accent independent of sieve8 rather than a refinement
# of it. (Since dois_14 it is no longer the ONLY omitted clause; see the note above.)
# What matters structurally is that {0,1,7} is not a subset of sieve8's {0,1,2,5,6} —
# residue 7 lies outside it — because a span accent contained by the weather would make
# accent states unreachable. At modulus 32 that gives {0,1,7}; at modulus 3, {0,1}.
SPAN_RESIDUE_SOURCE = (0, 1, 7)   # clause 1's mod-8 residues

# ---------------------------------------------------------------------------
# Voices — each derived from the base sieve, never independently authored
# ---------------------------------------------------------------------------
# Accent sets are NOT written here. They are assembled at render time from the weather
# plus the span accent the voice's unit requires, so a voice cannot be given accents of
# its own and cannot fall out of parity.
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

# ---------------------------------------------------------------------------
# PITCH — the sieve's own lattice, not a scale laid over it
# ---------------------------------------------------------------------------
# The base sieve is written in moduli 8 and 5. Because gcd(8, 5) = 1, every step of
# the 40-step period has a UNIQUE address (step mod 8, step mod 5), so the period is
# not a line of 40 things but an 8 x 5 grid, and the sieve drawn on that grid is a
# shape: 8@3 and 8@4 are complete rows, (8@1&5@2) is a single cell. Pitch is read off
# the grid — one interval for moving along each axis:
#
#     pitch = PITCH_ROOT + ( 5*(step mod 8) + 8*(step mod 5) )  mod  period
#
# The AXES are not written here. composition.py reads them from the base sieve's own
# moduli and refuses to render unless there are exactly two, coprime, whose product
# is the note-layer period — so the lattice cannot silently disagree with the sieve.
#
# The INTERVALS below are the sieve's moduli exchanged: the mod-8 axis steps by 5
# semitones, the mod-5 axis by 8. The numbers come from the sieve; the decision to use
# them this way — exchanged, read as semitones, folded into a 40-position space — is a
# compositional choice the source supports but does not mandate.
#
# Counting 0,1,2,... walks DIAGONALLY across the grid, so each step adds 5 + 8 = 13
# and folds inside the period. The identity  5*(n mod 8) + 8*(n mod 5) == 13n (mod 40)
# is exact: the lattice and multiplication by 13 are one operation, not two schemes.
#
# What that guarantees, each asserted at render time rather than assumed:
#   * It is MULTIPLICATION BY A UNIT mod 40 (gcd(13, 40) = 1). That is what carries
#     residue classes to residue classes — n = r (mod 8) always lands in one class
#     mod 8, likewise mod 5 — so the pitch set is the rhythm sieve under a
#     sieve-preserving transformation. Bijectivity alone would NOT give this: most
#     permutations of 40 things scatter a residue class. It is linearity that does.
#   * The +13-step canon is a transposition of +9 MODULO 40 — exact in the lattice,
#     NOT a constant audible interval. Across one cycle 23 of C's 27 notes rise 9
#     semitones from A's and 4 FALL 31, where the fold wraps. Since 40 is not a
#     multiple of 12 those four are not octave-equivalent either: pitch class moves
#     by 9 for 23 notes and by 5 for 4. verify() reports both, so the modular relation
#     and the audible one cannot be confused again (dois_15 conflated them).
#
# The period is the NOTE LAYER's period, so pitch states the sieve's periodicity in
# the same way duration does. It is derived at render time, never written here.
PITCH_ROOT = 36           # MIDI 36-75, C2 to D#5: 40 pitches spanning 39 semitones
PITCH_ROW_INTERVAL = 5    # one step along the mod-8 axis: a perfect fourth
PITCH_COL_INTERVAL = 8    # one step along the mod-5 axis: a minor sixth

# Voices no longer own a Drum Rack pad: pitch comes from the lattice. In the merged
# ensemble file each voice gets its own MIDI channel, in INSTRUMENT_CONFIGS order,
# because two voices may legitimately sound the same pitch at the same tick (a unison)
# and on one channel that would read as an overlapping note. dois_15's DRUM_RACK_BASE
# and per-voice 'root' did nothing after pitch was derived and have been removed.
