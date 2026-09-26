# Design background inherited from Claude’s dois_25

These are historical explanations from the parent version. Current behavior and the reading guide are in README.md.

## accents.py: module

The weather, the span accent, and the velocity each note is given.

Two kinds of accent. The WEATHER is shared by every voice and its moduli come from the
sieve, so it divides the note layer and lands the same way on every pass. The SPAN
accent is derived per voice from the parity arithmetic; because its modulus does NOT
divide the note layer, it inflects each restatement differently, which is what keeps
the piece from repeating itself.

Velocity is a property of the accent STATE — which accents are sounding at that step —
not of the note. Nothing here is written by hand; see `span_accent`.

## accents.py: span_accent

The span accent for a voice: modulus AND residues, both derived.

The modulus follows from the parity arithmetic (see `required_modulus`); nothing
chooses it. The RESIDUES come from config — SPAN_RESIDUE_SOURCE, or the candidate
passed in when compose.py is searching for a set that works — kept where they fall
below that modulus. For this composition they are clause 1's mod-8 residues. `sieve8` is clauses 2+3, so clause 1 is exactly the clause the
weather omits, which is also what keeps the span accent independent of `sieve8`
rather than a refinement of it.

At modulus 32 that gives {0,1,7}; at modulus 3, {0,1}. Both are what dois_eleven had
written by hand.

## accents.py: levels_from_weights

Rank every accent state by summed rarity, then space the velocities evenly.

A sparse accent outranks a common one, and more accents outrank fewer. Only the
SPACING is imposed: proportional spacing let accents of similar density earn
near-identical weights and rendered genuinely different states 1 velocity apart.

All 2^n states are ranked, including any this piece never reaches. Velocity is not
volume here — it drives synth parameters — so there is no audibility floor to
protect and no reason to withhold range from a state the rhythm happens to miss.

## accents.py: shared_velocity_levels

ONE velocity table for the whole piece. New in dois_22.

Until now each voice ranked its own accents, so the same combination of accents
could mean different velocities in different voices: with the weather alone
sounding, A played 19 and D played 37. The weather is one field (Principle III), so
what it MEANS should be one thing too.

Every voice carries the same weather in the same order plus exactly one span accent,
so bit positions already mean the same thing everywhere. Only the span accent's
density differs between grids — span32 is rare, span3 is common — so the shared
table weights that bit by the RAREST span in the piece. The rarest is the one whose
presence says the most, and taking the maximum keeps the span ranked above the
weather rather than sliding beneath it.

`fields` maps each voice name to its accent binaries.

## check.py: module

Reading the rendered files back, and proving they are what was intended.

Nothing here trusts the renderer. Every check re-reads the MIDI that was actually
written and tests it against the config, so a fault in the code that writes the notes
cannot vouch for itself.

`verify` is the driver: it runs each `check_*` below, collects every failure rather
than stopping at the first, and prints what it found. Each check is named for the
promise it keeps, and they are independent — read any one on its own.

## check.py: check_derivations

Assert every voice really is what config says it is derived from.

This is the one class of error the file-level checks cannot see. Change
`shift_amount` to 14, or swap `intersection` for `union`, and every clip is still
one true period, still ends on a bar line, still matches its ensemble track — and
the piece is no longer the structure it claims to be. The project's whole premise
is that voices are DERIVED rather than independently authored, so the derivations
are what must be checked.

## check.py: expected_velocity_table

Rebuild the velocity table from config, independently of the renderer.

This deliberately REIMPLEMENTS the ranking in accents.py rather than calling it.
That duplication is the point: a checker that asks the renderer what it intended
can only ever agree with it. Here the weights are exact fractions counted from the
accent patterns, so a fault in the renderer's arithmetic shows up as a mismatch.

Returns {state code: velocity}.

## check.py: check_every_velocity

EVERY note's velocity, against the table rebuilt from config. New in dois_23.

dois_22 kept one velocity per accent state and compared voices to each other. That
was weak twice over, and GPT found both holes (dois_23(gpt)):

  * a later note in the same state OVERWROTE the record of an earlier one, so a
    single wrong velocity passed unnoticed — D's first note set to 2 instead of 91
    was invisible;
  * comparing voices to each other only finds DISAGREEMENT. Rank every voice the
    same wrong way and they agree perfectly, and the check passed.

