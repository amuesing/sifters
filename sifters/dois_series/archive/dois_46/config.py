"""The composition's settings. README.md explains what each group means musically.

This file describes the piece; every other file works for any sieve (Principle VII).
Another piece names only what it changes, in pieces/<name>.py, and renders with
`python3 compose.py --piece <name>`.
"""
TITLE = 'dois_46'
VERSION = TITLE           # this engine's version; a piece keeps it while naming itself
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
# Where renders go, a folder per kind of file; another piece gets its own inside each.
OUTPUT_DIRS = {kind: _os.path.join(_HERE, kind)
               for kind in ('mid', 'wavetables', 'tuning', 'presets')}
TICKS_PER_QUARTER_NOTE = 480
TEMPO_BPM = 120

# Named durations in quarter notes. A triplet or other grid sets 'step_ticks' instead.
DURATION_MULTIPLIER_KEY = {
    'Whole Note':         4,
    'Half Note':          2,
    'Quarter Note':       1,
    'Eighth Note':        0.5,
    'Sixteenth Note':     0.25,
    'Thirty-Second Note': 0.125,
}

# Velocity is a synth-control value; 0 would mean note-off.
MIN_VELOCITY = 1
MAX_VELOCITY = 127

# How long a note sounds. 'step' fills its step at GATE_RATIO (1.0 = the whole step, so
# notes abut). 'held' holds every note until the voice's next attack, so the sieve's gaps
# become durations and a synth's envelopes and wavetable position have time to move. A
# device that will not retrigger from a zero-length gap needs 'step' below 1.0.
ARTICULATION = 'step'
GATE_RATIO = 1.0

TIME_SIGNATURE = (4, 4)           # fallback only, if no meter fits a period
MAX_METER_NUMERATOR = 99          # Ableton's limit

# THE ACCENTS. Velocity is a property of the accent STATE, so these two settings are what
# the whole velocity profile is built from. None means derived from the sieve:
#
#   WEATHER = None          one accent per modulus the sieve uses, on the half of its
#                           residues the sieve's attacks favour, chosen so that every
#                           voice meets every on/off combination (the whole velocity
#                           profile in every voice). The same field for every voice.
#   SPAN_RESIDUES = None    one residue set per span modulus, derived so the passes parity
#                           forces differ as much as possible: every block half full, the
#                           closest passes furthest apart (see span.py).
#
# Naming either explicitly is checked the same way, BEFORE anything is written.
WEATHER = None

# What the search derives for psappha at these units, pinned so a render does not repeat
# the search; tests/test_derivation.py fails if the search ever disagrees. IF YOU CHANGE
# THE SIEVE OR A BASIC UNIT, set this back to None (`--suggest-span` reports on a set).
SPAN_RESIDUES = {32: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 18, 20, 22, 27, 31), 3: (0,)}

# THE VOICES. A is the source; B its complement; C its shift; D their intersection.
# 'diagonal' is the lattice's own diagonal, sum(P/m) over the sieve's moduli: 5 + 8 = 13
# for psappha, the multiplier the pitch lattice and the wavetables also use.
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

# PITCH. Every mode shares timing and velocities; only pitch differs.
#   static   one fixed note per voice (36-39), for hardware that cannot take pitch;
#   lattice  pitch read off the sieve's own grid, the same for every voice at a step;
#   canon    each voice reads the lattice at the step its note descends from, so C plays
#            A's melody 13 steps later. Lattice and canon need two coprime moduli.
PITCH_MODES = ('static', 'lattice', 'canon')
VOICE_PITCH_BASE = 36     # static: C1, one semitone up per voice, in config order
PITCH_ROOT = 36           # lattice: MIDI 36–75; 40 positions spanning 39 semitones
# None derives the interval from the other lattice axis; integers override it.
PITCH_ROW_INTERVAL = None
PITCH_COL_INTERVAL = None

# THE FORM: `<title>_lattice_form.mid` and `<title>_canon_form.mid`, one section per step
# of the period, a voice present where its note layer has an attack (see form.py).
FORM = True

# The lattice's period as one octave: `.tun` for one Serum instance, `.scl` + `.kbm` for
# MTS-ESP (see tuning.py).
TUNING = True

# SERUM WAVETABLES: per voice a 128-frame table, one frame per note or velocity value,
# and a sweep table of the parity statement (see wavetable.py). `--install-serum` copies
# them into Serum's Tables/<SERUM_PROJECT>/<folder>, the folder named for the version, and
# for a piece the version and the piece ("dois_46", "dois_46 eight_five"), so no two
# versions ever share a folder. Installing replaces that folder's files; it never merges.
WAVETABLES = True
WAVETABLE_SWEEP = True
WAVETABLE_FRAME_SAMPLES = 2048     # Serum's single-cycle frame length
SERUM_PROJECT = 'sifters'

# SERUM PRESETS (dois_46): for every voice a drum whose numbers come from its own rhythm,
# and FM pairs whose modulator is the voice's complement table, at ratios from the sieve's
# numbers; with velocity or with the note picking the frame (see serum.py). The complement
# tables go into wavetables/ beside the voices' own; `--install-serum` installs both, and
# the presets under Presets/User/<SERUM_PROJECT>/<folder>, named after the same folder
# ("dois_46 FM B accents 1-1"). What is chosen, not derived:
SERUM_PRESETS = True
KIT_OCTAVES_UP = 5        # between a voice's attack rate and its drum's pitch
KIT_LEVEL = 0.35          # the level at the softest accent; velocity takes it to 1
FM_PEAK_DEPTH = 1.0       # Serum's FM warp depth at velocity 127

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('pitch', VOICE_PITCH_BASE + _i)
