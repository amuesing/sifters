TITLE = 'dois_12'
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

# How much of its step a note actually sounds for.
#
# A gate of exactly one step makes each note end on the tick the next one starts, so the
# note-off and the following note-on share a tick. That is legal MIDI and a one-shot drum
# sample ignores it, but a SUSTAINING synth patch frequently fails to re-articulate from a
# zero-length gap — consecutive notes are heard as one. In dois_12 that affected 91 pairs,
# including 56% of voice B's notes.
#
# The sieve says a sound occurs at that step; if the note does not re-articulate, the
# sound does not occur. So the gate is shortened to leave a real gap. This does not move
# any onset — the integers the sieve produces are untouched — it only shortens what
# sounds at each of them.
#
# 0.5 is a clean articulation that will retrigger on anything. Raise it toward 1.0 for a
# more legato reading if your patches retrigger reliably; a value of 1.0 restores the
# original behaviour and the problem with it.
GATE_RATIO = 0.5

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
#
# Both are drawn verbatim from the sieve, and both are STATIC: their moduli are the
# sieve's own, so they necessarily divide its period and land the same way on every
# pass. They colour the rhythm; they never vary it, and they never lengthen the piece.
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
# the derived modulus. sieve8 is clauses 2+3, so clause 1 is exactly the clause the
# weather omits — which is also what makes the span accent independent of sieve8 rather
# than a refinement of it. At modulus 32 that gives {0,1,7}; at modulus 3, {0,1}.
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
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
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
# Drum Rack pad assignment
# ---------------------------------------------------------------------------
DRUM_RACK_BASE = 36  # C1 = Drum Rack pad 1

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('root', DRUM_RACK_BASE + _i)
