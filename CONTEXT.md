# Sifters — Project Context

> This file is the canonical reference for continuing work across machines and sessions.
> **Always update this file at the end of a working session.**
> Last updated: 2026-09-03

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
16th voices  (unit 120): LCM(40, 5, 8, 3, 32) = 480 steps x 120 = 57600
triplet voice (unit 160): LCM(40, 5, 8, 3,  9) = 360 steps x 160 = 57600

480 / 360 = 4/3 = 160 / 120     <- the step counts invert the unit ratio exactly
```

**There is a floor.** A sixteenth voice's minimum period is 40x120 = 4800 and a triplet
voice's is 40x160 = 6400, so any shared duration must be a multiple of
LCM(4800, 6400) = **19200 ticks**. Parity below 4 bars of 40/16 is impossible. 57600 is
the multiple that also lets the sixteenth voices keep their mod-3 accent.

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

## `dois_eleven` — hardened rewrite (2026-09-03)

**`dois_eleven` is `dois_ten` with the same rhythms, an audible ghost floor, and code that
checks itself.** Onsets and pitches are identical to dois_ten in all six files; only
velocities differ, and only because the ghost floor moved from 1 to 24.

What it fixes, each a class of silent wrongness dois_ten was open to:

1. **True periods are measured, not declared.** `true_period()` evaluates a sieve over one
   nominal period and finds the smallest length the binary actually repeats on.
   `music21`'s `Sieve.period()` returns the LCM of the moduli written down, which is an
   upper bound: `32@0|32@1|32@16|32@17` reports 32 and truly repeats every 16. dois_ten
   would have rendered such a voice at 480 steps — the same material twice, still called
   one period. dois_eleven measures 240 and prints a warning naming the expression.
2. **Every voice derives its OWN period**, measured, never declared. dois_ten hardcoded
   `NOTE_LAYER_STEPS = 40`; the first dois_eleven derived it but took the *first* voice's
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
4. **Derivations dispatch to named operations** in `transformations.py`, which dois_ten
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

`dois_ten` is left as it stands. New work should happen in `dois_eleven`.

---

## Current State — read this for the snapshot (2026-09-03)

Verified against the rendered MIDI, not from memory.

| Voice | Pad | Basic unit | Steps | Period | Notes | Accent moduli |
|---|---|---|---|---|---|---|
| A | 36 | 16th (120) | 480 | 57600 | 180 | 5, 8, 3, **32** |
| B | 37 | 16th (120) | 480 | 57600 | 300 | 5, 8, 3, **32** |
| C | 38 | 16th (120) | 480 | 57600 | 180 | 5, 8, 3, **32** |
| D | 39 | triplet 8th (160) | 360 | 57600 | 54 | 5, 8, 3, **9** |

- **Every file is 57600 ticks = 12 bars of 40/16 at 120 BPM.** Every clip ends exactly on a
  bar line; nothing is padded by the host.
- **All four voices are in duration parity**, earned through accent-modulus choice rather
  than imposed. The ensemble therefore contains exactly one statement of each voice.
- `dois_ten_arrangement.mid` — 4 tracks, 714 notes. `dois_ten_drumrack.mid` — 1 track,
  714 notes, pads 36-39.
- A per-voice file is **identical note-for-note** to its arrangement track and its drum
  rack pad. That is the point of the per-voice files: they are the reference for checking
  the ensemble.
- Velocity has 8 graded levels: ghost 1, single accents 19/37/55/73, then 91 / 109 / 127
  for two, three and four accents agreeing.
- `max/sieve.js` is **PARKED and stale** — it describes a much older version. Ignore it.

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

The **psappha sieve** (from Xenakis's percussion piece) is the base formula used throughout:
```
(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))
```
This produces a period of **40 steps** — the foundational unit of the project.

`music21.sieve.Sieve` evaluates these formulas into binary arrays.

---

## Repository Structure

```
sifters/
  sifters/
    dois_series/          ← all dois versions live here
      dois/               ← original (v1)
      dois_two/
      dois_three/         ← best-sounding version; reference for voice design
      dois_four/
      dois_five/
      dois_six/
      dois_seven/
      dois_eight/
      dois_nine/          ← arrangement version of dois_three (5 movements × 8 sections)
      dois_ten/           ← superseded by dois_eleven; kept as it stands
      dois_eleven/        ← CURRENT FOCUS — same music, self-verifying code
        config.py
        composition.py
        transformations.py
        mid/              ← generated MIDI files (git-tracked)
        max/
          sieve.js        ← PARKED 2026-08-31 — not part of the pipeline, ignore
