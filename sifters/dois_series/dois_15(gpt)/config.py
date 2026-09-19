TITLE = 'dois_15(gpt)'
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
# Because gcd(8, 5) = 1, every step of the 40-step period has a UNIQUE address
# (step mod 8, step mod 5). The period is therefore not a line of 40 things but an
# 8 x 5 grid, and the sieve drawn on that grid is a shape: 8@3 and 8@4 are complete
# rows, (8@1&5@2) is a single cell. Pitch is read off that grid — one interval for
# moving a row, another for moving a column:
#
#     pitch = PITCH_ROOT + ( 5*(step mod 8) + 8*(step mod 5) )  mod  period
#
# The two intervals are the sieve's OWN moduli, exchanged: the mod-8 axis steps by 5
# semitones (a fourth), the mod-5 axis by 8 (a minor sixth). Nothing is chosen from
# outside the sieve.
#
# Counting 0,1,2,... walks DIAGONALLY across that grid — one row down and one column
# right at a time — so each step adds 5 + 8 = 13 semitones and folds back inside the
# period. That identity is exact:  5*(n mod 8) + 8*(n mod 5)  ==  13n  (mod 40), which
# is why the lattice and the multiplier are two descriptions of one operation, and why
# PITCH_MULTIPLIER below is 13 rather than an independent knob.
#
# The consequences, all asserted in verify() rather than assumed:
#   * gcd(multiplier, period) = 1, so the map is a BIJECTION — all 40 semitones are
#     reached before anything repeats, and residue classes map to residue classes, so
#     the pitch set is the rhythm sieve under a sieve-preserving transformation;
#   * the canon becomes an exact transposition. C is A shifted 13 steps, which on the
#     grid is 5 rows down and 3 columns right from wherever you start — always worth
#     5*5 + 8*3 = 49 = +9 semitones. The interval is not imposed; it falls out of the
#     displacement already in the piece. This is +9 MODULO 40; actual MIDI
#     differences are +9 or -31, not a constant octave-equivalent transposition.
#
# The period is the NOTE LAYER's period, so pitch states the sieve's periodicity in
# the same way duration does. It is derived at render time, never written here.
PITCH_ROOT = 36           # 40 MIDI pitches: 36 through 75, a 39-semitone span.
PITCH_ROW_INTERVAL = 5    # one step along the mod-8 axis: a perfect fourth
PITCH_COL_INTERVAL = 8    # one step along the mod-5 axis: a minor sixth

# ---------------------------------------------------------------------------
# Drum Rack pad assignment
# ---------------------------------------------------------------------------
# Retained only to give each voice a distinct MIDI CHANNEL in the merged file. With
# pitch derived, voices no longer own a pad, and two voices may legitimately sound the
# same pitch at the same tick (a unison). Separate channels keep that from reading as
# an overlapping note on one channel.
DRUM_RACK_BASE = 36

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('root', DRUM_RACK_BASE + _i)

# Comparison only: --pitch-mode moduli. Cycles per original parity span.
# A takes modulus 5, its complement B takes 8, C inherits A's rate.
# D uses gcd(5,8)=1 for a slow full-span traversal. Assignment is compositional.
PITCH_MODE = 'lattice'
PITCH_CYCLES = {'A': 5, 'B': 8, 'C': 5, 'D': 1}
