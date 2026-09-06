TITLE = 'dois_eleven'
import os as _os
OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mid')
TICKS_PER_QUARTER_NOTE = 480

# Named durations, as a fraction of a quarter note. Looked up STRICTLY — an unknown
# name raises rather than silently yielding a sixteenth. Note there is deliberately no
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

# The velocity range, used whole.
#
# MIN_VELOCITY is 1 rather than 0 because MIDI defines a note-on of velocity 0 as a
# note-off: velocity 0 would delete the note, not sound it faintly. 1 is the quietest a
# note can be and still exist.
#
# The full range is used because **velocity is not volume here**. These parts drive
# software synths where velocity is mapped to filter cutoff, envelope times, sample
# layer, or anything else the patch calls for. A low velocity is therefore not a quiet
# note that might go unheard — it is a different sound. That makes the whole range
# meaningful and small differences worth keeping, which is why levels are packed as
# tightly as the range allows rather than spread for audibility.
MIN_VELOCITY = 1
MAX_VELOCITY = 127

# A voice with no accent layer at all has no dynamic information to convey.
UNACCENTED_VELOCITY = 64

# Fallback meter, used only if no meter can put a bar line on a voice's period.
TIME_SIGNATURE = (4, 4)

# Ableton accepts time-signature numerators up to 99.
MAX_METER_NUMERATOR = 99
TEMPO_BPM = 120

# NOTE: the note layer's period is NOT declared here. It is derived from the base
# sieve at runtime (LCM of its moduli), because declaring it would duplicate a fact
# the sieve already states — and the two could then disagree silently.

# ---------------------------------------------------------------------------
# Accent sieves
# ---------------------------------------------------------------------------
# Three accents are shared by every voice. The fourth is the PARITY accent: its
# modulus is chosen so a voice's period in TICKS matches the others' despite the
# different basic units.
#
# Identical accent sets cannot give parity across different units — the accent moduli
# must scale INVERSELY to the basic unit:
#
#   16th voices  (unit 120): LCM(40, 5, 8, 3, 32) = 480 steps x 120 = 57600 ticks
#   triplet voice (unit 160): LCM(40, 5, 8, 3,  9) = 360 steps x 160 = 57600 ticks
#   480 / 360 = 4/3 = 160 / 120   <- the step counts invert the unit ratio exactly
#
# Parity depends only on the MODULI. Residues are free artistic choice — but they must
# be irreducible. `32@0|32@1|32@16|32@17` looks like modulus 32 and is really modulus
# 16, which would halve the period. music21's Sieve.period() reports the nominal
# modulus and will not catch it; composition.py measures the true period instead and
# refuses to run if the two disagree.
# ---------------------------------------------------------------------------
# THE WEATHER — shared by every voice, without exception
# ---------------------------------------------------------------------------
# The accent field is not per-voice character. It is the weather the notes and rhythms
# fall under, and every voice falls under the same weather.
#
# It also LICENSES REPETITION. Parity forces a voice to restate its note layer — D nine
# times, A twelve. Bare that would be literal repetition. Because these moduli do not all
# divide the note-layer period, each pass is inflected differently: the rhythm recurs
# while the music never does.
#
#   The psappha sieve, clause by clause:
#     clause 1   (8@0|8@1|8@7) & (5@1|5@3)      mod-8 {0,1,7}   mod-5 {1,3}
#     clause 2   (8@0|8@1|8@2) & 5@0            mod-8 {0,1,2}   mod-5 {0}
#     clause 3   (8@5|8@6) & (5@2|5@3|5@4)      mod-8 {5,6}     mod-5 {2,3,4}
#
# Note which accents actually move. A modulus that DIVIDES the 40-step note layer
# repeats identically on every pass — it colours the rhythm but never varies it:
#
#     sieve5  mod 5   divides 40   STATIC — fixed colour
#     sieve8  mod 8   divides 40   STATIC — fixed colour
#     cross3  mod 3   does not     MOVING — inflects every pass
#
# So the two accents drawn from the sieve's own vocabulary are exactly the two that
# cannot vary, because they are built from the sieve's own moduli. All the motion comes
# from cross3, which is foreign to the sieve by necessity, not oversight: only a modulus
# the sieve does not use can fail to divide its period.
WEATHER = {
    'sieve5': '5@1|5@3',                 # clause 1's mod-5, verbatim
    'sieve8': '8@0|8@1|8@2|8@5|8@6',     # clauses 2+3's mod-8, verbatim
    'cross3': '3@0|3@1',                 # foreign modulus — the only source of motion
}

# ---------------------------------------------------------------------------
# THE PARITY ACCENT — not weather; the device that makes weather cross grids
# ---------------------------------------------------------------------------
# This is the one place voices differ, and the difference is FORCED. The proof:
#
#   (1) all voices must begin and end together at the total cycle;
#   (2) nothing may repeat identically within it.
#   (1)+(2) => every voice must have the SAME period. If periods differed, the cycle
#             where they align is their LCM, longer than the shortest voice, so that
#             voice repeats inside it — absolute repetition.
#   A voice's period is LCM(note layer, accent moduli) x its basic unit. Voices sharing
#   an accent set share that LCM, so their periods stand in the ratio of their units:
#   480 x 120 = 57600 against 480 x 160 = 76800, never equal.
#   => parity and a fully shared accent set are mutually exclusive across grids.
#
# Giving up the polyrhythm instead would cost the piece its central relationship; giving
# up parity would make A repeat four times inside a 120-bar ensemble. Breaking the
# weather in ONE accent is the cheapest of the three, and it is broken in the accent
# whose only job is to set the period — so the weather proper stays universal.
#
# Residues follow one rule: take some the parent covers AND at least one it omits, so the
# accent is INDEPENDENT rather than a refinement. Carrying a parent's residues up wholesale
# guarantees containment (every n = 0,1,2,5,6 mod 32 is also 0,1,2,5,6 mod 8) and makes
# four accent states unreachable.
#   span32 = clause 1's mod-8 lifted — shares 0,1 with sieve8, adds 7 which it omits.
#   span9  = shares residue 0 with cross3, adds 2 which cross3 omits.
PARITY_ACCENT = {
    120: ('span32', '32@0|32@1|32@7'),   # sixteenth grid
    160: ('span9',  '9@0|9@2'),          # triplet grid
}

# ---------------------------------------------------------------------------
# Voices — each derived from the base sieve, never independently authored
# ---------------------------------------------------------------------------
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
# One pitch per voice, derived from position rather than written out per instrument,
# so every output agrees by construction. A fifth voice gets pad 5 free. A voice may
# still pin its own by setting 'root' explicitly above.
DRUM_RACK_BASE = 36  # C1 = Drum Rack pad 1

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('root', DRUM_RACK_BASE + _i)

    # The accent set is ASSEMBLED, never written per voice: the shared weather plus the
    # one parity accent its grid requires. A voice cannot be given accents of its own.
    _unit = _cfg.get('step_ticks') or int(
        TICKS_PER_QUARTER_NOTE * DURATION_MULTIPLIER_KEY[_cfg['duration']])
    if _unit not in PARITY_ACCENT:
        raise KeyError(f"voice {_cfg['name']!r} uses a {_unit}-tick unit with no parity "
                       f"accent defined. Known units: {sorted(PARITY_ACCENT)}. Without one "
                       f"this voice cannot reach the same period as the others.")
    _label, _expr = PARITY_ACCENT[_unit]
    _cfg['accent_dict'] = dict(WEATHER, **{_label: _expr})
