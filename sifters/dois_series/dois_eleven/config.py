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

# The parity accent. Its MODULUS is what makes a voice's period in ticks match the
# others' despite a different basic unit; its RESIDUES decide whether it is an
# independent layer or merely a refinement of another accent.
#
# It must be INDEPENDENT: it has to fire both with and without every other accent, or
# some accent states can never occur. The earlier residue sets failed this. Carrying a
# parent's residues up to a higher modulus — span32 = sieve8's {0,1,2,5,6} at mod 32,
# span9 = cross3's {0,1} at mod 9 — guarantees CONTAINMENT whenever the residues are
# smaller than the parent's modulus: every n congruent to 0,1,2,5,6 mod 32 is also
# 0,1,2,5,6 mod 8. So span32 could never fire without sieve8, span9 never without
# cross3, and 4 of the 16 accent states were unreachable by construction.
#
# The rule instead: take some residues the parent covers AND at least one it omits.
#
#   sieve8 is clauses 2+3's mod-8 {0,1,2,5,6}; clause 1's is {0,1,7}. Lifting clause 1
#   to modulus 32 gives 32@0|32@1|32@7 — it shares 0 and 1 with sieve8 and adds 7,
#   which sieve8 omits. Derived from the sieve, and independent of sieve8 for exactly
#   the reason that makes it derived: clause 1 is the clause sieve8 leaves out. Between
#   them the two accents now cover all three clauses' mod-8 vocabulary.
#
#   cross3 is foreign to the sieve, so its parity partner follows the rule rather than
#   a clause: 9@0|9@2 shares residue 0 with cross3 ({0,1} mod 3) and adds 2, which
#   cross3 omits.
#
# All 16 accent states are now reachable in every voice.
ACCENTS_SIXTEENTH = dict(_BASE_ACCENTS, span32='32@0|32@1|32@7')
ACCENTS_TRIPLET   = dict(_BASE_ACCENTS, span9='9@0|9@2')

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
