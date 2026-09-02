TITLE = 'dois_ten'
import os as _os
OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mid')
TICKS_PER_QUARTER_NOTE = 480

DURATION_MULTIPLIER_KEY = {
    'Whole Note':         4,
    'Half Note':          2,
    'Quarter Note':       1,
    'Eighth Note':        0.5,
    'Sixteenth Note':     0.25,
    'Thirty-Second Note': 0.125,
}

# Every generated file states the same meter and the same tempo, on every track,
# so no two outputs can disagree about them. 4/4 because it is the only meter all
# four voices can share: a triplet cycle cannot be expressed as any power-of-two
# meter (see CONTEXT.md), so a per-voice meter would have to differ by definition.
# Fallback meter, used only for a voice whose basic unit is not a power-of-two
# subdivision (a triplet grid) and therefore has no meter of its own.
TIME_SIGNATURE = (4, 4)

# Steps in one pass of the note layer — the sieve's own period, LCM(8, 5). This is
# the bar length for each voice's meter, so one bar = one statement of the rhythm.
NOTE_LAYER_STEPS = 40

# Ableton accepts time-signature numerators up to 99.
MAX_METER_NUMERATOR = 99
TEMPO_BPM = 120

# ---------------------------------------------------------------------------
# Accent sieves
# ---------------------------------------------------------------------------
# Three accents are shared by every voice. The fourth is the PARITY accent, and its
# modulus is chosen so that a voice's period in TICKS matches the others' even though
# the basic units differ.
#
# Identical accent sets cannot give parity across different units: A and D both used
# {5,8,3} and both landed on 120 steps, but 120x120 = 14400 while 120x160 = 19200. The
# accent moduli have to scale INVERSELY to the basic unit.
#
#   16th voices  (unit 120): LCM(40, 5, 8, 3, 32) = 480 steps x 120 = 57600 ticks
#   triplet voice (unit 160): LCM(40, 5, 8, 3,  9) = 360 steps x 160 = 57600 ticks
#
#   480 / 360 = 4/3 = 160 / 120   <- the step counts invert the unit ratio exactly
#
# 19200 ticks is the floor for any such parity (LCM of 40x120 and 40x160); 57600 is
# the multiple that lets the sixteenth voices keep their mod-3 accent.
#
# Parity depends ONLY on the moduli. The residues are free artistic choice and can be
# changed without breaking it — but keep them irreducible: residues that repeat at a
# smaller modulus (e.g. 32@0|32@1|32@16|32@17, which is really mod 16) silently
# shorten the period, and music21's Sieve.period() will not catch it.
_BASE_ACCENTS = {
    'low5':  '5@0|5@1',
    'wide8': '8@0|8@1|8@2|8@5|8@6',
    'mod3':  '3@0|3@1',
}
# wide8's residue set carried up to modulus 32
ACCENTS_SIXTEENTH = dict(_BASE_ACCENTS, span32='32@0|32@1|32@2|32@5|32@6')
# mod3's shape carried up to modulus 9; 9 is a multiple of 3, so mod3 is kept as well
# and D still accents the beat every 3 steps = one quarter note
ACCENTS_TRIPLET   = dict(_BASE_ACCENTS, span9='9@0|9@1')

# Same four voices as dois_three — base sieve, complement, canon, polyrhythm.
INSTRUMENT_CONFIGS = [
    {
        'name': 'A',
        'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
        'accent_dict': ACCENTS_SIXTEENTH,
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'B',
        'derives_from': 'A',
        'relationship': 'complement',
        'accent_dict': ACCENTS_SIXTEENTH,
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'C',
        'derives_from': 'A',
        'relationship': 'shift',
        'shift_amount': 13,
        'accent_dict': ACCENTS_SIXTEENTH,
        'duration': 'Sixteenth Note',
    },
    {
        'name': 'D',
        'derives_from': ['A', 'C'],
        'relationship': 'intersection',
        'step_ticks': 160,
        'accent_dict': ACCENTS_TRIPLET,
    },
]


# ---------------------------------------------------------------------------
# Drum Rack pad assignment
# ---------------------------------------------------------------------------
# Each voice plays one pad, derived from its position in INSTRUMENT_CONFIGS rather
# than written out per instrument. One pitch per voice, used by every output — the
# prime clips, the arrangement and the combined drum rack clip all agree by
# construction, so they cannot drift apart. Adding a fifth voice gets pad 5 for free.
# A voice may still pin its own pitch by setting 'root' explicitly above.
DRUM_RACK_BASE = 36  # C1 = Drum Rack pad 1

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('root', DRUM_RACK_BASE + _i)