So: every note is checked, nothing is overwritten, and the expected value comes from
`expected_velocity_table`, which is rebuilt from config rather than asked for.

## compose.py: module

Run the composition: config -> voices -> MIDI files -> checks.

Read this file first. It is the whole process in order, and every step it takes is a
call into one of the four modules beside it:

    config.py    the composition itself — the sieve, the voices, the weather, tempo
    sieve.py     the sieve expression becomes a pattern; voices are derived from it
    accents.py   the weather and span accent decide each note's velocity
    midi.py      steps become timed events and get written to .mid files
    check.py     the files are read back and tested against what was intended

Nothing here knows anything about THIS sieve. Change the sieve in config.py and every
period, span, accent modulus and meter below is recomputed from it.

    python3 compose.py                 render and verify
    python3 compose.py --suggest-span  for a new sieve: residues that inflect every pass

## compose.py: config_fingerprint

A short hash of everything that determines the output.

Two renders with different sieves, accents, units, tempo or meter get different
fingerprints; two renders of the same configuration get the same one. Without it,
files from different versions are indistinguishable once they are sitting in a
project folder.

dois_15's version hashed a hand-written list of settings, and when pitch was added
the list was not updated: dois_14 and dois_15 both stamped cfg=3a412cb1 despite
different pitches, and GATE_RATIO had never been covered at all. Any explicit list
has that failure mode — the next setting added has to be remembered. So nothing
here is listed by hand:

  * EVERY upper-case setting in config.py is collected automatically, so a new
    setting cannot be left out. OUTPUT_DIR is excluded — it is a path on this
    machine and would give the same music a different stamp on another one.
    'accent_dict' is excluded from the voices: main() writes it at run time,
    derived from settings that are already hashed.
  * EVERY .py file beside this one is hashed, so a change to the code — not only
    to the configuration — changes the stamp, and adding a module cannot be
    forgotten the way a hand-written list of filenames can;
  * the versions of the three libraries that shape the bytes are included.

The trade-off is deliberate: an edit that changes nothing audible, a comment say,
also changes the stamp. A spurious difference is harmless; a spurious match —
two different pieces claiming one fingerprint — is the failure this exists to stop.

## midi.py: module

Steps to MIDI, and back again.

Three jobs, in order: work out the meter a period wants (`meter_for`, `shared_meter`),
turn a voice's steps into timed note events (`voice_events`), and write or re-read the
files (`make_track`, `save_tracks`, `read_track`).

`read_track` exists so the checks can read what was actually WRITTEN rather than trust
what was computed.

## midi.py: meter_for_voice

A meter in which this voice's clip ends exactly on a bar line.

Preference 1 — the beat IS the voice's basic unit and the bar is one pass of the
note layer. A sixteenth grid gives 4*TPQ/120 = 16, so 40 steps is 40/16.

Preference 2 — a grid that is not a power-of-two subdivision cannot be a beat
(a triplet gives 4*TPQ/160 = 12, not a valid denominator). Fall back to any meter
whose BAR equals the voice's whole period: the beat is then not the voice's unit,
but the bar still lands on the period, which is what stops a host padding the clip.

## midi.py: shared_meter

One meter for every voice, when one exists.

A candidate bar is one pass of SOME voice's note layer at that voice's own basic
unit. Voices may have different note layers and different units, so each offers a
different candidate. One can be shared only if it divides EVERY length — otherwise
a clip would not end on a bar line and the host would pad it — and is expressible
as a meter at all. The finest workable bar wins, so the beat stays a real
subdivision rather than a coarse container.

## pitch.py: module

How a step becomes a note number — the only thing that differs between modes.

Two modes, rendered side by side from one rhythm:

    static    one fixed note per voice. Pitch carries nothing, so the sieve speaks
              through rhythm and velocity alone. This is the Grandmother version, and
              the one to use when pitch is not available as a CV source.
    lattice   pitch read off the sieve's own grid. Because the base sieve's two moduli
              are coprime, every step has a unique (step mod a, step mod b) address,
              and one interval per axis turns that address into a note.

Each mode supplies `notes(cfg)` — a function from step index to MIDI note — and
`check(note_layers)`, which refuses before anything is written if its settings cannot
render correctly. Nothing here knows which sieve is in config; the lattice reads its
axes from whatever moduli the sieve uses.

