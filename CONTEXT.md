# Sifters — Project Context

> This file is the canonical reference for continuing work across machines and sessions.
> **Always update this file at the end of a working session.**
> Last updated: 2026-09-24

---

## GPT general verifier correction — dois_23(gpt), 2026-09-24

User requested the shared-velocity bug fix and attention to updated principles.
Forked Claude22 into23(gpt), keeping lines separate. Principle VII was reread:
config is specific; engine must be general. No pitch revival or musical change.
Verifier now retains every velocity occurrence and checks every note against an
independently reconstructed configured table using exact rational rarity counts.
An early wrong velocity cannot be erased by a later correct occurrence, and a
uniformly wrong table is rejected too. Eight tests pass, including the alternate
7/5 sieve and two new regressions that both fail with the old checker. All six
MIDI files independently match22 note-for-note; original parity preserved.
Detailed response appended to FOR_CLAUDE.md; explanation in23(gpt)/README.md.


---

## GPT stationary-weather comparison — dois_19(gpt), 2026-09-23

User authorized fixing C's accent weather. Forked dois_18(gpt) into dois_19(gpt),
keeping the separate-lines rule. Removed C's13-step roll from all accent binaries,
including the span accent; rhythm and pitch remain canon-derived. Local-step weather
now samples i for every voice. Only84/108 C velocities change; A/B/D fully unchanged.
All onset/duration/pitch/channel data retained,328 notes,19200-tick first parity.
Accented passes stay distinct4/4/4/3 and full minimal periods hold. Eight tests and
independent raw-byte verification cover all six MIDI files. D's per-grid velocity
table and different clock are unchanged; this is not absolute-time weather or a
shared-table fix. README and root FOR_CLAUDE.md document the isolated comparison.


---

## GPT pitch-class reference — dois_18(gpt), 2026-09-21

User authorized an additive lattice-to-pitch-class version, with GPT in its folder,
and an update to FOR_CLAUDE.md. Forked Claude dois_17, keeping both lines distinct.
Axis movements are derived from cyclic closure into Z/12: mod8 permits {0,3,6,9},
mod5 only0; smallest positive maximal-image generator yields (3,0). MIDI realization
is root36 plus class offset: 36/39/42/45 in one octave. Register and positive-generator
choice are explicit. Four classes are a consequence of this additive experiment,
not a new project-wide restriction. Mod5 still affects rhythms but not class movement.

Original 328-note rhythm/velocity/gate streams and 19200-tick first parity retained.
Pitch field repeats every four local steps; accented complete passes remain distinct.
C's shift13 is +3 mod12 (actual +3 x20, -9 x7). A/B pitch partition is lost; same-clock
unisons remain. Seven tests and independent raw-byte checks cover all six MIDI exports.
Files under dois_18(gpt)/mid; design in its README, direct reply in root FOR_CLAUDE.md.
Claude versions and prior GPT versions unchanged. Next: audition this reference against
Claude's lattice/pcoct before choosing a less restrictive mapping or added pitch timing.

---

## CURRENT — `dois_24`: both pitch modes from one rhythm (2026-09-24)

Every run writes **twelve** files: the drumrack version and the lattice version, sharing
one rhythm and one set of velocities. Pitch is the only difference between them, so both
can be drawn from as material.

    mid/dois_24_static_*.mid     one fixed note per voice (36-39) — the Grandmother
                                 version; the sieve speaks through rhythm and velocity
    mid/dois_24_lattice_*.mid    pitch read off the sieve's own 8x5 grid, MIDI 36-75

**Verified from the bytes:**

| | |
|---|---|
| `static` vs `dois_23` | **identical, note for note**, all six files |
| `lattice` vs `static` | rhythm, velocity, channels identical — only pitch differs |
| `lattice` vs `dois_18` | rhythm and pitch identical; D's velocities differ by 42 (the shared table) |
| the canon, in lattice mode | **+9 modulo 40 exactly**; heard, 23 notes +9 and 4 at -31 |

**Pitch became a strategy, not a branch.** `pitch.py` holds the two modes; each supplies
a step-to-note function and a check that refuses before writing if its settings cannot
render. Nothing else in the engine knows which mode is running.

**The lattice intervals are now DERIVED** — the sieve's own moduli, exchanged, which is
the smallest pair that makes the map linear. They were hand-written before, and the
different-sieve test caught it: with moduli 7 and 5 the configured (5, 8) is not linear
and the render refused. Deriving them means a new sieve needs no new pitch settings,
which is Principle VII doing its job. The psappha output is unchanged.

## `dois_23`: the verifier earns its keep (2026-09-24)

Music identical to `dois_22`. **GPT found two real holes in my velocity check**
(`dois_23(gpt)`), and both were reproduced here before fixing:

1. **One velocity was kept per accent state, so later notes erased earlier evidence.**
   Setting D's first note to velocity 2 — plainly wrong — passed every check in
   `dois_22`, because a later note in the same state overwrote the record.
2. **Comparing voices to each other only finds DISAGREEMENT.** Reversing the ranking for
   every voice at once — consistent, and wrong — also passed.

`check_every_velocity` now tests every note against `expected_velocity_table`, which
**rebuilds the table from config with exact fractions rather than asking the renderer**.
That duplication is deliberate: a checker that asks the renderer what it intended can
only ever agree with it. Both tamperings now fail (1 note, and all 328).

## Claude's review of `dois_23(gpt)` (2026-09-24)

Verified, and it is right on both counts — I reproduced both gaps in my own `dois_22`
before porting the fix. Its output is identical to `dois_22` note-for-note in all six
files, its 8 tests pass, and its checker hardcodes no composition values (the only grep
hit is prose in a docstring). It kept my different-sieve test, left pitch parked, did not
reopen the gate, and did not touch Claude's line. It also says it had not given
Principle VII enough attention before and that this fork follows it — which it does.

Its fix and mine are independent implementations of the same idea: reconstruct the
expected velocity rather than compare voices. GPT reconstructs ranks from exact rational
densities; `dois_23` rebuilds the whole table with `Fraction` and checks every note.

---

## `dois_22`: one velocity table for every voice (2026-09-23)

The last known inconsistency in the piece, closed. Until now each voice ranked its own
accents, so the same combination of accents meant different velocities in different
voices: **with the weather alone sounding, A played 19 and D played 37.** The weather is
one field (Principle III), so what it MEANS is now one thing too.

**How.** Bit positions already agreed — every voice carries the same weather in the same
order plus one span accent. Only the span's density differed between grids (`span32` is
rare, `span3` common), so the shared table weights that bit by the RAREST span in the
piece. The rarest is the one whose presence says the most, and taking the maximum keeps
the span ranked above the weather rather than sliding beneath it. The table:

    1  37  19  73  55  109  91  127      (accent state 0 through 7)

**What changed, measured from the bytes:**

| | |
|---|---|
| A, B, C | **untouched** — 0 of 268 velocities |
| D | **42 of 60 velocities** |
| onsets, lengths, pitches, channels | identical throughout |
| rhythm vs `dois_14` | still identical, all four voices |
| accent states where A and D disagree | **5 of 7 -> 0 of 7** |

**`check.py` asserts it** from the files: work out which accents were firing at each
sounding step, and two voices reaching the same state must have been given the same
velocity. Restoring per-voice ranking in a scratch copy fails the run and names every
clash. 6 tests, including a different sieve end to end.

**This supersedes the open question** recorded under "Two real defects" below — both are
now fixed. Nothing else in the piece is known to be inconsistent.

---

## `dois_21`: the same music, in code you can read (2026-09-23)

Same output as `dois_20`, **note for note in all six files** — the reorganisation
changed how the code reads, not what it makes. Asserted by a test, not by eye.

**One 1077-line file became five, each with one job**, named at the top of `compose.py`:

| file | job | lines |
|---|---|---|
| `config.py` | the composition — sieve, voices, weather, tempo | 164 |
| `sieve.py` | expression to pattern; voices derived from it | 140 |
| `accents.py` | weather, span accent, velocities | 165 |
| `midi.py` | meter, events, writing and re-reading files | 246 |
| `check.py` | reading back and proving it right | 290 |
| `compose.py` | run it, in order | 332 |

**No function is long any more.** `verify` was 193 lines and is now a 32-line driver
over seven named checks, the largest 63. `main` was 159 and is now 43, reading as the
process itself: derive layers, find parity, build accents, check the pitch, build
voices, choose meter, write, verify. Read `compose.py` first; it is the whole story.

**Generality — Principle VII, new today.** See its own section below. The engine assumes
nothing about this sieve; a test renders a different one (moduli 7 and 5, period 35,
parity 16800, meter 35/16) end to end. `--suggest-span` reports the residues a new sieve
needs. A sieve whose accents cannot inflect every pass is refused BEFORE anything is
written, with the reason.

**Two real faults found and fixed while doing it**, both the kind the old single file hid:
- `config_fingerprint` hashed a hand-written list of filenames, so a new module would
  have gone unhashed. It now hashes every `.py` beside it.
- `rhythm_from_file` ended up defined twice during the split. Caught by a check for
  duplicate definitions across modules, and removed.

5 tests: identical output, static pitch, a different sieve renders, a bad sieve is
refused without writing, and `--suggest-span` reports without writing.

---

## `dois_20`: pared down for the Moog Grandmother (2026-09-23)

**The target changed, so the scope did.** The piece is being realised on a Moog
Grandmother, which cannot take pitch as a CV source. Pitch therefore carries no
information: **the sieve is expressed through RHYTHM and VELOCITY alone**, the two things
that instrument can act on. Each voice sounds one fixed note — A=36, B=37, C=38, D=39 —
and never moves off it.

**This is a narrowing, not a reversal.** `dois_20` is `dois_18` with the pitch derivation
removed and nothing else touched. Verified from the bytes: **rhythm, velocity, channels,
lengths and onsets are identical to `dois_18` in all four voices** — only each note's
pitch differs. 108/52/108/60 notes, 19200 ticks, 40/16, one weather asserted, no absolute
repetition. `verify()` now asserts each voice sounds exactly its one note, and a pitch
that is not a whole number in 0-127, or shared between two voices, is refused before any
output is replaced. 5 tests.

**Before patching the Grandmother, decide the gate.** `GATE_RATIO` is still 1.0, so a
note fills its step and its note-off lands on the tick the next note-on begins:

| voice | consecutive pairs that abut |
|---|---|
| A | 56 of 107 (52%) |
| B | 0 of 51 |
| C | 56 of 107 (52%) |
| D | 15 of 59 (25%) |

That is 127 pairs with no gap. The MIDI spec leaves it to the DEVICE whether a Note On
for a sounding pitch retriggers, and **this is the exact symptom the author hit on
hardware once before** (2026-09-10: consecutive notes not sounding, while the same files
played correctly through samplers in Ableton). If the Grandmother swallows them, half of
A and C simply will not articulate. The fix is one line — `GATE_RATIO = 0.5` in
config.py, the classic step-sequencer gate — at the cost that A and B no longer tile
time continuously. Undecided, deliberately: it changes what is heard.

## Pitch work, PARKED — the index (2026-09-23)

Nothing below is deleted, and none of it is load-bearing for rhythm, accents or parity.
If pitch becomes playable again, start here.

**Versions, all on the identical 108/52/108/60 rhythm:**

| where | derivation |
|---|---|
| `dois_15`-`dois_18` | the **lattice**: pitch = root + (5*(n mod 8) + 8*(n mod 5)) mod 40 |
| `dois_18(gpt)`, `dois_19(gpt)` | **strict additive** pitch class: 36 + (3*n mod 12), a diminished seventh |
| `dois_14(gpt)_pitch` | GPT's **gap-based** reading with a signed-sum closure solver |
| `pitch_studies/mid/k13_*`, `k19_*` | the two multiplier candidates first auditioned |
| `pitch_studies/mid/pcoct_*` | **pitch class x octave**: class from the mod-8 axis, octave from mod-5 |

**Results worth not re-deriving:**

- the lattice is **multiplication by 13 mod 40**; `5*(n mod 8) + 8*(n mod 5) == 13n (mod 40)`
  exactly, so the "lattice" and "multiplier" views are one operation;
- it is linear **iff 5 divides the row interval and 8 the column interval**, and (5, 8) —
  the exchanged moduli — is the smallest such pair (28 pairs qualify in 1..39, 16 invertible);
- linearity, not bijectivity, is what carries residue classes to residue classes;
- the +13 canon is **+9 modulo 40 exactly**, but NOT a constant heard interval: 23 of 27
  notes rise 9 semitones and 4 fall 31, and those four are not octave-equivalent;
- **gcd(40, 12) = 4**, so any structure-preserving map onto the 12 pitch classes reaches
  at most **4** of them, and an exact pitch-class canon forces a diminished seventh.
  `dois_18(gpt)` is that case, built and verified;
- the lattice makes A and C sound in **unison 100%** of the time they overlap — the
  texture is heterophonic, not contrapuntal. Never resolved;
- **untested:** the factor 3 that mod-12 needs and the sieve lacks does exist in the
  piece's own 4:3 polyrhythm.

---

## `dois_18`: one weather, fixed (2026-09-23)

The accent-phase defect is fixed, and this is the first change since `dois_14` that
alters what you hear without touching pitch. `dois_17`'s lattice pitch is kept exactly.

**What changed.** `dois_12` through `dois_17` rolled the whole accent field by the shift
amount for a canon voice, with no comment and no principle calling for it, so C carried
A's weather displaced 13 steps. The roll is gone: every voice samples the field at its
own step index. Verified from the bytes:

| | `dois_17` | `dois_18` |
|---|---|---|
| A / B / D velocities | — | **unchanged, 0 of 220** |
| C velocities changed | — | **84 of 108 (78%)** |
| onsets, lengths, pitches, channels | — | identical throughout |
| A and C agree where both strike | **10 / 80** | **80 / 80** |
| B and C agree | **14 / 28** | **28 / 28** |
| pitch | 27 pitches, MIDI 36-75 | unchanged |
| no absolute repetition | holds | holds |

**`verify()` now ASSERTS one weather** instead of describing it: voices sharing a grid
must carry the same velocity wherever they strike together. Restoring the roll in a
scratch copy fails the run — "A and C ... differ in velocity at 70 of 80 shared attacks
— they are not under one weather" — so the bug cannot come back unnoticed. 5 tests.

**Cross-check with GPT.** `dois_19(gpt)` made the same fix independently, on top of its
own pitch mapping. **My C velocities and GPT's are identical at all 108 attacks.**

