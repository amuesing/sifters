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
- **`SPAN_ACCENT`** — one per basic unit, and in `dois_twelve` **derived** rather than
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

## `dois_twelve` — the production version (2026-09-07)

**Same music as dois_eleven** — all six files identical note-for-note — with the four
things that stood between the code and actually producing with it.

**1. The span accent is fully derived, modulus AND residues.** dois_eleven wrote 32 and 3
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

**2. Rendering no longer empties the output directory.** dois_eleven deleted every `.mid`
in `mid/` on each run, destroying anything saved or edited there. `clear_our_outputs()`
replaces only the six files it is about to write and reports what it left alone. Verified
with a foreign file in the folder: it survives.

**3. Every track carries provenance.** A `text` meta event with title, date, config
fingerprint, parity point, tempo, weather, the sieve, the voice and its accents:

```
dois_twelve 2026-09-07 cfg=52ab7f83 parity=19200 tempo=120 weather=sieve5+sieve8
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

### What is still NOT in the code, deliberately

**There is no form.** The output is one 19200-tick statement — 10 bars, 20 seconds at 120
BPM, 238 notes across four drum pads. It is correct, verified material, not a track.
Arrangement, development and variation across a piece live above this layer and are not
attempted here. `dois_nine` had that layer (5 movements x 8 sections); this lineage
deliberately stripped it out to get the material right first.

**Tempo and meter are largely moot in Ableton**, which uses the project's own and reads a
19200-tick clip as 10 bars of whatever you are in. They matter for notation software and
other hosts.

---

## Current State — read this for the snapshot (2026-09-07)

**Current version: `dois_twelve`.** Verified against the rendered MIDI, not from memory.

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
- `dois_twelve_arrangement.mid` — 4 tracks, 238 notes. `dois_twelve_drumrack.mid` —
  1 track, 238 notes on pads 36-39.
- A per-voice file is **identical note-for-note** to its arrangement track and drum rack
  pad — that is what makes them usable as a reference for checking the ensemble.
- Config fingerprint of this state: **`cfg=52ab7f83`**, stamped in every track.
- `max/sieve.js` (in dois_ten) is **PARKED and stale**. Ignore it.

### Ready to produce with — verified 2026-09-07

Checked as a DAW sees the files, not as the code reports them:

| check | result |
|---|---|
| all six files, valid MIDI type 1 | yes |
| every file exactly 19200 ticks / whole bars | yes |
| pads 36-39 = C1, C#1, D1, D#1, Drum Rack pads 1-4 | yes, 60/100/60/18 notes |
| hanging notes, same-pitch overlaps, zero-length notes | **none in any file** |

**Which file to use.** `dois_twelve_drumrack.mid` on one track with a Drum Rack is the
plugin-ready form. `dois_twelve_arrangement.mid` is the same content split across four
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
      dois_eleven/        ← superseded by dois_twelve
      dois_twelve/        ← CURRENT FOCUS — production version
        config.py
        composition.py
        transformations.py
        mid/              ← generated MIDI files (git-tracked)
        max/
          sieve.js        ← PARKED 2026-08-31 — not part of the pipeline, ignore
```

---

## The `dois_ten` version — superseded, kept for reference

> **This section describes `dois_ten` as it stands, not the current version.** Its figures
> (57600 ticks, 480/360-step spans, four accents, 12 and 9 passes) are correct *for that
> version* and are not the current state — see "Current State" above for `dois_twelve`.
> `dois_ten` remains on disk and is the version whose 30-bar length and four-accent field
> are worth comparing against by ear.

### Current Focus: `dois_ten`

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
`wide8` and had been written `8@0|8@1|8@2|8@5|8@6` since dois_two. On 2026-09-03 it was
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

## What's Next (as of 2026-09-07)

- [x] Update `dois_ten` to output all voices on Drum Rack pitches (36/37/38/39) in a single combined clip — the true plugin-ready output format *(done 2026-08-27: `dois_ten_drumrack.mid`)*
- [x] Code ready to produce with *(verified 2026-09-07 — see "Ready to produce with")*
- [ ] **Build a track from `dois_twelve`.** Load `mid/dois_twelve_drumrack.mid` onto one
      track with a Drum Rack (pads 1-4 = A/B/C/D), or `_arrangement.mid` for four separate
      tracks. Form — repetition, variation, entrances and exits — is being built in the DAW
      for now rather than in the code, by choice.
- [ ] Worth an A/B by ear: `dois_ten` (30 bars, four accents, 12 passes) against
      `dois_twelve` (10 bars, three accents, 4 passes). The shorter version carries no
      repetition beyond what parity requires; the longer one has more accent variety.
- [ ] Only after producing with this: decide whether form belongs in the code (a
      `dois_thirteen` with an arrangement layer, as `dois_nine` had) or stays in the DAW.
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
