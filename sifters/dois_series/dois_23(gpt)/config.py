TITLE = 'dois_23(gpt)'
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
# PITCH — deliberately STATIC. One fixed note per voice, and it never moves.
# ---------------------------------------------------------------------------
# This version is for realising the piece on a Moog Grandmother, which cannot take
# pitch as a CV source. So pitch carries no information here: the sieve is expressed
# through RHYTHM and VELOCITY alone, which are what the instrument can act on.
#
# That is a narrowing of scope, not an abandonment. dois_15 through dois_19(gpt)
# derived pitch from the sieve four different ways, and all of it is kept — see
# CONTEXT.md, "Pitch work, parked". If pitch becomes playable again, that work is
# there to return to; nothing about the rhythm, accents or parity depends on it.
#
# Each voice gets its own note so the four parts stay separable in a DAW and can be
# routed independently — the Grandmother is monophonic, so it takes one at a time.
# The notes are consecutive from a base, as in dois_12: C1, C#1, D1, D#1. Transpose
# per track in the DAW; nothing in the structure depends on these numbers.
VOICE_PITCH_BASE = 36     # C1, and one semitone up per voice in INSTRUMENT_CONFIGS order

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('pitch', VOICE_PITCH_BASE + _i)
