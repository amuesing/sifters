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

# The quietest a sieve hit is allowed to be.
#
# "Where a number occurs, a sound occurs" — so a step the sieve selects but no accent
# lands on must still be AUDIBLE, not merely present. At velocity 1 about a tenth of
# the piece (and a sixth of voice D) was inaudible on a Drum Rack, which silently
# subtracted those hits from the sieve's statement. Raising the floor costs almost
# nothing in contrast: the accent weights simply share a smaller budget and keep the
# same spread — 16 distinct velocities either way.
GHOST_VELOCITY = 24
FULL_VELOCITY  = 127

# A voice with no accent layer at all sits here — neither ghost nor accented.
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
# Four accents per voice. Two are drawn from the base sieve's own vocabulary, one
# introduces a modulus the sieve does not use, and one sets the period.
#
#   The psappha sieve, clause by clause:
#     clause 1   (8@0|8@1|8@7) & (5@1|5@3)        mod-8 {0,1,7}   mod-5 {1,3}
#     clause 2   (8@0|8@1|8@2) & 5@0              mod-8 {0,1,2}   mod-5 {0}
#     clause 3   (8@5|8@6) & (5@2|5@3|5@4)        mod-8 {5,6}     mod-5 {2,3,4}
#
# `sieve8` is the mod-8 residues of clauses 2 and 3 together — equivalently, every
# mod-8 residue the sieve uses except 7. It has been written that way since dois_two.
# It was briefly thinned to 8@0|8@1|8@5 on 2026-09-03 to fix a velocity-spacing
# problem, and then dropped entirely; both were mistakes. {0,1,5} corresponds to no
# clause of the sieve, so the thinning turned a derived object into a hand-picked one,
# and dropping it removed the sieve's mod-8 self-reference from the accent layer
# altogether. Ranked velocity spacing solves the spacing problem without touching the
# residues, so the original is restored.
#
# `sieve5` is clause 1's mod-5 component, verbatim. It replaces the former `low5`
# (5@0|5@1), which matched no clause — it was simply the two lowest residues, chosen
# by hand. Same density, so the ordering is unaffected; the difference is that it now
# means something. Between them, sieve8 and sieve5 reference all three clauses.
#
# `cross3` uses modulus 3, which appears NOWHERE in the sieve. That is deliberate and
# should not be "corrected": it is the accent that does not divide the 40-step note
# layer, so it is what makes the accent field land differently on each pass, and it
# carries the factor of 3 the triplet voice's period needs. A foreign modulus by
# choice, not by oversight.
#
# The parity accent is derived in turn: span32 carries sieve8's residue set up to
# modulus 32, span9 carries cross3's shape up to modulus 9.
_BASE_ACCENTS = {
    'sieve5': '5@1|5@3',                    # clause 1's mod-5, verbatim
    'sieve8': '8@0|8@1|8@2|8@5|8@6',        # clauses 2+3's mod-8, verbatim
    'cross3': '3@0|3@1',                    # a modulus the sieve does not use
}

# The parity accent: its modulus is what makes a voice's period in TICKS match the
# others' despite a different basic unit. Residues are carried up from an existing
# accent rather than invented — span32 is sieve8's residue set at modulus 32, span9
# is cross3's shape at modulus 9 (and 9 being a multiple of 3, cross3 survives beside
# it, so the triplet voice still accents the beat every 3 steps = one quarter note).
ACCENTS_SIXTEENTH = dict(_BASE_ACCENTS, span32='32@0|32@1|32@2|32@5|32@6')
ACCENTS_TRIPLET   = dict(_BASE_ACCENTS, span9='9@0|9@1')
# ---------------------------------------------------------------------------
# Voices — each derived from the base sieve, never independently authored
# ---------------------------------------------------------------------------
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
        'step_ticks': 160,          # triplet 8th — no named duration can express it
        'accent_dict': ACCENTS_TRIPLET,
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