**Still open, deliberately untouched here:** the velocity RANKING table is per-voice, so
one accent combination can still mean different velocities in D than in A/B/C (A and D
disagree on 5 of 7 shared states — same in `dois_17`, `dois_18`, `dois_18(gpt)` and
`dois_19(gpt)`). Changing it in the same version would have confused two variables.

## Claude's review of `dois_19(gpt)` (2026-09-23)

GPT's stationary-weather fix, forked from `dois_18(gpt)` — the separate-lines rule was
followed. Every claim verified from raw MIDI: only C's velocities change, exactly 84 of
108; A, B and D are untouched; onsets, lengths, pitches and channels are identical;
A/C agreement goes 10/80 -> 80/80 and B/C 14/28 -> 28/28; passes stay distinct with
minimal period = full span; 8 tests pass. It states plainly that it did NOT address the
velocity-table question, and that is true — A and D still disagree on 5 of 7 states.

**One practical caveat.** `dois_19(gpt)` is forked from `dois_18(gpt)`, so it carries the
four-note diminished seventh, not the lattice. Auditioned against `dois_17` it changes
two things at once. To isolate the weather, compare `dois_19(gpt)` with `dois_18(gpt)`,
or use `dois_18`, which isolates it on the lattice pitch.

---

## Claude's review of `dois_18(gpt)` (2026-09-23)

GPT's strict-additive pitch-class version, forked from `dois_17` into its own folder —
the separate-lines rule was followed. Verified from the rendered MIDI, not its reports:
rhythm, velocity and channels identical to `dois_17` in all four voices; the pitch
collection is exactly **{36, 39, 42, 45} = C, Eb, F#, A**, the diminished seventh the
arithmetic predicts; the canon is **+3 mod 12 exactly** (20 notes +3, 7 notes -9) and,
unlike `dois_15`-`dois_17`'s mod-40 fold, those ARE octave-equivalent; A and B no longer
partition the pitches; accent passes stay distinct with minimal period = full span; its
7 tests pass. Every pitch is `36 + (3 * step mod 12)` — pitch is a function of `step mod
4` alone, so the mod-5 axis carries no pitch information. That is the price of strict
additivity, which GPT states plainly. It confirms the result recorded above: with moduli
8 and 5, no more than four pitch classes survive a structure-preserving map onto mod 12.

**Not a defect, but worth knowing:** re-rendering any version on a later date changes the
six MIDI files, because the provenance stamp embeds `date.today()`. Notes and fingerprint
are unaffected. `dois_17`'s outputs showed as modified on 2026-09-23 for exactly this
reason — a re-run, not a change. Byte-identical re-renders hold within a day, not across.

`FOR_CHATGPT.md` was restructured the same day: current state and the open questions
first, the exchange as dated "Round" sections below, the original review as sections 1-10.

---

## Latest Claude iteration — `dois_17`: the two `dois_16` bugs, fixed (2026-09-19)

GPT found two real bugs in `dois_16` (see below). Per the author's rule that the two
lines stay distinct, GPT's fixes live in `dois_16(gpt)` and Claude's are here, written
independently. **The music is unchanged**: every note in all six files is identical to
`dois_16`. Stamp `cfg=d395b224`.

1. **Canon check across different grids.** A canon relates STEPS, not ticks, so each
   voice is now read in its own steps (onsets / its OWN unit). `dois_16` divided both by
   the follower's unit and crashed with `KeyError: 15` when C was given 160 ticks. The
   check also now asserts the modular interval the lattice PREDICTS (diagonal x shift
   mod period = +9), not merely a constant one — GPT's idea — and a misaligned canon is
   reported as a verification failure instead of an exception.
2. **Pitch settings must be whole numbers**, checked before any output is replaced.
   `PITCH_ROOT = 36.5` used to pass preflight, be truncated, and fail afterwards. Uses
   `type(v) is int`, since Python counts `True` as 1.

**Tests:** `dois_17/tests/test_dois17.py`, 4 tests, all rendering into temp dirs:
default notes = `dois_16`; C on 160 ticks renders with the 23/4 canon; a damaged C file
is reported, not raised; bad pitch types leave six REAL previous files untouched (not
decoys, so the test cannot go vacuous if filenames change). Run from `dois_17`:
`python3 -B -m unittest discover -s tests -v`. **The tests were run against `dois_16`'s
code too: every bug test fails there** — they detect the bugs rather than merely pass.

**Cross-check:** with C on 160 ticks, `dois_17` and GPT's `dois_16(gpt)` produce identical
notes in all six files — two independent fixes agreeing on the case that used to crash.

**Still true:** `verify()` reads the written files back, so anything only it can detect is
found after the previous files are replaced. Preflight covers what is knowable in
advance; git keeps every committed render.

---

## GPT follow-up fixes to dois_16 — 2026-09-19

User authorized acting on GPT's review and updating FOR_CLAUDE.md. Two fixes applied
in dois_16: canon verification now uses each voice's own time unit and checks first-
layer correspondence; pitch root/axis intervals must be non-boolean integers before
publication. Unequal A=120/C=160 clocks now verify correctly. Fractional root or invalid
interval types leave all existing MIDI untouched. Four regression tests added under
dois_16/tests, including a decoded dois_15 fixture. Default configuration and musical
note events are unchanged; MIDI rerendered to update source-aware provenance.
FOR_CLAUDE.md has the detailed response and verified mathematical observations.

*[Note by Claude, 2026-09-19: at the author's request these fixes were moved out of
Claude's `dois_16` into `dois_16(gpt)`, unchanged apart from TITLE and the two test
filenames that must follow it. `dois_16` is restored to exactly what Claude pushed. The
tests are in `dois_16(gpt)/tests`.]*

---

## `dois_16`: corrections, no musical change (2026-09-19)

Prompted by GPT's review in `dois_15(gpt)` (its `FOR_CLAUDE.md`, at the repo root and
copied inside that folder). GPT caught four errors in `dois_15`; all were real, all are
fixed here. **The music is unchanged**: every note in all six files — onset, length,
pitch, velocity, channel — is identical to `dois_15` and to GPT's `lattice` baseline,
verified by raw-byte parse. Claude's reply to GPT is the "Latest" section at the top of
`FOR_CHATGPT.md`.

**The four errors GPT found:**

1. **The canon was misdescribed.** `dois_15` said C is A "+9 semitones, constant
   everywhere". It is **+9 modulo 40**. Heard, 23 of C's 27 notes rise 9 semitones and
   **4 fall 31** where the fold wraps; pitch-class moves are 9 and 5 (40 is not a multiple
   of 12, so the wrapped notes are not octave-equivalent). The check had taken the
   difference `% 40` and the result was then described as audible. `verify()` now
   prints both, e.g. `+9 mod 40 (exact); heard +9 x23, -31 x4`, and asserts only the
   modular relation.
2. **Linearity, not bijectivity**, carries residue classes to residue classes. Most
   permutations of 40 things scatter a class. `dois_16` asserts linearity (the lattice
   equals multiplication by a unit at every step) and the class property itself.
3. **The fingerprint omitted pitch and gate.** `dois_14` and `dois_15` both stamped
   `cfg=3a412cb1`; `GATE_RATIO` had never been covered. Fixed differently from GPT's fork:
   GPT listed the fields; `dois_16` collects EVERY upper-case setting automatically (an
   explicit list is exactly how the bug happened), hashes the renderer's own source, and
   includes library versions. `OUTPUT_DIR` excluded, so the same music gets the same
   stamp on another machine. Trade-off: a comment edit changes the stamp too. New stamp
   `cfg=c9049b2d`.
4. **The range** is MIDI 36-75, top note D#5, not E5.

Also removed three more stale claims in `dois_15`: a comment saying `DRUM_RACK_BASE`
assigns channels (dead code — channels come from voice order; setting and per-voice
`root` removed), a reference to a nonexistent `PITCH_MULTIPLIER`, and a docstring still
titled `dois_14`.

**Other changes, adopted from GPT's fork or in its spirit:** lattice axes are read from
the base sieve's moduli (must be exactly two, coprime, product = every voice's layer
period) rather than hard-coded; files are verified with the multiplier form rather than
the function that wrote them; `_drumrack.mid` is now `_ensemble.mid`. Four kinds of bad
lattice are refused before any output is replaced — tested on a scratch copy: non-linear
intervals (7, 4), non-invertible (10, 8 -> x18), root 100, a base sieve with a third
modulus. *(Corrected 2026-09-19: this originally said any lattice that cannot render
correctly is refused first. False — a fractional `PITCH_ROOT` of 36.5 passes preflight,
replaces all six files, and only then fails verification. GPT found it.)*