## pitch.py: lattice_intervals

One interval per axis. Derived by default: the sieve's moduli, EXCHANGED.

The lattice is a linear map — which is what carries residue classes to residue
classes and makes the canon an exact transposition — exactly when the row interval
is a multiple of the column modulus and the column interval a multiple of the row
modulus. Exchanging the two moduli is the smallest pair that qualifies, so it is the
default, and a new sieve needs no new pitch settings. Config may still override.

## pitch.py: check_lattice

Everything the lattice claims, asserted before any file is replaced.

Credit where due: dois_15 justified the residue-class property by BIJECTIVITY, and
GPT showed that was wrong — most permutations of n things scatter a residue class.
What carries classes to classes is LINEARITY, the map being multiplication by a
unit. So that is what is checked, and the class property is then asserted directly
rather than inferred.

## sieve.py: module

What the sieve produces: a pattern of steps, and the voices derived from it.

A sieve expression like `8@0|8@1` is a rule about which integers belong. `evaluate`
turns it into a row of 1s and 0s — a 1 wherever the rule is satisfied. Everything else
in the project is built on that row.

The engine knows nothing about any particular sieve. Moduli, period, how many voices
and how they relate all come from config.py.

## sieve.py: true_period

The period a sieve's binary ACTUALLY repeats on.

`music21.sieve.Sieve.period()` returns the LCM of the moduli written in the
expression. That is an upper bound, not the truth: `32@0|32@1|32@16|32@17` reports
32 and repeats every 16, because its residues are themselves periodic. Trusting it
would let a voice be rendered at twice its real period — the same material stated
twice and still called one period.

The true period always divides the nominal one, so evaluating over one nominal
period and taking the smallest divisor the array repeats on is exact.

## sieve.py: build_binary

One voice's note layer, at its OWN true period.

Every voice derives its own period; they happen to coincide here because all four
descend from one 40-step sieve, but nothing assumes that. A voice defined by its
own sieve takes that sieve's measured period. A derived voice is combined over the
LCM of its sources' periods, then reduced to the period the result actually has —
a derivation can close sooner than its sources do, and the voice's length must state
the period it really has, not the one it was computed over.

## Original composition-setting commentary

```python
TITLE = 'dois_25'
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
# PITCH — two modes, rendered side by side from one rhythm
# ---------------------------------------------------------------------------
# Both are written on every run, into mid/<mode>/, so the same rhythm and the same
# velocities can be auditioned either way and drawn from as material.
#
#   static    one fixed note per voice, so pitch carries nothing and the sieve speaks
#             through RHYTHM and VELOCITY alone. This is the Moog Grandmother version:
#             that instrument cannot take pitch as a CV source. Consecutive notes from
#             a base — C1, C#1, D1, D#1 — so the four parts stay separable in a DAW.
#
#   lattice   pitch read off the sieve's own grid. The base sieve's moduli are coprime,
#             so every step has a unique (step mod 8, step mod 5) address; one interval
#             per axis turns that address into a note. The intervals below are the
#             sieve's moduli exchanged, which is the smallest pair that makes the map
#             linear — and linearity is what carries residue classes to residue classes
#             and makes the canon an exact transposition (of +9 MODULO 40; heard, 23 of
#             C's 27 notes rise 9 semitones and four fall 31 where the fold wraps).
#
# The AXES are not written here: pitch.py reads them from whatever moduli the sieve
# uses, and refuses to render if there are not exactly two, coprime, whose product is
# every voice's note-layer period. See CONTEXT.md, "Pitch work", for the four
# derivations tried and the results worth not re-deriving.
PITCH_MODES = ('static', 'lattice')

VOICE_PITCH_BASE = 36     # static: C1, one semitone up per voice, in config order

PITCH_ROOT = 36           # lattice: MIDI 36-75, C2 to D#5, 40 pitches over 39 semitones
# The intervals are DERIVED: the sieve's own moduli, exchanged, which is the smallest
# pair that makes the lattice linear. For this sieve that is 5 semitones per mod-8 row
# (a fourth) and 8 per mod-5 column (a minor sixth). Set a number to override.
PITCH_ROW_INTERVAL = None
PITCH_COL_INTERVAL = None

for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('pitch', VOICE_PITCH_BASE + _i)

```