```

---

## Current Focus: `dois_ten`

The active project. A stripped-down, plugin-oriented version that generates a single **40-step rhythmic beat** from the psappha sieve. No arrangement layer, no shift library — just the four core voices at their prime.

### Four Voices

| Voice | Relationship | Density | Pitch / Drum Pad | Step Grid | Note layer | Full statement |
|-------|-------------|---------|-----------|-----------|------|------|
| A | Base sieve | 15/40 (37.5%) | 36 (C1) — pad 1 | 16th (120 ticks) | 40 steps | **480 steps = 57600 ticks** |
| B | Complement of A | 25/40 (62.5%) | 37 (C#1) — pad 2 | 16th (120 ticks) | 40 steps | **480 steps = 57600 ticks** |
| C | A shifted +13 steps (canon) | 15/40 (37.5%) | 38 (D1) — pad 3 | 16th (120 ticks) | 40 steps | **480 steps = 57600 ticks** |
| D | Intersection of A and C | 6/40 (15%) | 39 (D#1) — pad 4 | Triplet 8th (160 ticks) | 40 steps | **360 steps = 57600 ticks** |

All four are in duration parity at 57600 ticks. D reaches it in fewer steps because its
steps are wider — see "Governing Principle II" at the top.

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
`wide8` and had been written `8@0|8@1|8@2|8@5|8@6` since dois_two. On 2026-09-03 it was
thinned to `8@0|8@1|8@5` purely because that measured better, and then dropped entirely.
{0,1,5} matches no clause — the thinning **turned a derived object into a hand-picked
one**, and dropping it removed the sieve's mod-8 self-reference from the accent layer.
The former `low5` (`5@0|5@1`) was equally arbitrary: the two lowest residues, matching no
clause. It is now `sieve5`. Same density, so nothing about the ordering changed — it just
means something now.

**Velocity: rank the states that OCCUR, spaced evenly.**

Ordering is derived — an accent contributes its rarity `(1 - density)`, so a sparse accent
outranks a common one and more accents outrank fewer. Two things are imposed, both for the
reason the ghost floor is imposed: *a distinction the sieve makes must be one you can hear.*

- **Even spacing, not proportional.** Proportional spacing let accents of similar density
  earn near-identical weights, so genuinely different states rendered 1 velocity apart.
- **Only the states that occur.** Four accents give 16 combinations, but 6 never coincide
  with a note in voice A. Spacing all 16 spent a third of the range on states that never
  sound — levels landed 6-7 apart and merging anything under 8 left just 5 of 10 distinct.
  Ranking the 10 that occur spreads them 11-12 apart, every one audible.

The mapping is therefore **per-voice**: the same accent state can render at a different
velocity in different voices, because each reaches a different set of states and each is
given the whole range. The voices are separate drum sounds whose notes never coincide, so
nothing is lost; what is gained is that no voice wastes range on a distinction it never makes.

**Measured — and this version beats every alternative tried:**

| | levels | gaps | entropy | audible after merge | audible entropy |
|---|---|---|---|---|---|
| A | 10 | 11-12 | 3.051 | **10** | **3.051** |
| B | 12 | 9-10 | 3.210 | **12** | **3.210** |
| C | 10 | 11-12 | 3.051 | **10** | **3.051** |
| D | 9 | 12-13 | 2.990 | **9** | **2.990** |
| *dois_ten A* | *16* | *2-17* | *3.596* | *9* | *2.899* |
| *dois_ten D* | *9* | *2-32* | *2.990* | *6* | *2.530* |

Every level is audible in every voice — nothing merges. dois_ten had more raw levels but
fewer that could be told apart, and 10.6% of its notes below audibility. **Rhythm and pitch
remain identical to dois_ten in all six files.**

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

- `dois_ten_A_prime.mid` — 57600 ticks (12 bars), 480 steps, 180 notes
- `dois_ten_B_prime.mid` — 57600 ticks (12 bars), 480 steps, 300 notes
- `dois_ten_C_prime.mid` — 57600 ticks (12 bars), 480 steps, 180 notes
- `dois_ten_D_prime.mid` — 57600 ticks (12 bars), 360 steps,  54 notes
**A per-voice file is one period. The ensemble files repeat those same periods, whole,
until every voice finishes together** — 57600 ticks, the LCM of the voice periods
(A ×4, B ×12, C ×4, D ×9). No voice's internal period is altered to fit; it simply recurs,
so any single cycle inside an ensemble file is identical to that voice's own file.

- `dois_ten_arrangement.mid` — 57600 ticks (30 bars), four tracks, all ending together
- `dois_ten_drumrack.mid` — 57600 ticks (30 bars), all four voices merged onto a **single
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
(a pitched voicing: 36/55/48/60, inherited from dois_three) and `drum_root` (the pad).
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

**Symptom:** `dois_ten_D_prime.mid` declared `40/16`, but that meter describes a
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

**All four voices are now in duration parity at 57600 ticks** — see Governing Principle II
at the top. The ensemble is therefore exactly **one statement of every voice**: each
appears x1, nothing repeats.

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
All generated MIDI files are prefixed with the project TITLE (e.g. `dois_ten_A_prime.mid`) so versions can be differentiated when multiple projects are loaded in Ableton simultaneously.

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

`sieve.js` already written at `sifters/dois_series/dois_ten/max/sieve.js`. It handles:
- Transport position → step index for A/B/C (120-tick grid) and D (160-tick grid)
- Step crossing detection (fires note only on new step, not every bang)
- Velocity lookup from precomputed arrays
- Outputs pitch on outlet 0, velocity on outlet 1 (velocity must arrive at noteout before pitch)

**`max/sieve.js` is generated from `mid/dois_ten_*_prime.mid` — do not hand-edit it.**
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
notes it fires against `mid/dois_ten_drumrack.mid`. Verified 2026-08-31 this way — **714
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
| dois | First working sieve → MIDI pipeline |
| dois_two | Added shift library (all non-factor shifts of A) |
| dois_three | **Best-sounding**: A + complement B + canon C + intersection D with triplet grid. Accent voicing. |
| dois_four–six | Explored different instrument configurations |
| dois_seven–eight | Ensemble and arrangement experiments |
| dois_nine | Arrangement version of dois_three — fractal form (5 movements × 8 sections = 40 = sieve period), per-instrument presence thresholds, per-movement MIDI tracks |
| dois_eleven | **Current**: same music as dois_ten, with measured (not declared) sieve periods, a derived note layer, strict duration lookup, dispatched derivations, and a `verify()` pass that re-reads every rendered file and asserts the invariants |
| dois_ten | duration states periodicity; accent layers span multiple passes of the note layer; accent moduli chosen so all four voices reach the same period; graded overlap velocities; one derived pitch per voice on Drum Rack pads |

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

## What's Next (as of 2026-09-03)

- [x] Update `dois_ten` to output all voices on Drum Rack pitches (36/37/38/39) in a single combined clip — the true plugin-ready output format *(done 2026-08-27: `dois_ten_drumrack.mid`)*
- [ ] Test dois_ten in Ableton with a Drum Rack to validate the musical result — load `mid/dois_ten_drumrack.mid` onto one track with a Drum Rack; pads 1-4 are A/B/C/D
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
cd sifters/sifters/dois_series/dois_ten
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
   - `sifters/dois_series/dois_ten/config.py` — voices, accent sieves, meter/tempo constants
   - `sifters/dois_series/dois_ten/composition.py` — full pipeline
   - ~~`sifters/dois_series/dois_ten/max/sieve.js`~~ — parked and stale; ignore for now
5. Run `python composition.py` and compare its printed periods against "Current State".
   The first run after a reboot takes ~60s in numpy's import; that is normal here.