**Two known bugs in `dois_16`, found by GPT — fixed in `dois_16(gpt)` (GPT's fix) and in
`dois_17` (Claude's, written independently).** Neither
affects the default configuration or a single note:
- the canon check converts both voices' onsets with the follower's time unit, so giving
  C a different unit from A (e.g. 160 ticks) crashes with `KeyError: 15` after rendering;
- non-integer or boolean pitch settings (`PITCH_ROOT = 36.5`) are not refused up front.
Both reproduced against the pushed `dois_16`. `dois_16` itself is left as Claude pushed
it; see the naming rule below.

**A new guarantee, worth knowing:** the lattice `a*(n mod 8) + b*(n mod 5)` is a linear
map (= k*n mod 40) **iff 5 | a and 8 | b**; exhaustively checked, 28 pairs qualify and
**(5, 8) — the exchanged moduli — is the smallest**. So the exchange is a choice, but the
minimal one that makes the lattice linear, which is what the class and canon guarantees
rest on.

**GPT's `moduli` experiment** (in `dois_15(gpt)`, `--pitch-mode moduli`) is NOT in
`dois_16` — it is GPT's experiment and an unmade musical decision. Verified: every note
matches its formula; its comparison table reproduces exactly. One thing its table
misses: under `moduli` A, C and D never repeat their melody from pass to pass (0 of 27,
0 of 27, 0 of 20 positions keep one pitch) — melodic variation across passes, an extra
choice rather than a fix, since the accents already keep passes from repeating; the
cost is that pitch no longer reflects a step's residues. B is the exception — its pitch
cycle (2400 ticks) divides its rhythm layer (4800), so its sampled pitches are exactly
the lattice with multiplier 26 (verified on all 52 notes), not invertible: 20 reachable
pitches and an identical melody every pass. B does gain something else: its unisons with
C fall from 28/28 to 1/28. Rule: for a 120-tick voice under P = 19200, the pitch cycle
divides the rhythm cycle iff 4 | k. *(Corrected 2026-09-19 from "a gain for nothing
repeats identically" and "commensurate iff 4 | k" — every one of these rational clocks is
commensurate; divisibility is the property that matters. Both caught by GPT.)*

**Pitch class — why mod 12 does not fit this sieve (2026-09-19).** The author asked
whether the lattice could move onto pitch classes (octave equivalence). Proven, not
opinion: 12 = 4 x 3 and the sieve is built from 8 and 5, so they share only the factor 4.
Any structure-preserving (linear) map from the 40-step cycle to the 12 pitch classes
reaches **at most 4** of them, and the +13 canon can be an exact pitch-class transposition
only inside a diminished seventh {C, Eb, F#, A}. Alternative, rendered as
`pitch_studies/mid/pcoct_*.mid`: pitch class from the mod-8 axis stepping by fourths,
octave from the mod-5 axis. Octave equivalence is then structural — every `8@r` class IS a
pitch class, so the pedal clauses `8@3`/`8@4` become Eb and Ab pedals across five octaves
— at the cost of 8 pitch classes (no E, A, D, G), a 59-semitone range, and no canon
transposition. The one untested route to all 12: take the missing 3 from the piece's own
4:3 polyrhythm (D's triplet grid, its `span3` accent). Undecided.

**Operational note — iCloud.** This repo lives in iCloud-synced Documents. On
2026-09-19 `dois_15(gpt)/VALIDATION.json` was cloud-only (`ls -lO` shows `dataless`), and
`git status`, `git fetch` and some reads stalled for minutes until sync caught up. If
git hangs here, suspect iCloud before suspecting the code.

**Still open, unchanged:** the accent roll on shifted voices and the non-shared velocity
table (both below); whether to keep the lattice's heterophonic texture; and GPT's four
iteration questions in `dois_15(gpt)/FINDINGS.md`, which are the author's to answer.

---

## GPT response to the lattice — dois_15(gpt), 2026-09-16

Direct fork of Claude dois_15, with default lattice event-for-event baseline and a
separate --pitch-mode moduli clock comparison. All original rhythm/velocity policies
remain. The comparison samples the lattice on independent pitch steps 96/60/96/480
ticks, corresponding to 5/8/5/1 cycles within the original 19200-tick parity. All phases
remain zero; this isolates rate. C is still a rhythmic canon but the experiment does
not promise the baseline modular pitch canon or A/B pitch partition. Measured tradeoffs
are in FINDINGS.md; baseline A/B overlap 0, clock comparison 10. A/C remain unisons.

Clarification of Claude's canon wording: +9 is modulo 40. Across one 27-note canon,
23 corresponding notes move +9 semitones and four move -31; these are not equivalent
modulo 12. A 40-note lattice from root 36 spans MIDI 36–75, or 39 semitones.

GPT fixed pitch/gate omissions in configuration fingerprints, added explicit fixed-
lattice/range guards, independent pitch arithmetic in readback, and eight tests.
All 12 output MIDI files independently checked; baseline reproduces Claude's fixture.
Outputs: ordinary mid/lattice and mid/moduli folders. Full-gate notes, 328 notes,
original 20-second parity. No sound audition claimed. Root FOR_CLAUDE.md is GPT's
direct handoff note, also copied inside the version. Claude sources and prior GPT
versions unchanged. Next: hear same-instrument comparisons, then choose rate/phase
experiments explicitly and measure which structural relationships survive.

---

## `dois_15` — pitch from the sieve's lattice (2026-09-16; corrected by `dois_16`)

Pitch is now derived, not assigned. Every voice previously sounded one fixed Drum Rack
pad; `dois_15` reads pitch off the sieve's own structure.

**The geometry.** Because gcd(8, 5) = 1, every step of the 40-step period has a UNIQUE
address `(step mod 8, step mod 5)`. The period is therefore not a line of 40 things but
an **8 x 5 grid**, and the sieve drawn on it is a shape: `8@3` and `8@4` are complete
rows, `(8@1&5@2)` is a single cell — which is exactly why those clauses fire every 8
steps and once per period respectively. Pitch takes one interval per axis:

```
pitch = PITCH_ROOT + ( 5*(step mod 8) + 8*(step mod 5) )  mod  40
```

The two intervals are the sieve's own moduli exchanged — the mod-8 axis steps by 5
semitones (a fourth), the mod-5 axis by 8 (a minor sixth). Nothing comes from outside
the sieve. Counting 0,1,2,... walks DIAGONALLY across the grid, so each step adds
5 + 8 = 13 semitones and folds back inside the period.

**That identity is exact and is asserted at render time:**
`5*(n mod 8) + 8*(n mod 5) == 13n (mod 40)` for every n. The lattice form and the
multiplier form are one operation. An earlier session presented them as two different
schemes with different characters — that was wrong, and the rendered note content is
identical.

**Verified from the MIDI bytes, not from the code that wrote them:**

| check | result |
|---|---|
| every note on the lattice (recomputed from file onsets) | yes, all four voices |
| rhythm and velocity vs `dois_14` | **byte-identical** — only pitch changed |
| canon: C vs A shifted 13 steps | **+9 mod 40**, exact. Heard: +9 on 23 notes, **-31 on 4** *(corrected 2026-09-19)* |
| A and B pitch sets | 27 and 13, overlap 0, union **40 of 40** |
| hanging / overlapping notes | none |
| merged file | one MIDI channel per voice (0-3) |

The canon interval is not imposed. On the grid, moving 13 steps is 5 rows down and 3
columns right from anywhere, always worth 5*5 + 8*3 = 49, i.e. **+9 modulo 40**. That
modular relation falls out of the displacement already in the piece. **It is not a
constant audible interval** — where the fold wraps, 4 of C's 27 notes FALL 31 semitones
instead, and since 40 is not a multiple of 12 those are a pitch-class move of 5, not 9.
*(Corrected 2026-09-19. This section originally said "+9 semitones, constant everywhere":
the check took the difference `% 40` and the result was then described as heard. GPT
caught it in `dois_15(gpt)`.)*

**`verify()` now asserts the lattice rather than assuming it:** gcd(diagonal, period) = 1;
that all 40 pitches are reached; and that the lattice and multiplier forms agree at
every step. Changing the intervals to something non-bijective now FAILS the run instead
of quietly producing a degenerate scale. *(Corrected 2026-09-19: this originally said a
bijection is what carries residue classes to residue classes. It is not — most
permutations scatter a class. LINEARITY does: the lattice is multiplication by a unit.
`dois_16` asserts that, and the class property itself, directly.)*

**Bug found while building it.** `read_track` keyed sounding notes by pitch alone, so a
cross-voice unison registered as an overlap. It now keys by `(channel, pitch)`.

### The consequence to know about — the texture is heterophonic, not contrapuntal

Pitch is a function of the STEP INDEX, and A, B and C all share the 120-tick grid. So
whenever they sound together they read the same lattice cell and play the same pitch:

| pair | share of overlapping time in unison |
|---|---|
| **A + C** | **100%** |
| **B + C** | **100%** |
| A + D | 4% |
| C + D | 4% |
| B + D | 0% |

42% of the time two or more voices sound, there is only ONE distinct pitch present. This
is not a defect — it is the honest consequence of deriving pitch from the step index, and
it is a real aesthetic: one melodic line stated by three rhythmic agents, with D (on the
160-tick grid) the only genuine second voice. But the +9 (mod 40) canon is a relationship between
MELODIES heard over time, not a harmony — where A and C actually coincide they are in
unison. **Undecided:** whether to keep it. Counterpoint is reachable without leaving the
sieve — let each voice read the lattice through its own derivation rather than the shared
global index (B is the complement, so it could read the transposed lattice, 8 per row and
5 per column; C could index from its source position rather than its sounding position).

### The serial connection (noted 2026-09-16)

The user observed the resemblance to twelve-tone technique. It is not loose:
multiplying by a number coprime to the modulus IS a serial operation (M5/M7 in mod 12,
central to Boulez's "multiplication"); the 40-element row completes the aggregate before
anything repeats; and A/B partition that aggregate exactly — combinatoriality, arriving
free because B is defined as the complement rather than chosen for the property.
**x13 has order 4 in the group mod 40** (13 -> 9 -> 37 -> 1), so there is a closed family
of four mappings parallel to P/I/R/RI:

| map | canon becomes (mod 40) | longest scalar run |
|---|---|---|
| x1 | +13 | 26 — the chromatic degenerate case |
| **x13** (current) | **+9** | **2** |
| x9 | +37 | 3 |
| x37 | +1 | 8 |

Differences that matter: Xenakis wrote sieve theory AGAINST serialism ("The Crisis of
Serial Music", 1955); the row here is generated rather than composed, so there is no free
act to defend; and there is no octave equivalence, the space being 40 semitones, so it is
serial in structure but not in perception. Closest relative is Babbitt's time-point
system, which maps serial operations onto rhythm — the exact inverse of this.

### `pitch_studies/` — throwaway auditions, kept

`sifters/dois_series/pitch_studies/mid/` holds the demos used to choose the scheme:
`k13_*` (adopted, reproduced note-for-note by `dois_15`) and `k19_*` (the rejected
alternative, where the canon lands on a perfect fifth instead). Built by repitching
`dois_14`'s output, so rhythm and velocity are guaranteed identical. Not a version;
delete freely.

---

## `dois_14` — the sieve correction (2026-09-16)

**NOT the same thing as `dois_14(gpt)`.** This is Claude's minimal port: `dois_12`'s code
with one change, to the sieve, and nothing else.

`dois_12`'s base sieve was the psappha sieve **truncated to its first three clauses** —
15 attacks in 40 where the published source has 27. The four missing terms `8@3`, `8@4`,
`(8@1&5@2)`, `(8@6&5@1)` are restored. The expression now reproduces the attack list in
Besada, Barthel-Calvet & Pagan Canovas (2021), DOI 10.3389/fpsyg.2020.611316, open access
as **PMC7849451**, exactly:

```
[0,1,3,4,6,8,10,11,12,13,14,16,17,19,20,22,23,25,27,28,29,31,33,35,36,37,38]
```

`dois_12`'s sieve was a strict subset — no spurious attacks, twelve missing. **Sourcing
caution:** the frontiersin.org copy of this same paper returns a formula that simplifies
to 20 attacks while the prose claims 27, and an attack list matching neither. Use PMC.

Because the voices are derived, correcting A rewrote all four:

| voice | attacks in 40 | notes rendered |
|---|---|---|
| A — base sieve | 15 -> **27** | 60 -> 108 |
| B — complement | 25 -> **13** | 100 -> 52 |
| C — A shifted +13 | 15 -> **27** | 60 -> 108 |
| D — A ∩ C | 6 -> **20** | 18 -> 60 |

The density relationship between A and its complement **inverts** — B was the busier
voice and is now the sparse one. Most audible consequence, and intended.

**Independently cross-confirmed:** `dois_14`'s A and B render to 108 and 52 notes,
identical to `dois_13(gpt)`'s A and B, reached from a different codebase by a different
route. Two unrelated implementations agreeing note-for-note is good evidence the
correction is right. C and D differ between them only by the compositional choices
`dois_13(gpt)` made on top (C slowed to 160; D changed to B ∩ C at 240).

Everything else is `dois_12` unchanged, so the two are directly A/B-able. Parity is still
19200 ticks; meter still 40/16; accent-state coverage moved 6/8 -> 7/8 (A), 6/8 -> 5/8
(B, now too sparse to reach as many), 6/8 -> 7/8 (C), 6/8 -> 8/8 (D).

---

## Two real defects found in this project's code (2026-09-16)

Both surfaced by reviewing `dois_13(gpt)`'s engine. **Both are now FIXED.** The first
in `dois_18` (Claude) and `dois_19(gpt)` (GPT), independently, with identical results.
The second in **`dois_22`** (Claude), 2026-09-23. They are still present in `dois_12`
through `dois_17`; the second remains in `dois_18`-`dois_21` and in `dois_19(gpt)`.

**1. Accents travel with the canon, silently.** The accent roll (`composition.py` line
816 in `dois_12`, 832 in `dois_14`, 883 in `dois_15`, 1016 in `dois_16`) rolls the entire
accent field by the shift amount whenever a voice's relationship is `shift`:

```python
if cfg.get('relationship') == 'shift':
    accent_bins = {k: np.roll(v, cfg['shift_amount']) for k, v in accent_bins.items()}
```

No comment on it, and no principle calls for it. Verified against the rendered MIDI:
**voice C's velocity at step i equals voice A's at step i-13, everywhere C sounds.** C is
not under the same weather as A and B — it carries A's weather displaced 13 steps, which
contradicts Governing Principle III. **84 of C's 108 notes (77%) would change velocity
under a fixed weather.** Rhythm is untouched either way. GPT made this an explicit setting
(`ACCENT_PHASE_POLICY`) and defaulted it to `fixed`; that default matches the stated
principle and this project's silent behaviour does not. A canon carrying its own
accentuation is defensible; happening by accident is not.

**2. The "shared" velocity table is not shared.** `generate_velocity_profile`
(`composition.py` line 352 in `dois_12`, 368 in `dois_14` and `dois_15`, 426 in `dois_16`) claims in a
docstring that "a given combination of accents means the same velocity everywhere in the
piece." True for A, B and C; **false for D**, whose span accent is `span3` where the
others use `span32`, reshuffling the rarity ranking. Six of the eight states differ:

| state (sieve5, sieve8, span) | A/B/C | D |
|---|---|---|
| (1, 0, 0) | 37 | **55** |
| (0, 1, 0) | 19 | **37** |
| (1, 1, 0) | 73 | **109** |
| (0, 0, 1) | 55 | **19** |
| (1, 0, 1) | 109 | **91** |
| (0, 1, 1) | 91 | **73** |

GPT's `VELOCITY_POLICY = 'shared_rarity'` makes the docstring's claim actually true.

---

## `FOR_CHATGPT.md` (repo root, 2026-09-16)

A review of `dois_13(gpt)` written to be handed to ChatGPT directly, so it can act on the
findings without this conversation. Nine sections: what it got right and how that was
verified; the two defects above; what was not adopted musically and why; which of its
engineering changes are worth taking (round-trip verification against the plan,
`validate_settings` rejecting unknown AND missing keys, `ENGINE_VERSION` in the
fingerprint, bounding the sieve LCM before music21, `Fraction` over float) and which are
not (the ~95-line symlink/generation/lock publication machinery, which created the
duplicate `mid-files/` problem it then had to solve); the governing principles restated;
and the open questions. Its central ask: keep source corrections and musical taste in
SEPARATE, separately-adoptable changes — one is checkable against a source, the other is
only the author's to rule on. GPT acted on this in `dois_14(gpt)`, which makes the
policies independently selectable rather than bundled.

---

## Latest pitched iteration — dois_14(gpt)_pitch

2026-09-14 revision at the user's request: A/B now interpret their own cyclic sieve
gaps as semitone intervals, with C membership preferring upward motion and absence
preferring downward. A deterministic minimum-reversal solver makes the signed sum
exactly zero (six reversals A, one B); no interval sizes change or extra time is added.
C remains A's shifted pitch canon. D ranks position-modulo-12 counts in its own
intersection and assigns one class per raw pass: creative MIDI 38 then 45.

Parent rhythms/gates/velocities remain unchanged: creative 255 notes, 19200 ticks,
20 seconds at 120 BPM; all four rhythm presets retained. Accents remain independent.
Current MIDI in mid/<preset>; initial mapping in mid-initial/<preset> with --initial-pitch.
Channels 1–4, ordinary files, pitched instruments. The initial approach is documented
in INITIAL_APPROACH.md and archived in history/initial-pitch.zip. MUSICAL_DESIGN.md
explains the revision, exact closure, tie breaks and limitations. Diagnostics/manifests
include derivation details. 25 tests cover both designs, gap/closure optimality and MIDI.
Next: audition same-preset initial/current arrangements on the user's instruments.


---

## Latest GPT iteration — dois_14(gpt)

Created at the user's request after reading Claude's FOR_CHATGPT.md. Creative
liberties are authorized when consistent with the principles and explicitly explained.
The corrected source and musical choices are now independently selectable:
reference (note-for-note Claude dois_14), fixed-weather (C's accent phase only),
shared-weather (common state table), creative (default 4:3:2 proposal from GPT 13).
Reference/policy versions have 108/52/108/60 notes; creative has 108/52/81/14.
All end at the first 19200-tick convergence with distinct complete accented passes.
Historical reference policies expose, rather than silently endorse, the weather
inconsistencies discussed in Claude's review.

Exports are ordinary files in dois_14(gpt)/mid/<preset>/, with preset names in filenames.
No symlinks, generations, lock or duplicate browser copy. Temporary output is verified
before replacing files individually; existing real folders and unrelated files are
preserved. An interrupted multi-file replacement needs rerendering. --all creates
all comparisons; --preset selects one; dry-run, diagnostics and verify-only remain.
43 tests cover the independent source/reference, isolated policy changes, creative
structure, MIDI readback and ordinary publication. See MUSICAL_DESIGN.md and
REVIEW_RESPONSE.md in the new iteration. Existing versions are unchanged.

Next: audition the presets in sequence with the user's patches; choose phase,
velocity policy and creative clocks independently. Form/Max work remain parked.

---

## Ableton browser fix — 2026-09-13

Confirmed in Live UI: dois_13(gpt) expanded to show other subfolders but not the
symlinked mid directory. Added automatic ordinary-file export to mid-files/ on
every normal render; this is the folder to browse in Ableton. The managed mid
snapshot/history remains. Forty-four tests pass; note data is unchanged. The user
also reports improper rendering; the specific note/timing/playback symptom has
been requested and is not yet identified. Do not call that broader issue fixed
merely because MIDI-byte checks pass.

---

## Latest GPT iteration — `dois_13(gpt)`: complete sieve and musical redesign

The user requested restoration of the omitted Psappha terms and a creative
implementation within the original principles. Work remains local to this iteration.
The base expression now includes `8@3|8@4|(8@1&5@2)|(8@6&5@1)`: 27 attacks,
not 15, per 40 steps. Source: Besada et al. (2021), DOI 10.3389/fpsyg.2020.611316,
opening sieve S (including 22). Earlier GPT audits established consistency with
existing MIDI, not fidelity to that transcription; the current tests address both.

Current voices: A=complete sieve, B=complement(A), C=shift(A,+13), D=B intersect C.
Units 120/120/160/240 ticks create three rates (4:3:2), with raw periods
4800/4800/6400/9600. First convergence remains 19200 ticks (20 seconds at 120 BPM).
Passes 4/4/3/2 contain 108/52/81/14 notes, 255 in total. Every full rhythm pass is
distinct through accents, and each accented voice has the full minimal period.
Operations use integer step indices before clocks: D is not an actual-time
coincidence detector. Initial rests are intentional; shared origin/end is the rule.

The two shared clause-derived weather sieves remain. Default accent phase is now
`fixed` in local step indices; the canon does not shift its weather. Derived span
accents are 32/32/3/16, with source residues {0,1,7} filtered by modulus. New
`shared_rarity` uses one velocity table for all accented voices, based on weather
rarities and the largest rarity among the required span sieves (29/32 here).
Equivalent states have identical velocity across clocks; all eight states occur.
`per_grid_rarity`/`follow_shift` remain for historical comparisons. Full gates,
1–127 velocity control and 40/16 metadata are retained. No form or Max work added.

Current docs: README.md and MUSICAL_DESIGN.md in the iteration. Forty tests pass,
including the published attack set, independent congruences and all MIDI formats.
Legacy 15-hit tests now load an explicit fixture configuration. Previous code/tests
and MIDI are saved in history/before-full-psappha.zip; previous generations remain.

Next: audition A/B, then C, then D with the user's patches. This is a reasoned
compositional choice tested structurally, not an assertion of an objectively best
sound. Arrangement stays in the DAW. Historical sections below retain superseded
figures; the current code and this snapshot take precedence.

---

## New parallel iteration — `dois_12(gpt)` (2026-09-11)

At the user's request, a new implementation lives in `sifters/dois_series/dois_12(gpt)/`.
It includes the full GPT audit as `REVIEW.md`, a concise local README and changes log,
separate planning/MIDI modules, regression tests, and generated MIDI. The original
`dois_12` and all earlier iterations remain the historical reference.

The baseline musical output is unchanged: 60/100/60/18 notes, 19,200 ticks, 40/16,
120 BPM, gate 1.0. The new version fixes unsafe output replacement, incomplete
readback verification, ignored channels/ensemble metadata, missing first-parity
validation, augmentation's double expansion, and incomplete configuration identity.
Publication stages and verifies an entire generation before switching the `mid`
symlink; prior generations are retained under `.mid-renders/`.

Musical-policy clarification: C intentionally retains a shifted accent field, and
D retains per-grid rarity mapping. These are explicit settings, not a claim of one
identical velocity table or phase-aligned field. The default residues with fixed
weather cause C's passes to repeat and are rejected. Intersections are in integer
step coordinates, before assigning each voice's own time unit. A mathematically
minimal span modulus is a policy: 32 is the smallest M with LCM(40,M)=160, not the
only solution (160 also satisfies it).

Use this variant's README for its current commands, full contract and limitations;
the historical snapshots below contain superseded numerical and policy descriptions.
No new arrangement layer or Max-patch work was undertaken.

---

## Instructions for Claude (read this first, every session)

1. **Read this entire file before doing any work** — it is the source of truth for project state.
2. **At the end of every working session**, update this file with:
   - Any new decisions made and why
   - Any bugs found and fixed (with the root cause, not just the fix)
   - Any new files created or significantly changed
   - Updated "What's Next" checklist — check off completed items, add new ones
   - Updated "Last updated" date at the top
3. **After updating**, commit and push: `git add CONTEXT.md && git commit -m "update CONTEXT.md" && git push origin main`
4. **Never assume** the code matches what this file says — always verify against the actual files before making claims. This file may be days or weeks old.

---

## What This Project Is

A generative MIDI composition system based on **Xenakis sieve theory** — a mathematical framework that uses modular congruences to produce boolean rhythmic patterns. The Python code is a **proof of concept**. The eventual target is a **Max for Live MIDI Effect device** (`.amxd`) for distribution to Ableton users, with a possible VST3/CLAP version via JUCE for broader DAW support.

---

## Governing Principle VII: The Engine Is General; Only Config Is Specific (2026-09-23)

Stated by the author 2026-09-23: *"i don't want it to be hard coded. in other words, I
want to be able to input another sieve and for it to also work."*

**config.py describes THIS composition. Every other file must work for any sieve.** No
module may assume the moduli are 8 and 5, the period 40, the voices four, the units 120
and 160, or the meter 40/16. Everything downstream — note-layer periods, the parity
point, span-accent moduli, spans, meter, fingerprint — is measured or derived from what
config says, and recomputed when config changes.

**The test of this is not an argument, it is a run.** `dois_21/tests/test_dois21.py`
renders a DIFFERENT sieve end to end: moduli 7 and 5, period 35, parity 16800, meter
35/16, all checks passing. If a change breaks generality, that test fails.

**Two things are genuinely per-composition and stay in config**, because they are
compositional choices, not consequences:
- `WEATHER` — which residues of the sieve's own moduli form the shared field;
- `SPAN_RESIDUE_SOURCE` — the residues the derived span accent draws on.

Neither can be inferred from the sieve without inventing a rule. The engine instead
VALIDATES them against the sieve and fails before writing anything if they do not work,
naming a set that would: `python3 compose.py --suggest-span`. That is the bridge — put
in a new sieve, run it, and the program tells you what its accents need.

**A limit worth knowing, found while proving this.** Generality of the ENGINE does not
guarantee the PRINCIPLES can be met by every sieve. A sparse sieve
(`(4@0|4@1)&3@1|4@2`, 5 attacks in 12) has no residue set at all whose span accent can
inflect every pass — Principle IV is unreachable for it at those basic units. The run
refuses, explains, and writes nothing. That is the correct outcome, not a bug.

## Governing Principle IV: The Accent Span IS the Parity Justification (2026-09-05)

> The user: *"I want the piece to be just as long as it takes for the sieves with different
> base units to achieve parity with the other voices. The accent layer should express itself
> fully and without repetition to achieve this... the accent layer should be exactly as long
> as it is needed to justify the repetition of the various voices to achieve parity across
> voices of different basic durational unit. I am taking parity to mean the first time all
> voices converge at the same end point."*

**Parity is the FIRST convergence of the raw rhythms**, and it sets the length of the piece:

```
16th voices   40 x 120 = 4800 ticks
triplet       40 x 160 = 6400 ticks
LCM(4800, 6400) = 19200 ticks   = the piece, 10 bars of 4/4, 4 bars of 40/16
```

Reaching it **forces** repetition: the sixteenth voices state their rhythm 4 times, the
triplet voice 3. The accent span is what redeems that repetition, so it must be **exactly**
long enough to inflect it — no longer, or it would over-run the convergence and repeat
something; no shorter, or a repetition would go unjustified.

**The span is therefore dictated, not chosen:**

| grid | passes needed | required span | modulus that gives it |
|---|---|---|---|
| 16th (120) | 4 | LCM(40, M) = 160 | **32** — the only one |
| triplet (160) | 3 | LCM(40, M) = 120 | **3** |

`160 x 120 = 19200 = 120 x 160`. The accent that MOVES and the accent that BUYS PARITY are
now the same accent, which is why `SPAN_ACCENT` replaced the old separate parity accent.

**This is why the weather holds only static accents.** `sieve5` and `sieve8` have moduli the
sieve itself uses, so they divide its 40-step period and land identically on every pass —
they colour without varying, and crucially they do not lengthen the span. Any *further*
coprime modulus would push the piece past its first convergence. The old `cross3` is gone as
a separate accent: modulus 3 is now the triplet voice's span accent, doing the job it was
always really doing.

**Result:** 8 accent states, all reached; 4 distinct passes in the sixteenth voices, 3 in the
triplet; every voice 19200 ticks; nothing repeated. The piece went from 30 bars to **10** —
the earlier length carried repetition beyond what parity required.

---

## Governing Principle III: One Weather (2026-09-05)

> The user: *"It would be ideal if there was a uniform approach to accent sieves... the
> accent sieve is like the weather that the notes and rhythms fall under. Each voice should
> be under the same weather... It is important that nothing is ever repeated identically.
> Every total cycle of rhythm should find all the voices beginning and starting at the same
> point and should never have any absolute repetition. The accent sieve helps justify
> repetitions to achieve parity."*

**One accent field, shared by every voice.** Accents are not per-voice character. Do not
give a voice its own accent sieves to differentiate it — the uniformity is the point.
*(A suggestion to give voice B the complement of A's accent field was made on 2026-09-05
and is ruled out by this. B sharing A's field is the design, not a weakness.)*

**The accent field licenses repetition.** Parity forces a voice to repeat its note layer —
D states its 40-step rhythm 9 times, A 12 times. Bare, that is literal repetition. Because
the accent moduli do not divide the note-layer period, each pass is inflected differently:
**the rhythm recurs while the music never does.** That is what the accent layer is *for*.

**Nothing may repeat identically.** Two requirements, both verified:

- every voice begins and ends together (parity — Principle II);
- within that cycle no passage exactly repeats another.

Checked 2026-09-05: all 12 passes of A/B/C distinct, all 9 of D distinct, rhythm identical
across passes while velocities never are, and each voice's minimal period equals its full
span so nothing repeats at any sub-length. `verify()` enforces the minimal-period half of
this on every run.

### The one weather is broken in exactly one place, and it is FORCED

Principle III (one weather) and Principle II (parity) cannot both hold across voices on
different basic units. The proof, worth keeping because the conclusion looks like a defect
and is not:

1. Principles (1) *all voices begin and end together* and (2) *nothing repeats identically*
   **jointly force parity.** If periods differed, the cycle where voices align is their LCM
   — longer than the shortest voice, which must then repeat inside it. Parity is not a
   preference; it is what those two demand together.
2. A voice's period is `LCM(note layer, accent moduli) x basic unit`. Voices sharing an
   accent set share that LCM, so their periods stand in the ratio of their units:
   with the current accents, `160 x 120 = 19200` against `160 x 160 = 25600`. Never equal.
3. Therefore parity, one weather, and differing basic units are mutually exclusive. One
   must give.

| give up | cost |
|---|---|
| the polyrhythm | the piece loses its central relationship |
| parity | A repeats **4x** inside a 120-bar ensemble — absolute repetition |
| **one weather** | **D differs in one of four accents; everything else holds** |

The third is the cheapest by a wide margin, and the break is placed in the accent whose
*only* job is to set the period. So `config.py` now separates them explicitly:

- **`WEATHER`** — `sieve5`, `sieve8`. Shared by every voice, no exceptions.
- **`SPAN_ACCENT`** — one per basic unit, and in `dois_12` **derived** rather than
  written: `span32` on the 120-tick grid, `span3` on the 160-tick grid. Not weather; the
  device that lets weather cross grids, and whose length is dictated by the parity point.

*(Written 2026-09-05, when the weather also held `cross3` and the parity accent was a
separate fourth accent. Principle IV then showed the span accent must be exactly as long
as parity requires — which made `cross3` the triplet voice's span accent rather than a
separate layer, and shortened the piece from 30 bars to 10. The reasoning below still
holds; the accent names have moved on.)*

A voice no longer names an accent set at all — it is **assembled** from the weather plus
the one parity accent its unit requires, so a voice cannot be given accents of its own. A
unit with no parity accent defined raises rather than silently rendering out of parity.

`verify()` now enforces all three principles on every run:

```
parity: every voice is 19200 ticks
one weather: ['sieve5','sieve8'] shared by all; span accent differs by grid
A: 4 passes of its note layer, all distinct
D: 3 passes of its note layer, all distinct
```

The pass check matters separately from the minimal-period check: the latter catches
repetition at a *divisor* of the span, but two arbitrary passes could coincide without
making the sequence periodic. Every pass is now compared against every other. All four
sabotage cases were tested and caught.

### Static and moving accents

An accent whose modulus **divides** the note-layer period repeats identically on every pass.
It colours the rhythm but never varies it:

| accent | modulus | divides 40? | role |
|---|---|---|---|
| `sieve5` | 5 | yes | **static** — fixed colour, same every pass |
| `sieve8` | 8 | yes | **static** — fixed colour, same every pass |
| `span32` / `span3` | 32 / 3 | no | **moving** — inflects each pass |

Only the moving accents create non-repetition, and they alone set how many distinct passes
exist: LCM(40,32)/40 = **4** passes for the sixteenth voices, LCM(40,3)/40 = **3** for the
triplet voice. So the polyrhythm exists at the accent level too, not only in the note grid —
A's weather turns over 4 times while D's turns 3, against each other, inside one cycle.

**The cost of more variation is length.** Every accent modulus coprime to the note layer
multiplies the total period. This is exactly why Principle IV fixes the span at the parity
point: any further coprime accent would push the piece past its first convergence and carry
repetition parity never asked for. Depth of variation and total duration are one dial.

---

## Governing Principle II: Parity Through Accent Choice (2026-09-02)

> Stated by the user: *"it is important to try to create accent sieves that create parity
> between durations in the event where the base unit of one voice differs from another."*

This refines — it does not contradict — the principle below. Equal lengths must never be
**imposed** by padding or repeating. But they can be **earned**, by choosing accent moduli
so that voices on different basic units arrive at the same period on their own.

**Identical accent sets cannot do it.** A and D both carried `{5,8,3}` and both landed on
120 steps — but 120x120 = 14400 and 120x160 = 19200. The accent moduli must scale
**inversely to the basic unit**:

```
16th voices  (unit 120): LCM(40, 5, 8, 32) = 160 steps x 120 = 19200
triplet voice (unit 160): LCM(40, 5, 8,  3) = 120 steps x 160 = 19200

160 / 120 = 4/3 = 160 / 120     <- the step counts invert the unit ratio exactly
```

**There is a floor, and the piece now sits exactly on it.** A sixteenth voice's minimum
period is 40x120 = 4800 and a triplet voice's is 40x160 = 6400, so any shared duration
must be a multiple of LCM(4800, 6400) = **19200 ticks**. Nothing shorter is possible, and
Principle IV fixes the piece at that floor rather than any higher multiple — a longer
choice would carry repetition parity never asked for.

**Parity depends only on the moduli — the residues are free.** Change residues freely for
musical reasons; parity survives. But keep them **irreducible**: a set that repeats at a
smaller modulus (`32@0|32@1|32@16|32@17` is really mod 16) silently halves the period, and
**`music21`'s `Sieve.period()` returns the nominal modulus and will not catch it.** Always
confirm with the measured minimal period read back from the rendered MIDI.

---

## Governing Principle: What a Duration Must Express

> Stated by the user on 2026-08-31. **This governs every duration decision in the project.
> Read it before changing any length, and do not trade it away for convenience.**

The sieve is **a catalyst for artistic expression**. Interpreting one musically means:
**where numbers occur as a result of the sieve, so do sounds.**

**The graph-paper analogy.** Picture the sieve plotted on graph paper. The **basic unit of
duration is the equal spacing between the lines**. The **dots are the integers the sieve
produces**, and each dot is a sound. Two things must hold:

1. **Micro — the basic unit.** Every voice places its sounds on a chosen unit of duration,
   so all sounds correspond to equal and matching numerical values expressed by the sieve.
2. **Macro — the periodicity.** A voice's **overall duration must equal the periodicity of
   the sieve**, normally found as the **LCM of all its moduli**. Correct overall duration is
   "essential to maintaining accuracy of the sieve and deeply tied into my artistic goals."

**Equal track lengths are NOT a goal.** In the user's words: *"it is not necessarily
important that every track is exactly the same length."* When voices use different basic
units to create a polyrhythm — as D does with its triplet grid against A/B/C's sixteenths —
they **will** have different total durations. That is correct. Do not "fix" it.

**Two failure modes to avoid:**

- **Extending a voice to match another's length**, or rendering everything at a cross-voice
  LCM so all files match. That makes a voice N periods long rather than one, which no longer
  states the sieve's periodicity. *This mistake was made on 2026-08-31 — see "Every output is
  one LCM span" below, which is now superseded.*
- **Truncating at a length that is not the true period**, cutting the structure
  mid-statement.

Before choosing any duration, ask: **which moduli are actually in play, and what is their
LCM?** Include the accent sieves in that question — see the open issue below.

---

## `dois_11` — hardened rewrite (2026-09-03)

**`dois_11` is `dois_10` with the same rhythms, an audible ghost floor, and code that
checks itself.** Onsets and pitches are identical to dois_10 in all six files; only
velocities differ, and only because the ghost floor moved from 1 to 24.

What it fixes, each a class of silent wrongness dois_10 was open to:

1. **True periods are measured, not declared.** `true_period()` evaluates a sieve over one
   nominal period and finds the smallest length the binary actually repeats on.
   `music21`'s `Sieve.period()` returns the LCM of the moduli written down, which is an
   upper bound: `32@0|32@1|32@16|32@17` reports 32 and truly repeats every 16. dois_10
   would have rendered such a voice at 480 steps — the same material twice, still called
   one period. dois_11 measures 240 and prints a warning naming the expression.
2. **Every voice derives its OWN period**, measured, never declared. dois_10 hardcoded
   `NOTE_LAYER_STEPS = 40`; the first dois_11 derived it but took the *first* voice's
   period as everyone's, which holds only while all voices descend from one sieve. Now:

   - a voice with its own sieve takes that sieve's **measured** period;
   - a derived voice combines its sources over the **LCM of their periods** - sources need
     not share one, so a 40-step and a 35-step sieve intersect over 280 - and the result
     is then **reduced to the period it actually has**, since a derivation can close
     sooner than its sources do;
   - each voice offers one **candidate bar** (a pass of its own note layer at its own
     unit). `shared_meter` takes the finest that divides every length, and returns None
     rather than forcing one when no bar fits, so per-voice meters take over.

   Tested on a config with two independent sieves: A (40 steps), E (35), F = A intersect E
   (280), G = complement of E on a triplet grid. Each derived its own period; no shared
   meter existed so per-voice meters were used (A 40/16, E 35/16, F 70/2); and G correctly
   got none at all, its 5600-tick period having no factor of 3. That config could not
   previously be expressed: E would have been mislabelled 40 steps, and F would have raised
   on sources of unequal length.
3. **Unknown duration names raise.** `'sixteenth note'` or `'Triplet Eighth'` used to
   silently become a sixteenth — the exact shape of the bug that produced the 40/16 meter
   error. Now a `KeyError` naming the voice and listing valid durations.
4. **Derivations dispatch to named operations** in `transformations.py`, which dois_10
   imported but never used, reimplementing `1 - src` and `np.roll` inline. Unknown
   relationships, forward references and mismatched source lengths all raise.
5. **The ghost floor is audible.** `GHOST_VELOCITY = 24`, not 1. "Where a number occurs,
   a sound occurs" — so a step the sieve selects but no accent lands on must still *sound*.
   At velocity 1, 76 of 714 notes were inaudible on a Drum Rack (a sixth of voice D),
   which silently subtracted them from the sieve's statement. The cost is nil: the accent
   weights share a smaller budget and keep the same spread — still 16 distinct velocities,
   still 16.7% on the most common level, range now 24-127 instead of 1-127.
6. **The derivations are asserted.** `check_derivations()` proves each voice really is what
   config says: A matches its own sieve, B is the complement of A (and their union covers
   every step with no overlap), C is a genuine canon (a shift by a whole period is rejected
   as a copy), D is the non-empty intersection of A and C. This is the one class of error
   the file-level checks cannot see — change `shift_amount` to 14 and every clip is still
   one true period, still ends on a bar line, still matches its ensemble track, and the
   piece is no longer the structure it claims to be. Tested by sabotage: replacing B with a
   shift, making D a union, shifting C by a full cycle, and detuning A from its own sieve
   are each caught and named.
7. **Rendered rhythms are checked against the sieve.** `verify()` reads each file's note
   layer back and asserts it equals the binary the sieve produces, and that the file really
   is periodic on it.
8. **Every run verifies itself.** `verify()` re-reads the written files and asserts what
   the project promises: each file is exactly one true minimal period (not a repeat of
   something shorter, not a truncation), every clip ends on a bar line, every note is one
   step long and on the grid, no hanging notes or same-pitch overlaps, meter and tempo as
   intended, and every cycle inside both ensemble files identical to that voice's own file.
   A failure lists each problem and exits non-zero. A voice defined by a sieve is now
   EVALUATED over its full span rather than tiled, and `tile_to()` refuses a span a note
   layer does not divide, so the tiling assumption is removed rather than relied upon.

Point 5 is the important one. **Every bug in this project's history was caught by a
throwaway script that was then discarded**, so the next regression went unnoticed until
someone thought to look. Those checks now run on every render, against the bytes on disk.

`dois_10` is left as it stands. New work should happen in `dois_11`.

---

## `dois_12` — the production version (2026-09-07)

**Same music as dois_11** — all six files identical note-for-note — with the four
things that stood between the code and actually producing with it.

**1. The span accent is fully derived, modulus AND residues.** dois_11 wrote 32 and 3
by hand; they are correct for a 40-step note layer and silently wrong for any other — the
last hand-picked numbers in the system. `required_modulus()` computes the smallest M with
`LCM(layer, M) = P / unit`, and the residues are `SPAN_RESIDUE_SOURCE` (clause 1's mod-8
residues) kept where they fall below that modulus. The derivation reproduces 32 with
{0,1,7} and 3 with {0,1} exactly, and follows a change of layer:

| note layer | parity | 16th-grid modulus | residues |
|---|---|---|---|
| **40** (current) | 19200 | **32** | `32@0\|32@1\|32@7` |
| 35 | 16800 | 4 | `4@0\|4@1` |
| 24 | 11520 | 32 | `32@0\|32@1\|32@7` |
| 20 | 9600 | 16 | `16@0\|16@1\|16@7` |

**2. Rendering no longer empties the output directory.** dois_11 deleted every `.mid`
in `mid/` on each run, destroying anything saved or edited there. `clear_our_outputs()`
replaces only the six files it is about to write and reports what it left alone. Verified
with a foreign file in the folder: it survives.

**3. Every track carries provenance.** A `text` meta event with title, date, config
fingerprint, parity point, tempo, weather, the sieve, the voice and its accents:

```
dois_12 2026-09-07 cfg=52ab7f83 parity=19200 tempo=120 weather=sieve5+sieve8
sieve=(8@0|8@1|8@7)&(5@1|5@3)|... voice=A accents=sieve5+sieve8+span32
```

`config_fingerprint()` is a SHA-256 prefix over everything that determines the output.
Tested: it changes for tempo, weather residues, span residue source, the base sieve, a
voice's shift amount, and a voice's basic unit — and returns to the baseline when they do.

**4. Retrograde and augmentation are wired up.** `transformations.py` had
`reverse_binary` and `stretch_binary` with nothing dispatching them. Both are now
relationships. Augmentation lengthens the note layer (A stretched by 2 states itself over
80 steps), which changes that voice's period and hence its span accent — handled, because
layers are per-voice and span accents are now derived per voice. That is precisely why the
moduli had to stop being hardcoded.

### Note gate — a device question, not a file question (2026-09-10)

**`GATE_RATIO = 1.0` is the default: a note fills its step, so consecutive notes abut.**

Briefly changed to 0.5 on 2026-09-08 after consecutive notes failed to sound on a hardware
synth, then reverted when the user established the decisive fact: **the same files
articulate correctly in Ableton through samples.** The MIDI was never at fault.

- **The file's structure was always correct.** Verified at the byte level, bypassing mido:
  100 note-ons and 100 note-offs in voice B, real `0x8n` messages rather than the
  `0x9n`-with-velocity-0 shorthand, every note closed before its pitch sounds again,
  nothing hanging. The note-off correctly precedes the note-on when they share a tick —
  the documented convention, since note-off first starts a new note while note-on first
  gives a zero-length one.
- **Abutting is legal but not guaranteed to retrigger.** The MIDI specification leaves it
  to the DEVICE whether a Note On for a sounding pitch retriggers or is absorbed. There is
  no correct behaviour to appeal to, which is why samples were fine and the synth was not.
- **A full gate is the structurally truthful reading.** A and B are complements; only at
  gate 1.0 do they tile time continuously, every tick covered by exactly one of the pair.
  0.5 silently discarded that.
- **Two real conventions exist.** 100% is the modern digital default (Logic's Step
  Sequencer); ~50% is the classic analogue gate (TB-303), chosen so fast repeated notes
  read as distinct events.
- **A survey of 196 local MIDI files did not settle it.** Ableton's factory packs appear to
  abut 100% of the time, but that is an artifact — they hold a fixed length of about one
  quarter note, which only *looks* like abutting at quarter spacing, and they contain zero
  repeated notes at 16th spacing. A 50% figure from score exports is Finale's export
  default. Neither is a considered choice about material like this.

**If a device absorbs the retrigger**, set `GATE_RATIO` below 1.0 — 0.5 is the classic
value and retriggers on anything — or use Ableton's Note Length MIDI effect, which
overrides durations per track at playback and leaves the file intact.

`verify()` enforces that notes never OVERLAP and reports how many abut, so the condition is
visible rather than silent: A 16, B 56, C 16, D 3.

### What is still NOT in the code, deliberately

**There is no form.** The output is one 19200-tick statement — 10 bars, 20 seconds at 120
BPM, 238 notes across four drum pads. It is correct, verified material, not a track.
Arrangement, development and variation across a piece live above this layer and are not
attempted here. `dois_09` had that layer (5 movements x 8 sections); this lineage
deliberately stripped it out to get the material right first.

**Tempo and meter are largely moot in Ableton**, which uses the project's own and reads a
19200-tick clip as 10 bars of whatever you are in. They matter for notation software and
other hosts.

---

## Current State — read this for the snapshot (2026-09-07, superseded 2026-09-16)

**Current version: `dois_24`** — see the top of this file. The snapshot below describes
`dois_12` and remains accurate FOR `dois_12`, which is still the last version whose sieve
was the truncated 15-attack form. Read it as history, not as current state. What changed
since:

- **`dois_14`** corrected the sieve (15 -> 27 attacks), which rewrote all four voices;
  note counts below (60/100/60/18) became 108/52/108/60.
- **`dois_15`** derives pitch from the sieve's 8x5 lattice, so voices no longer sound one
  fixed pad each. The merged file now separates voices by MIDI CHANNEL, not by pitch.
- Two defects in this code are **unresolved** — the accent roll on shifted voices and the
  velocity table that is not actually shared. Both documented at the top.

Verified against the rendered MIDI, not from memory.

| Voice | Pad | Basic unit | Note layer | Passes | Span | Period | Notes |
|---|---|---|---|---|---|---|---|
| A | 36 (C1) | 16th (120) | 40 steps | 4 | 160 steps | 19200 | 60 |
| B | 37 (C#1) | 16th (120) | 40 steps | 4 | 160 steps | 19200 | 100 |
| C | 38 (D1) | 16th (120) | 40 steps | 4 | 160 steps | 19200 | 60 |
| D | 39 (D#1) | triplet 8th (160) | 40 steps | 3 | 120 steps | 19200 | 18 |

- **Every file is 19200 ticks** — 4 bars of 40/16, equivalently 10 bars of 4/4, 20 seconds
  at 120 BPM. That is the parity point: the *first* moment the raw rhythms converge,
  LCM(4800, 6400).
- **Accents:** the weather is `sieve5` (`5@1|5@3`) and `sieve8` (`8@0|8@1|8@2|8@5|8@6`),
  shared by every voice. Each voice adds one **span accent**, derived: `span32`
  (`32@0|32@1|32@7`) on the sixteenth grid, `span3` (`3@0|3@1`) on the triplet grid.
- **Velocity:** 8 levels, `1 19 37 55 73 91 109 127`, evenly spaced 18 apart across the
  full range. Each voice reaches 6 of the 8; all 8 appear across the piece.
- **Note gate:** `GATE_RATIO = 1.0` — a note fills its step, so consecutive notes abut
  (16 pairs in A, 56 in B, 16 in C, 3 in D). Correct, and what lets the A/B complement
  pair tile time continuously. Lower it only for a device that will not retrigger from a
  zero-length gap — see "Note gate" below.
- `dois_12_arrangement.mid` — 4 tracks, 238 notes. `dois_12_drumrack.mid` —
  1 track, 238 notes on pads 36-39.
- A per-voice file is **identical note-for-note** to its arrangement track and drum rack
  pad — that is what makes them usable as a reference for checking the ensemble.
- Config fingerprint of this state: **`cfg=52ab7f83`**, stamped in every track.
- `max/sieve.js` (in dois_10) is **PARKED and stale**. Ignore it.

### Ready to produce with — verified 2026-09-07

Checked as a DAW sees the files, not as the code reports them:

| check | result |
|---|---|
| all six files, valid MIDI type 1, 480 tpq | yes |
| every file exactly 19200 ticks / whole bars | yes |
| pads 36-39 = C1, C#1, D1, D#1, Drum Rack pads 1-4 | yes, 60/100/60/18 notes |
| hanging notes, overlapping notes, zero-length notes | **none in any file** |
| note-ons matched by real `0x8n` note-offs | yes — 60/100/60/18 each, no velocity-0 shorthand |
| every onset on its voice's tick grid | yes |
| per-voice file == arrangement track == drum rack pad | yes, all four |
| re-render byte-identical | yes — deterministic |

Re-confirmed 2026-09-10 by parsing the raw MIDI bytes directly, without mido and without
the project's own `verify()`, so the check does not depend on the code it is checking.

**Which file to use.** `dois_12_drumrack.mid` on one track with a Drum Rack is the
plugin-ready form. `dois_12_arrangement.mid` is the same content split across four
tracks for independent processing. The `_prime` files are single voices.

**Tempo and meter.** Ableton uses the project's tempo, not the file's, so the clip is 40
quarter notes at whatever tempo is set. The files declare **40/16** — musically meaningful
(one bar = one pass of the note layer) but unusual. 19200 ticks is *also* exactly 10 bars
of 4/4, so if 40/16 disturbs a session, switching costs nothing musically: one line in
`config.py`.

**Re-running is safe.** `python composition.py` replaces only its own six files and leaves
anything else in `mid/` alone, so bounces and edits kept there survive.

**What is deliberately absent: form.** This is 20 seconds of verified material, not a
track. Repetition, variation, entrances and exits are not attempted by the code and are
being built in Ableton for now, by choice — the material was got right first.

### Session log — 2026-08-27 to 2026-09-02

Roughly in order, and each entry is a thing that is now true:

1. **Drum Rack output.** Added the merged single-track clip on pads 36-39.
2. **One derived pitch per voice.** `root` is derived from position (`DRUM_RACK_BASE + i`)
   instead of a pitched voicing and a pad kept in sync by hand.
3. **Time signature bug.** D declared 40/16 — a 4800-tick bar — for a 6400-tick clip. The
   cause was a silent `.get(step_ticks, 16)` fallback fabricating a meter for a triplet grid.
4. **Uniform meter and tempo**, then **per-voice meters**, then **uniform again.** Tempo was
   absent entirely and is now stated (120 BPM). The meter went 40/16 → 4/4 → per-voice →
   40/16 as the constraints changed; the final 40/16 is the project's original meter and is
   correct because 40 sixteenths *is* one pass of the note layer.
5. **Duration states periodicity.** The governing principle, from the user. Two mistakes were
   made and reverted: rendering every file at a cross-voice LCM, and filling the ensemble
   files by repetition while the per-voice files stayed at one period (which broke the
   prime-vs-ensemble comparison).
6. **The accent layer spans the note layer.** Accents were being evaluated over 40 steps and
   restarting each repeat. They now run their own period, so the same rhythm is re-accented
   on each pass.
7. **D gained an accent layer**, which supplied the factor of 3 its meter needed.
8. **Parity through accent choice.** Accent moduli now scale inversely to the basic unit, so
   all four voices reach 57600 on their own. B is no longer flat.
9. **Graded overlap velocities.** Overlaps of 2+ used to collapse to 127; with four accent
   layers that put 78% of A's notes at full velocity. Each count now has its own level.
10. **`max/sieve.js` was invalid JavaScript** — the generator emitted a literal `\n` between
    entries. Found only by executing it (`osascript -l JavaScript`, since `node` is absent).
    Fixed, then the whole Max effort was parked.

### Verification habits that caught real bugs

- **Read the rendered MIDI back**, never trust the config or the code's own report.
- **Measure the minimal period** rather than trusting `music21`'s `Sieve.period()`, which
  returns the nominal modulus and misses a reducible residue set.
- **Execute generated code**; inspecting its data is not the same as knowing it parses.
- **Compare byte-for-byte before and after** a refactor that should not change output.
- **Check every cycle**, not just the first, when something repeats.

---

## Core Concept: How Sieves Work

A sieve is expressed as boolean combinations of modular congruences. For example:
- `5@0` means "every position where `n mod 5 == 0`"
- `8@1|8@7` means "positions where `n mod 8 == 1` OR `n mod 8 == 7`"
- `&` = intersection, `|` = union, complement = `1 - binary`

The following **historical partial Psappha-derived sieve** was used through the first
GPT iterations; it omitted four terms. The complete formula and current configuration
are documented at the top of this file and in dois_13(gpt)/MUSICAL_DESIGN.md:
```
(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))
```
This produces a period of **40 steps** — the foundational unit of the project.

`music21.sieve.Sieve` evaluates these formulas into binary arrays.

---

## Naming convention for the dois series (2026-09-07)

**Versions are `dois_NN`, zero-padded to two digits.** `dois_01` through `dois_24` in Claude's line, `dois_23(gpt)` in GPT's, so the
folders sort in the order they were made and the newest is always last.

**Two parallel lines now share the numbering.** Folders suffixed `(gpt)` are ChatGPT's
iterations; bare `dois_NN` are Claude's.

**Rule, from the author (2026-09-19): keep the two lines distinct.** Neither assistant
edits the other's folders. To fix or extend the other's version, fork it into a new
folder of your own line — as `dois_15(gpt)` forked `dois_15` — and leave the original as
its author pushed it. Output filenames follow the folder (TITLE `dois_16(gpt)` gives
`dois_16(gpt)_*.mid`), so clips from the two lines never collide in a DAW. Commit each
assistant's work separately, and mark GPT's commits `[GPT]`. This rule exists because
GPT, at the author's request, once edited `dois_16` in place; that work was moved to
`dois_16(gpt)`. They are NOT the same work and the numbers do not
correspond — `dois_14` (Claude's minimal sieve correction) and `dois_14(gpt)` (GPT's
multi-preset version built after reading `FOR_CHATGPT.md`) are different things that happen
to share a number. Check the suffix before assuming which is meant.

The spelled-out names sorted uselessly — `dois, dois_eight, dois_eleven, dois_five,
dois_four, dois_nine, dois_seven, dois_six, dois_ten, dois_three, dois_twelve, dois_two`.
Alphabetical order and creation order had almost nothing in common, so finding the current
version meant reading the docs rather than the directory.

Renamed retroactively on 2026-09-07: 12 folders, 95 MIDI files, 11 `TITLE` constants, and
every reference in CONTEXT.md and README.md. **`dois_01` keeps `TITLE = 'psappha'`** — its
outputs are named after the piece, not the folder, and always were.

**Two traps if this is ever done again.** `_` is a word character, so `\bdois_ten\b` does
NOT match in `dois_10_A_prime.mid` — a word-boundary pattern silently renames nothing. And
chained `re.sub` calls will re-match: replacing `dois_ten` then `dois` turns `dois_10` into
`dois_01_10`, and `dois_series` into `dois_01_series`. Use ONE alternation ordered
longest-first so each position is replaced exactly once, allow `_` after a version but not
after bare `dois`, and test the pattern against known cases before touching any file.

---

## Repository Structure

```
sifters/
  sifters/
    dois_series/          ← all dois_01 versions live here
      dois_01/               ← original (v1)
      dois_02/
      dois_03/         ← best-sounding version; reference for voice design
      dois_04/
      dois_05/
      dois_06/
      dois_07/
      dois_08/
      dois_09/          ← arrangement version of dois_03 (5 movements × 8 sections)
      dois_10/           ← superseded by dois_11; kept as it stands
      dois_11/        ← superseded by dois_12
      dois_12/        ← CURRENT FOCUS — production version
        config.py
        composition.py
        transformations.py
        mid/              ← generated MIDI files (git-tracked)
        max/
          sieve.js        ← PARKED 2026-08-31 — not part of the pipeline, ignore
```

---

## The `dois_10` version — superseded, kept for reference

> **This section describes `dois_10` as it stands, not the current version.** Its figures
> (57600 ticks, 480/360-step spans, four accents, 12 and 9 passes) are correct *for that
> version* and are not the current state — see "Current State" above for `dois_12`.
> `dois_10` remains on disk and is the version whose 30-bar length and four-accent field
> are worth comparing against by ear.

### Current Focus: `dois_10`

The active project. A stripped-down, plugin-oriented version that generates a single **40-step rhythmic beat** from the psappha sieve. No arrangement layer, no shift library — just the four core voices at their prime.

### Four Voices

| Voice | Relationship | Density | Pitch / Drum Pad | Step Grid | Note layer | Full statement |
|-------|-------------|---------|-----------|-----------|------|------|
| A | Base sieve | 15/40 (37.5%) | 36 (C1) — pad 1 | 16th (120 ticks) | 40 steps | **160 steps = 19200 ticks** |
| B | Complement of A | 25/40 (62.5%) | 37 (C#1) — pad 2 | 16th (120 ticks) | 40 steps | **160 steps = 19200 ticks** |
| C | A shifted +13 steps (canon) | 15/40 (37.5%) | 38 (D1) — pad 3 | 16th (120 ticks) | 40 steps | **160 steps = 19200 ticks** |
| D | Intersection of A and C | 6/40 (15%) | 39 (D#1) — pad 4 | Triplet 8th (160 ticks) | 40 steps | **120 steps = 19200 ticks** |

All four are in duration parity at 19200 ticks — the parity floor. D reaches it in fewer
steps because its steps are wider. See Governing Principles II and IV at the top.

Each voice has **one** pitch, used by every output. See "Pad assignment is derived" below.

A + B always fill all 40 steps with no gaps and no collisions (they are complements).
C is a rhythmic canon of A — same pattern, delayed by 13 steps.
D is sparse — only 6 hits per cycle, at the 6 steps where A and C coincide simultaneously.

### Active Step Positions (verified from Python)

```
A: [0, 1, 8, 10, 13, 14, 16, 22, 23, 25, 29, 31, 33, 37, 38]
B: [2,3,4,5,6,7,9,11,12,15,17,18,19,20,21,24,26,27,28,30,32,34,35,36,39]
C: [2,4,6,10,11,13,14,21,23,26,27,29,35,36,38]
D: [10, 13, 14, 23, 29, 38]
```

### Accent Voicing — derived accents, ranked over occurring states (2026-09-05)

**Four accents per voice, and each one means something.**

| accent | expression | what it is |
|---|---|---|
| `sieve5` | `5@1\|5@3` | clause 1's mod-5, **verbatim from the sieve** |
| `sieve8` | `8@0\|8@1\|8@2\|8@5\|8@6` | clauses 2+3's mod-8, **verbatim from the sieve** |
| `cross3` | `3@0\|3@1` | modulus 3 — **absent from the sieve**, deliberately foreign |
| `span32` / `span9` | | the parity accent; carries `sieve8`'s / `cross3`'s residues up to a new modulus |

The psappha sieve, clause by clause:

```
clause 1   (8@0|8@1|8@7) & (5@1|5@3)        mod-8 {0,1,7}   mod-5 {1,3}
clause 2   (8@0|8@1|8@2) & 5@0              mod-8 {0,1,2}   mod-5 {0}
clause 3   (8@5|8@6) & (5@2|5@3|5@4)        mod-8 {5,6}     mod-5 {2,3,4}
```

`sieve8` = clauses 2+3's mod-8 = every mod-8 residue the sieve uses except 7. `sieve5` =
clause 1's mod-5. Between them they reference all three clauses: **the sieve accents its
own vocabulary.** `cross3` is the deliberate outsider — modulus 3 appears nowhere in the
sieve, which is exactly why it does not divide the 40-step note layer, and so is what
makes the accent field land differently on each pass and carries the factor of 3 the
triplet voice's period needs.

**Two mistakes were made here and are recorded so they are not repeated.** `sieve8` was
`wide8` and had been written `8@0|8@1|8@2|8@5|8@6` since dois_02. On 2026-09-03 it was
thinned to `8@0|8@1|8@5` purely because that measured better, and then dropped entirely.
{0,1,5} matches no clause — the thinning **turned a derived object into a hand-picked
one**, and dropping it removed the sieve's mod-8 self-reference from the accent layer.
The former `low5` (`5@0|5@1`) was equally arbitrary: the two lowest residues, matching no
clause. It is now `sieve5`. Same density, so nothing about the ordering changed — it just
means something now.

**Velocity: one shared table, ranked by rarity, spread across the whole 1-127 range.**

```
1  9  18  26  35  43  51  60  68  77  85  93  102  110  119  127     16 levels, 8-9 apart
rarity order: cross3 < sieve8 < sieve5 < span32/span9
```

**Every voice uses this same table.** It depends only on the accent set, never on which
states a particular rhythm happens to reach, so a given combination of accents means the
same velocity everywhere in the piece. Velocity is a property of the sieve structure, not
of the notes it lands on. All 16 states are ranked, including any this piece never reaches.

Ordering is derived — an accent contributes its rarity `(1 - density)`, so a sparse accent
outranks a common one and more accents outrank fewer. Only the spacing is imposed, and
evenly, because proportional spacing let accents of similar density earn near-identical
weights and rendered genuinely different states 1 velocity apart.

**`MIN_VELOCITY` is 1, not 0.** MIDI defines a note-on of velocity 0 as a note-off, so
velocity 0 would delete the note rather than sound it faintly. 1 is the quietest a note can
be and still exist. Verified: zero velocity-0 note-on events in any file.

### The parity accent must be INDEPENDENT (2026-09-05)

Four of the sixteen accent states were unreachable — **by construction, not by accident.**

The parity accents were derived by carrying a parent's residues up to a higher modulus:
`span32` was `sieve8`'s {0,1,2,5,6} at modulus 32, `span9` was `cross3`'s {0,1} at
modulus 9. That looked elegant and guarantees the wrong thing: when the residues are
smaller than the parent's modulus, **every** n congruent to 0,1,2,5,6 mod 32 is also
0,1,2,5,6 mod 8. So `span32` could never fire without `sieve8` — measured, 0 steps out
of 480 — and `span9` never without `cross3`. The parity accent was not an independent
layer at all; it only subdivided its parent, and 4 states could never occur.

**The rule: a parity accent takes some residues its parent covers AND at least one it
omits**, so it fires both with and without it.

- `sieve8` is clauses 2+3's mod-8 {0,1,2,5,6}. Clause 1's is {0,1,7}. Lifting *clause 1*
  to modulus 32 gives **`32@0|32@1|32@7`** — it shares 0 and 1 with `sieve8` and adds 7,
  which `sieve8` omits. Still derived from the sieve, and independent of `sieve8` for
  precisely the reason it is derived: clause 1 is the clause `sieve8` leaves out. The two
  accents together now cover all three clauses' mod-8 vocabulary.
- `cross3` is foreign to the sieve, so its partner follows the rule rather than a clause:
  **`9@0|9@2`** shares residue 0 with `cross3` and adds 2, which `cross3` omits.

Moduli are unchanged (32 and 9), so every period and the duration parity are untouched.

**Result: all 16 levels now appear in the piece**, up from 13. Each voice reaches 12 of
the 16 — a voice only meets the states its own rhythm coincides with, and no arrangement
of a *shared* table can make every voice reach every state.

| | levels used | range |
|---|---|---|
| A, C, D | 12 of 16 | 18-127 |
| B | 12 of 16 | 1-102 |
| whole piece | **16 of 16** | 1-127 |

### A wrong assumption, corrected (2026-09-05)

Between 2026-09-03 and 2026-09-05 the velocity design was built on the premise that
**velocity means volume**, and that a low-velocity note would therefore go unheard. That
produced two changes which have now been reverted:

- a raised floor of 24, on the grounds that ~10% of notes were "inaudible" at velocity 1;
- wide spacing (and briefly, dropping an accent entirely to get it), on the grounds that
  differences under about 8 could not be resolved.

**The premise was wrong.** The user's note, 2026-09-05: *"When creating the synth patches
velocity is not necessarily directly tied to volume. I can use velocity to tie many other
attributes in the sound design process utilizing software synths."* Velocity here drives
filter cutoff, envelope times, sample layer — whatever a patch maps it to. A low-velocity
note is not a quiet note that might vanish; it is a **different sound**. So there is no
audibility floor to protect, no just-noticeable-difference to spread levels around, and no
reason to withhold range from a state the current rhythm happens to miss.

The lesson worth keeping: the audibility reasoning was sound engineering applied to a
premise never checked with the person who knew. Ask what velocity is *for* before
optimising what it looks like.

Voices use different subsets of the shared table, which is expected — a voice reaches only
the accent states its rhythm coincides with. A, C use 10 of 16; B uses 12; D uses 9. The
*values* are identical; only which of them occur differs.

### Velocity Arrays

A and C carry **120-step** velocity arrays, B and D 40-step. They are not transcribed
into this file — they are long, and every past attempt to keep a copy here drifted out
of date. **The authority is `composition.py` and the `mid/` files it writes.** To read
the arrays, run the script and inspect the output.

### Polyrhythm and LCM

D uses triplet eighth notes (160 ticks/step) while A/B/C use sixteenth notes (120 ticks/step). This creates a 4:3 polyrhythm. Full alignment:

```
A full statement: 480 × 120 = 57600 ticks   (accents span 12 note-layer iterations)
B full statement: 480 × 120 = 57600 ticks   (12 iterations)
C full statement: 480 × 120 = 57600 ticks   (12 iterations)
D full statement: 360 × 160 = 57600 ticks   ( 9 iterations, wider steps)
```

**All four voices are in duration parity**, so the ensemble is 57600 ticks = 12 bars of
40/16 and contains exactly **one statement of each voice** — nothing repeats inside it.
The 4:3 relation between the 16th and triplet-8th grids still drives the polyrhythm; the
parity accents are what bring the two grids to a common period.

The rule this preserves: an ensemble may only ever contain **whole repetitions** of a
voice's period, never a padded or truncated one. It happens to be ×1 for every voice now,
but the rule is what keeps the per-voice files valid as a reference.

### Generated Files

Each per-voice file is **exactly one full statement** of that voice — which means they
are deliberately different lengths. See the Governing Principle at the top.

- `dois_10_A_prime.mid` — 57600 ticks (12 bars), 480 steps, 180 notes
- `dois_10_B_prime.mid` — 57600 ticks (12 bars), 480 steps, 300 notes
- `dois_10_C_prime.mid` — 57600 ticks (12 bars), 480 steps, 180 notes
- `dois_10_D_prime.mid` — 57600 ticks (12 bars), 360 steps,  54 notes
**A per-voice file is one period. The ensemble files repeat those same periods, whole,
until every voice finishes together** — 57600 ticks, the LCM of the voice periods
(A ×4, B ×12, C ×4, D ×9). No voice's internal period is altered to fit; it simply recurs,
so any single cycle inside an ensemble file is identical to that voice's own file.

- `dois_10_arrangement.mid` — 57600 ticks (30 bars), four tracks, all ending together
- `dois_10_drumrack.mid` — 57600 ticks (30 bars), all four voices merged onto a **single
  track** at Drum Rack pitches 36/37/38/39. The plugin-ready format: drop it on one Ableton
  track holding a Drum Rack.

### Drum Rack Output (added 2026-08-27)

The drum rack clip holds the same material as the arrangement, merged onto one MIDI
track. Same notes, same pitches, one track instead of four:

- **One track, not four.** All voices become a single absolute-time event stream.
- **Meter and tempo come from the shared header**, same as every other track — see
  "Uniform meter and tempo" below. The ensemble period is exactly 30 bars of 4/4.
- **Event ordering matters.** Events sort by `(tick, kind)` with `note_off` (kind 0)
  ahead of `note_on` (kind 1), so a pad retriggering on consecutive steps releases
  before it strikes again instead of being cut short by the previous note's release.

### Pad assignment is derived (2026-08-28)

Each voice has exactly one pitch, and it is **not written per instrument**. `config.py`
assigns it from the voice's position in `INSTRUMENT_CONFIGS`:

```python
DRUM_RACK_BASE = 36  # C1 = Drum Rack pad 1
for _i, _cfg in enumerate(INSTRUMENT_CONFIGS):
    _cfg.setdefault('root', DRUM_RACK_BASE + _i)
```

A → 36, B → 37, C → 38, D → 39, and a fifth voice would get 40 for free. A voice can
still pin its own by setting `'root'` explicitly.

**Why derived rather than two values.** The first version of this carried both `root`
(a pitched voicing: 36/55/48/60, inherited from dois_03) and `drum_root` (the pad).
That meant the prime clips and the drum rack clip played *different notes* for the same
voice — B was G3 in `B_prime.mid` but C#1 in the drum rack — so comparing them in
Ableton showed the same rhythm on different rows, and the two values could drift apart
silently. One derived value makes every output agree by construction; there is no
second place for the mapping to be wrong.

The pitched voicing is gone. If it is ever wanted back, it belongs as a separate render
target (a `pitched=True` flag on the save call), not as a parallel field that has to be
kept in sync by hand.

Verified on 2026-08-27 by reading the file back with mido: 1 track, correct span, 4/4,
no hanging notes, no same-pitch overlaps, onset positions equal to the sieve steps on
each voice's own grid, and per-pad velocities identical to the arrays in `max/sieve.js`.
*(Tick counts in that check were the then-current 19200; the structure of the check
still holds and has been re-run against each later version of the files.)*

### Time Signature Bug Fixed (2026-08-27)

**Symptom:** `dois_10_D_prime.mid` declared `40/16`, but that meter describes a
4800-tick bar while D's clip is 6400 ticks — the file asserted it was 1-1/3 bars long.

**Root cause:** `generate_time_signature` did
`STEP_TICKS_TO_DENOMINATOR.get(step_ticks, 16)`. That table holds only power-of-two
divisions (1920 → 60). D's 160-tick triplet-eighth step is not in it, so the silent
`, 16` default fabricated a sixteenth-note meter for a triplet grid.

**Why it cannot be fixed by choosing better numbers:** a meter `N/D` spans
`N * (4 * TPQ / D)` ticks with `D` a power of two. D's cycle is 6400 ticks = 13-1/3
quarter notes, needing `N/D = 3.333…` — N = 13.33 at D=4, 26.67 at D=8, 53.33 at D=16.
No power-of-two meter expresses a third of a beat, so **no time signature describes
D's cycle at all.** That is inherent to the triplet grid, and it is the same 4:3
relationship that drives the polyrhythm.

**First fix (2026-08-27):** the fallback stopped guessing — an unlisted step size
returned `4, 4`, so D read as 3-1/3 bars of 4/4 (honest) rather than 1-1/3 bars of
40/16 (false).

**Superseded (2026-08-30):** `generate_time_signature` no longer exists. Every track
now declares the same meter, so there is nothing left to derive per voice. See below.

### Meter states the period (2026-09-01, unified 2026-09-02)

**A clip must end on a bar line, or the host extends it.** Ableton fills the remainder of
the measure, so a clip whose length is not a whole number of bars is silently padded and
no longer ends at the sieve's period. The fix is to give each voice **its own meter,
derived from its own grid**: the beat is the voice's basic unit, and the bar is one pass
of the 40-step note layer.

```python
meter_for_unit(step_ticks, NOTE_LAYER_STEPS)   # 120-tick unit -> 4*480/120 = 16 -> 40/16
```

`meter_for_voice` has two preferences:

1. **The beat is the voice's basic unit**, bar = one pass of the note layer. A 16th grid
   gives `4*480/120 = 16`, so 40 steps is **40/16** — one bar per statement of the rhythm.
2. **For a grid that cannot be a beat** (a triplet gives `4*480/160 = 12`, not a valid
   denominator), any meter whose **bar equals the voice's full period**. D's 19200 ticks
   is exactly 40 quarter notes, so **40/4**: the beat is no longer D's own unit, but the
   bar still lands precisely on the period, which is all that stops the host padding.

**Everything is 40/16** — one meter across every voice and every file, with every clip
still ending exactly on a bar line:

| Voice | Unit | Steps | Meter | Period | Bars |
|---|---|---|---|---|---|
| A | 16th (120) | 480 | 40/16 | 57600 | 12 — exact |
| B | 16th (120) | 480 | 40/16 | 57600 | 12 — exact |
| C | 16th (120) | 480 | 40/16 | 57600 | 12 — exact |
| D | triplet 8th (160) | 360 | 40/16 | 57600 | 12 — exact |
| arrangement, drumrack | — | — | 40/16 | 57600 | 12 — exact |

**All four voices are in duration parity at 19200 ticks** — the parity floor, see
Governing Principles II and IV. The ensemble is exactly **one statement of every voice**:
each appears x1, nothing repeats.

**A shared meter only became possible when D gained its accent layer.** The bar must
divide every period, and `gcd(14400, 4800, 19200) = 4800` — so 40/16 fits. With D's old
6400-tick period the gcd was 1600 and no meter with a 4800-tick bar could work, which is
why per-voice meters were needed on 2026-09-01. Extending D's period to 19200 removed the
obstruction.

`shared_meter()` is tried first and used when it fits every length; `meter_for_voice()`
remains as the per-voice fallback if a future change breaks the shared case. D is a triplet
voice inside a sixteenth-based meter, which is simply how triplets are always notated — the
bar lines land correctly, the subdivisions sit between them.

**This restores something that was removed and should not have been.** The project used
40/16 from the start, precisely because 40 sixteenths *is* one period. It was flattened to
a uniform 4/4 on 2026-08-30 at the user's request for consistent metadata — which was a
real request, but the cost was that every prime clip stopped landing on a bar line. Meter
here is not decoration; it is what makes the host agree with the sieve about where the
period ends.

### Voice D's accent layer (added 2026-09-02) — and why it was the fix

D used to be flat velocity 64 with a 40-step period of 6400 ticks, and **no meter could
put a bar line there.** A bar is `N * (4*TPQ/Den)` with `Den` a power of two, and
`4*480 = 1920 = 2^7 x 3 x 5` always carries a factor of 3, while `6400 = 2^8 x 5^2` has
none — so no bar length could divide it, independent of TPQ. Ableton padded it to 7680.

**The fix was to give D the same accent set as A and C.** That is not a workaround; the
factor of 3 the meter needs is exactly the factor the mod-3 accent supplies:

```
D period = LCM(40 rhythm, 5, 8, 3 accents) = 120 steps x 160 ticks = 19200 ticks
         = 40 quarter notes = one bar of 40/4     <- exact
```

On D's triplet grid the mod-3 accent falls every 3 steps = 480 ticks = **exactly one
quarter note**, so it accents the beat. The same modulus that fixes the meter is also
musically the most natural accent D could carry.

D now has 18 notes over 120 steps (was 6 flat notes over 40), re-accented on each of three
passes of its 6-hit rhythm:

```
steps:  10   13   14   23   29   38
it 1:  127  127   63    1   63   63
it 2:  127   63  127   94  127  127
it 3:  127  127  127   94  127  127
```

The ensemble length did not change — D simply repeats 3x instead of 9x within the same
57600 ticks.

### Uniform meter and tempo (2026-08-30, meter part superseded)

**Tempo is still uniform: 120 BPM on every track.** The *meter* half of this is
superseded — see "Meter states the period" above. `TIME_SIGNATURE` remains in `config.py`
as the fallback for a voice whose unit has no valid meter. Both are written by one helper:

```python
TIME_SIGNATURE = (4, 4)
TEMPO_BPM = 120

def append_header(track, name):
    """Name, meter and tempo — written identically at the head of every track."""
    track.append(mido.MetaMessage('track_name', name=name, time=0))
    num, den = TIME_SIGNATURE
    track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(TEMPO_BPM), time=0))
```

All three save functions call it, so no code path can emit a track whose metadata
disagrees with another's. Verified across all 9 tracks in the 6 files: exactly one
distinct time signature `(4, 4)` and one distinct tempo `500000` µs/quarter.

**Why 4/4 and not the old per-voice meters.** 4/4 is the only meter all four voices can
share. A triplet cycle cannot be expressed as any power-of-two meter (see the bug above),
so per-voice meters must differ by definition — uniformity and per-voice meters are
mutually exclusive here.

**What this cost.** A/B/C no longer read as one bar of 40/16, which was genuinely elegant
(40 steps of 120 ticks *is* exactly one bar of that meter). They are now 2.5 bars of 4/4.
Clip lengths did not change — 4800 ticks either way — only the declared meter. If that
one-bar property is ever wanted back it cannot coexist with uniform meter.

**Tempo was previously absent entirely.** The files played at 120 BPM only because that
is MIDI's default with no `set_tempo` event. It is now stated rather than assumed.

**Also retired by this change:** the `STEP_TICKS_TO_DENOMINATOR` table, and the
unreachable `step_ticks == 60` branch that would have declared `20/32` (1200 ticks)
against a true 2400-tick cycle — the same halving bug, now moot. Writing the meter on
every track of the arrangement is non-standard for a type-1 file (conventionally the
conductor track's job) but is now deliberate: it is what makes every track self-describing
and identical.

**Verified:** regenerating after this change moved no notes. A dump of every note in every
file — onset, gate length, pitch, velocity — is identical before and after. Only metadata
differs.

### Superseded: "every output is one LCM span" (2026-08-31, reverted same day)

For part of 2026-08-31 every file was rendered at a single cross-voice LCM (19200 ticks,
10 bars) so all outputs matched in length. A later version kept per-voice files at one
period but still filled the *ensemble* files to the LCM by repeating each voice — same
mistake, smaller scope, and it broke the per-voice-vs-ensemble comparison. **Both were
wrong** and have been reverted. A
cross-voice LCM makes each voice N periods long rather than one, which states a DAW
convenience instead of the sieve's periodicity — see the Governing Principle at the top
of this file. Per-voice files are now one full statement each, at deliberately different
lengths.

The refactor that shipped alongside it was kept, because it was independently good:
`voice_events` / `make_track` / `save_tracks` replaced three near-duplicate writers.

### Important Bug Fixed

MIDI clips were previously ending at the last note-off tick instead of the true cycle boundary. `end_of_track` was being placed at `time=0` after the last note. Fixed by computing `remaining = cycle_ticks - last_note_off` and explicitly appending `end_of_track` with that delta. Without this fix, Ableton reads clips as slightly short and loops drift over time. This fix now lives in `make_track`, which every output goes through.

---

## Key Technical Decisions

### `end_of_track` Padding
Always append `mido.MetaMessage('end_of_track', time=remaining)` explicitly. Never rely on mido's automatic placement (it appends at `time=0` which truncates the clip).

### Absolute OUTPUT_DIR
All `config.py` files use:
```python
import os as _os
OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mid')
```
This ensures scripts run correctly from any working directory.

### TITLE Prefix on Filenames
All generated MIDI files are prefixed with the project TITLE (e.g. `dois_10_A_prime.mid`) so versions can be differentiated when multiple projects are loaded in Ableton simultaneously.

### LCM Arrangement
`main` computes `math.lcm(*cycle_lengths)` once across all voices and every file is written to exactly that length. Handles any combination of step durations. Each track padded to `total_ticks` with an explicit `end_of_track`.

### Voice Derivation Philosophy
Voices are **derived** from a single base sieve, not independently designed. The user explicitly preferred this approach — complement, canon (shift), and intersection relationships produce a coherent ensemble that is mathematically unified. Do not propose independently-designed sieves as separate voices.

---

## Plugin Architecture (PARKED as of 2026-08-31)

> **The user has parked all Max-patch work: "ignore any files created for creating a max
> patch for now."** Do not maintain, regenerate, verify or update `max/sieve.js` or
> anything else in `max/` until the user reopens this. It is not part of the working
> pipeline — nothing in `composition.py` reads it, and no Max device exists to host it.
>
> `max/sieve.js` currently matches the 2026-08-31 render and **will silently go stale**
> the next time the sieves, accents or durations change. That is expected and acceptable
> while parked. When the work resumes, regenerate it from the MIDI files rather than
> editing it, and verify it by *executing* it (see the note at the end of this section).

The plan below is retained for when that happens.

## Plugin Architecture (Future)

### Target: Max for Live MIDI Effect
- Single `.amxd` file, drag onto any Ableton track
- All four voices output on different MIDI pitches → one Drum Rack on the same track
- No cross-track routing needed

### Drum Rack Pitch Mapping

Derived in `config.py` from each voice's position, not written per instrument — see
"Pad assignment is derived" above.

```
Voice A → pitch 36 (C1)   — Drum Rack pad 1
Voice B → pitch 37 (C#1)  — Drum Rack pad 2
Voice C → pitch 38 (D1)   — Drum Rack pad 3
Voice D → pitch 39 (D#1)  — Drum Rack pad 4
```

### Max for Live Patch Structure (planned)
```
[metro 32n @lock 1]     ← fires every 32nd note, transport-locked
        |
[transport]             ← outputs current beat position as float
        |
[js sieve.js]           ← sieve engine (see max/sieve.js)
 |          |
(pitch)  (velocity)
        |
[noteout]               ← sends to Drum Rack
```

`sieve.js` already written at `sifters/dois_series/dois_10/max/sieve.js`. It handles:
- Transport position → step index for A/B/C (120-tick grid) and D (160-tick grid)
- Step crossing detection (fires note only on new step, not every bang)
- Velocity lookup from precomputed arrays
- Outputs pitch on outlet 0, velocity on outlet 1 (velocity must arrive at noteout before pitch)

**`max/sieve.js` is generated from `mid/dois_10_*_prime.mid` — do not hand-edit it.**
*(Parked — see the notice above. The generator that produced it was not committed, so
it will need rewriting when this work resumes. That is deliberate: there was no point
committing a generator for a file nobody is maintaining.)*

It now carries a `VOICES` table instead of loose constants. Each entry holds the voice's
pitch, step size in ticks, and velocity array — and **the array's length is that voice's
period**, so A and C are 120 long while B and D are 40. Step position comes from absolute
transport ticks (`floor(ticks / step) % vel.length`), which keeps every voice phase-locked
to the piece start even though their periods differ.

**Verify it by RUNNING it, not by parsing it.** `node` is not installed on this machine,
but macOS ships JavaScriptCore via `osascript -l JavaScript`, which will execute the file:
stub Max's `outlet()`, sweep `msg_float()` across one ensemble period, and compare the
notes it fires against `mid/dois_10_drumrack.mid`. Verified 2026-08-31 this way — **714
notes, identical in tick, pitch and velocity** (pads 36/37/38/39 = 180/300/180/54).

This matters: an earlier version of the generator emitted a literal `\n` between voice
entries instead of a newline, producing invalid JavaScript. A regex check of the file's
*data* passed anyway, because it never asked whether the file would parse. Only executing
it caught the bug. Do not verify generated code by inspecting it.

**Known gap:** `fireNote` sends note-ons but never note-offs. Fine for one-shot Drum
Rack samples, but it will hang notes on any sustaining device — worth addressing when
the patch is assembled.

### VST Alternative
If broader DAW support is needed beyond Ableton: JUCE framework in C++. Same architecture, rewritten in C++. More work but works in Logic, FL Studio, Reaper, etc.

---

## Version History Summary

| Version | Key feature |
|---|---|
| dois_01 | First working sieve → MIDI pipeline |
| dois_02 | Added shift library (all non-factor shifts of A) |
| dois_03 | **Best-sounding**: A + complement B + canon C + intersection D with triplet grid. Accent voicing. |
| dois_04–six | Explored different instrument configurations |
| dois_07–eight | Ensemble and arrangement experiments |
| dois_09 | Arrangement version of dois_03 — fractal form (5 movements × 8 sections = 40 = sieve period), per-instrument presence thresholds, per-movement MIDI tracks |
| dois_11 | **Current**: same music as dois_10, with measured (not declared) sieve periods, a derived note layer, strict duration lookup, dispatched derivations, and a `verify()` pass that re-reads every rendered file and asserts the invariants |
| dois_10 | duration states periodicity; accent layers span multiple passes of the note layer; accent moduli chosen so all four voices reach the same period; graded overlap velocities; one derived pitch per voice on Drum Rack pads |

---

## Verified Clip Integrity (2026-08-27)

Every file was re-read with mido and walked event-by-event in absolute ticks — checking
the bytes on disk, not the code that wrote them:

- Every track's `end_of_track` lands on its cycle boundary; padding after the last note
  is exactly one step of silence (120 or 160 ticks) or zero because a note genuinely
  reaches the boundary. Never an arbitrary amount.
- Folding each voice onto its own cycle gives **byte-identical repeats** (A/B/C 4x4800,
  D 3x6400) — the repetition is in phase, not drifting.
- No notes past `end_of_track`, no hanging notes, no same-pitch overlaps, no notes
  straddling a loop seam in any file.
- A and B are complements, so their gates tile time continuously within any shared span:
  checked across 19200 ticks at the time, **zero gaps and zero overlaps**, every tick
  covered. (A and B are both 57600 now, but their accent layers differ in phase, so the
  tiling is a property of the 40-step note layer rather than of the whole file.)

Meter and tempo are now uniform — 4/4 at 120 BPM on every track of every file. See
"Uniform meter and tempo" above for the clip lengths that implies.

## Output Consistency (verified 2026-08-28)

Every output now plays the same note for the same voice. Checked by re-reading the
files and comparing note-for-note **including pitch**:

- Each prime clip vs. its pad in the drum rack clip (folding the drum rack's repeats
  back onto one cycle): fully identical — pitch, onset, gate length, velocity.
- Each arrangement track vs. its drum rack pad: fully identical, 60/100/60/18 notes.
- Pitches present per file: A_prime [36], B_prime [37], C_prime [38], D_prime [39],
  arrangement and drum rack [36,37,38,39].
- `max/sieve.js` `PITCH_A`–`PITCH_D` parsed and compared against `config.py`: match.

**The per-voice files exist to check the ensemble files against.** That works because the
ensemble repeats whole periods: *every* cycle inside an ensemble file equals the voice's
own file exactly.

*Historical record — verified 2026-08-31, when the voices had different periods and the
ensemble repeated them (A ×4 of 14400, B ×12 of 4800, C ×4 of 14400, D ×9 of 6400). Every
repetition in both ensemble files was compared against the per-voice file, cycle by cycle
rather than just the first, and all matched.*

**Current state (2026-09-02):** all four voices are in parity at 57600, so each appears ×1
and a per-voice file equals its arrangement track and drum rack pad outright — 180 / 300 /
180 / 54 notes. Re-verified after the parity change.

**The rule this protects:** an ensemble may only ever contain whole repetitions of a
voice's period. Never pad, stretch or truncate a voice to reach a common length — that
would both break this comparison and state a duration that is not the voice's period.

## The accent layer spans the note layer (resolved 2026-08-31)

What was logged as an open issue — the mod-3 accent not fitting the 40-step note layer —
is now the mechanism, at the user's direction: *"it would be interesting to have an accent
layer that spans multiple iterations of the note layer, creating depth and dimensionality."*

**How it works.** The note layer's period is 40 steps (moduli 8, 5). The accent sieves add
modulus 3, and 3 does not divide 40, so the accents land on *different notes* on each pass.
A voice has not stated itself until the two realign:

```
voice_span = LCM(rhythm period, *accent periods) = LCM(40, 5, 8, 3) = 120 steps
```

Three iterations of the same rhythm, re-accented each time. Previously the accents were
evaluated over only 40 steps and restarted at every repeat, which flattened this away.

**The audible result** — voice A, identical note positions on all three passes:

```
step:  0    1    8   10   13   14   16   22   23   25   29   31   33   37   38
it 1: 127  127   63  127  127   63  127  127    1  127   63  127  127  127   63
it 2: 127  127  127  127   63  127  127   63   94  127  127   32  127   63  127
it 3: 127  127  127  127  127  127  127  127   94  127  127  127   63  127  127
```

*(Figures below describe the 2026-08-31 state, when only A and C were accented and their
span was 3 iterations. The mechanism is unchanged; the numbers have moved on — see
"Governing Principle II" and the voice table for current values.)*

**10 of the 15 hits per iteration were re-accented across passes.** Step 23 was the
clearest: a ghost at velocity 1 on the first pass, 94 on the other two. The note layer is
bit-identical across iterations, so every difference is the accent layer.

**The span is derived, not set.** `voice_span(rhythm_period, accent_dict)` takes the LCM of
the rhythm period and every accent modulus, so it follows whatever accents are written.
**This is the lever for depth:** any accent modulus coprime to 40 lengthens the span.

| accents | span | iterations of the note layer |
|---|---|---|
| mod 3 | 120 steps | 3 |
| mod 3 + mod 32 *(current, 16th voices)* | 480 steps | 12 |
| mod 3 + mod 9 *(current, D)* | 360 steps | 9 |
| mod 3 + mod 7 | 840 steps | 21 |

**All four voices now carry accents.** B was flat at velocity 64 until 2026-09-02; it now
uses the same set as A and C.

## What's Next (as of 2026-09-07)

- [x] Update `dois_10` to output all voices on Drum Rack pitches (36/37/38/39) in a single combined clip — the true plugin-ready output format *(done 2026-08-27: `dois_10_drumrack.mid`)*
- [x] Code ready to produce with *(verified 2026-09-07 — see "Ready to produce with")*
- [ ] **Build a track from `dois_12`.** Load `mid/dois_12_drumrack.mid` onto one
      track with a Drum Rack (pads 1-4 = A/B/C/D), or `_arrangement.mid` for four separate
      tracks. Form — repetition, variation, entrances and exits — is being built in the DAW
      for now rather than in the code, by choice.
- [ ] Worth an A/B by ear: `dois_10` (30 bars, four accents, 12 passes) against
      `dois_12` (10 bars, three accents, 4 passes). The shorter version carries no
      repetition beyond what parity requires; the longer one has more accent variety.
- [ ] Only after producing with this: decide whether form belongs in the code (a
      `dois_thirteen` with an arrangement layer, as `dois_09` had) or stays in the DAW.
- [x] Write an explicit `set_tempo` into the generated files *(done 2026-08-30 — 120 BPM on every track)*
- [x] Give every generated track the same time signature *(done 2026-08-30 — 4/4 everywhere)*
- [x] Render each voice at the full 19200-tick LCM *(done 2026-08-31, then **superseded**
      the same day — a cross-voice LCM makes each voice N periods long, which violates the
      governing principle above. Needs reverting to one period per voice.)*
- [x] **Revert per-voice files to one sieve period each** *(done 2026-08-31)*
- [x] **Resolve the accent modulus issue** *(done 2026-08-31 — the accent layer now spans
      3 iterations of the note layer, by design; see the section above)*
- [x] Give D an accent layer *(done 2026-09-02 — it supplied the factor of 3 its meter
      needed, and accents the beat on the triplet grid)*
- [x] Accent layer for B *(done 2026-09-02 — B is no longer flat; all four voices now
      carry accents and share the 57600-tick period)*
- [ ] Decide whether the files should carry a MIDI `key_signature` meta event. There is
      currently **none** in any file. These are Drum Rack parts on pitches 36-39, where a
      key signature is musically inert, but it affects how a notation program renders them.
- [ ] Listen to the 30-bar ensemble and judge whether 3 iterations is the right depth, or
      whether a longer accent span (mod 9, or adding mod 7) serves the piece better
- [ ] Decide on next layer of complexity to add (form/arrangement, parameter variation, sieve formula controls)
- [ ] ~~Assemble the Max for Live patch using `max/sieve.js`~~ — **parked 2026-08-31**
      at the user's request; ignore `max/` entirely until they reopen it

---

## Running the Code

```bash
cd sifters/sifters/dois_series/dois_10
python composition.py
```

Output appears in `mid/`. Requires: `mido`, `music21`, `numpy`.

**Gotcha:** the first run after a reboot can take ~60s before printing anything. That
is macOS code-signing verification of numpy's compiled extensions on first load — not
music21, which imports in well under a second. Subsequent runs are immediate.

---

## How to Continue on Another Machine

1. `git pull` to get latest code and this file
2. Open this file first to re-establish context
3. Read "Current State" and both Governing Principles at the top of this file before
   touching any duration, meter or accent — they are where the reasoning lives, and the
   mistakes they describe were all made once already.
4. The key files to read are:
   - `sifters/dois_series/dois_10/config.py` — voices, accent sieves, meter/tempo constants
   - `sifters/dois_series/dois_10/composition.py` — full pipeline
   - ~~`sifters/dois_series/dois_10/max/sieve.js`~~ — parked and stale; ignore for now
5. Run `python composition.py` and compare its printed periods against "Current State".
   The first run after a reboot takes ~60s in numpy's import; that is normal here.
