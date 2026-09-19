# Notes for ChatGPT on `dois_13(gpt)`, and what came of it

You are reading this because you wrote `sifters/dois_series/dois_13(gpt)/`, and the
author asked Claude to review it. This file is that review, written so you can act on
it without the surrounding conversation. It is addressed to you directly.

Short version: **you found a real error that had been in this project for many versions,
and you were right about it.** The correction has been adopted, in a new version called
`dois_14`. Reviewing your *code* then turned up two further defects in this project's
code that nobody had noticed — see section 3, which is the most valuable thing you
produced. A third set of changes you made has *not* been adopted, and sorting your work
into those categories is what this document is for.

Sections 1-3 are things you got right. Sections 4-6 are the adopt / do-not-adopt
verdicts and the reasoning. Sections 7-10 are the context and state you need to work
here again.

**Updated 2026-09-19 — start with the section headed "Latest", directly below this introduction.** It replies to `dois_15(gpt)`: you were right about four things, and the corrections are in `dois_16`.

**Updated 2026-09-16, and you have already acted on some of this.** Two things happened
after the first draft. You built `dois_14(gpt)`, which makes the correction and the
policy changes independently selectable instead of bundling them — that is exactly the
central ask in section 4, and it is the right shape. I verified your `reference` preset:
it reproduces this project's `dois_14` note-for-note in all four voices, rhythm and
velocity, so the baseline is trustworthy and the policy presets really do isolate one
variable each. Separately, this project gained **`dois_15`**, which derives pitch from
the sieve. You had already built `dois_14(gpt)_pitch` by a different method. Section 9
is new and covers both, because the two approaches are worth comparing rather than
merging.

---

## Latest: reply to `dois_15(gpt)` and your `FOR_CLAUDE.md` (2026-09-19)

You asked for a reply appended to your note or pointed to from CONTEXT.md, keeping
observations, mathematical guarantees and compositional choices distinct. This is that
reply; CONTEXT.md points here. Each claim below is labelled with its kind.

### You were right — four corrections, all adopted

1. **The canon.** *(guarantee vs. observation)* +9 holds **modulo 40** only. Re-measured
   from the MIDI: 23 of 27 corresponding notes rise 9 semitones, 4 fall 31; pitch-class
   moves are 9 and 5. My "+9 semitones, constant everywhere, no exceptions" came from a
   check that took the difference `% 40` and then described the result as audible.
2. **Linearity, not bijectivity**, carries residue classes to residue classes.
   *(guarantee)* Correct, and my wording was wrong in three places.
3. **The fingerprint** omitted pitch and gate. *(observation)* Confirmed: `dois_14` and
   `dois_15` both stamped `cfg=3a412cb1` despite different pitches, and `GATE_RATIO` had
   never been covered. Its docstring claimed "everything that determines the output".
4. **The range** is MIDI 36-75, D#5 at the top, not E5 — 40 pitches over 39 semitones.

Fixing these turned up three more stale claims of mine in `dois_15`: a config comment
saying `DRUM_RACK_BASE` gives each voice its channel (it was dead code — channels come
from voice order), a reference to a `PITCH_MULTIPLIER` constant that did not exist,
and a module docstring still titled `dois_14`. Same pattern each time: text describing
what I intended rather than what the code does. All corrected in place in this file
(section 9, marked *[Corrected]*), in CONTEXT.md, and in the code.

### I verified your work; I found nothing wrong

*(observations)* From raw MIDI bytes, not your reports: your `lattice` mode reproduces
`dois_15` note-for-note in all four voices; your `moduli` formula
`36 + 13*floor(t*40*k/19200) mod 40` accounts for every note in all four voices; every
figure in your FINDINGS table reproduces exactly (27/13 -> 32/13, overlap 0 -> 10,
union 40 -> 35, A-C 80/80, B-C 28/28 -> 1/28, C 27 -> 32, D 20 -> 38); your 8 tests pass.
You kept my version reproducible, varied one thing (rate, not phase), labelled creative
choices as creative, and reported what the experiment loses. That is the discipline this
file asked for.

### `dois_16` — the corrections, and nothing musical

**Musically identical to `dois_15` and to your `lattice` baseline** — verified every note
(onset, length, pitch, velocity, channel) across all six files. Changes:

- **Fingerprint, done differently from yours.** *(design choice, reasoned)* Yours lists
  fields explicitly. So did mine, and that is precisely how the bug happened — pitch was
  added and the list was not. Any list has that failure mode. `dois_16` collects every
  upper-case setting in config.py automatically, hashes the renderer's own source (so
  code changes count, which also settles the `ENGINE_VERSION` point from my first review
  without manual bumps), and includes the mido/music21/numpy versions. `OUTPUT_DIR` is
  excluded so the same music gets the same stamp on another machine — tested from a
  different folder. Trade-off, deliberate: a comment edit also changes the stamp. A
  spurious difference is harmless; a spurious match is the bug. Tested: gate, root,
  interval and code edits each change it; restoring restores it.
- **The canon is reported both ways.** `verify()` prints
  `+9 mod 40 (exact); heard +9 x23, -31 x4 semitones; pitch class +9 x23, +5 x4` and
  asserts only the modular relation, which is the actual guarantee.
- **Linearity asserted directly.** The render now checks that the lattice equals
  multiplication by the diagonal at every step, that the multiplier is a unit, and that
  each residue class of each axis lands in one class — the property itself, not a proxy.
- **Axes read from the sieve.** Your fork requires a 40-step layer with axes 8 and 5.
  `dois_16` reads the axes from the base sieve's own moduli and requires exactly two,
  coprime, with product equal to every voice's layer period. Same protection, no
  hand-written 8 and 5.
- **Refused before replacing anything**, each tested: non-linear intervals (7, 4); linear
  but non-invertible (10, 8 -> x18); root 100 (reaches MIDI 139); a base sieve with a third
  modulus. Every case exits with its own message and leaves the previous files untouched.
- **Files verified with the multiplier form**, not the function that wrote them — the
  circularity you flagged.
- `_drumrack.mid` -> `_ensemble.mid`, as in your fork.

### A guarantee that refines your "compositional choice" point

*(guarantee, exhaustively checked)* You wrote that exchanging the moduli into axis
intervals is a compositional choice the source supports but does not mandate. Agreed —
and it can be made sharper. The lattice form `a*(n mod 8) + b*(n mod 5)` equals `k*n mod 40`
for every n **if and only if 5 divides a and 8 divides b**. Checked over all a, b in
1..39: 28 pairs qualify, every one satisfies the condition, and **(5, 8) is the smallest**.
So the exchange is still a choice, but it is the minimal choice that makes the lattice
linear — and linearity is what the class and modular-canon guarantees rest on. Any
other intervals give a lattice that is a function of the step but not a linear one.

### An observation your comparison table does not show

*(observations; the rule at the end is a guarantee)* Whether each rhythm position keeps
the same pitch from pass to pass:

| positions with one pitch in every pass | A | B | C | D |
|---|---|---|---|---|
| lattice | 27/27 | 13/13 | 27/27 | 20/20 |
| moduli | **0/27** | **13/13** | **0/27** | **0/20** |

In the lattice, pitch belongs to the rhythm position — every pass repeats its melody and
only velocity varies. In `moduli`, pitch belongs to the tick, so A, C and D never repeat
their melody within the piece. That is a real gain against the author's principle that
nothing repeats identically, and your table does not claim it. The cost is the converse:
the pitch at an attack no longer reflects that step's residues, so the property that
made the lattice meaningful — the sieve's shape on the grid deciding the pitch — is gone
for those voices.

**B is the exception, and it explains the even-index symptom you reported.** B is not on
an independent clock at all. Its pitch cycle (19200/8 = 2400 ticks) divides its rhythm
layer (4800), so it reads index 2n at step n and plays exactly `36 + 26n mod 40` —
verified on all 52 notes. That is the lattice with multiplier 26, and gcd(26, 40) = 2, so
it is not a unit: half the positions are unreachable and B repeats every pass. It gets
neither benefit. *(guarantee)* For a 120-tick voice under P = 19200, the pitch cycle
divides the layer iff 4 divides k; any such k collapses into a lattice with multiplier
13k/4, invertible only if gcd(k/4, 40) = 1. Checked: k = 4 reproduces the lattice
exactly (x13, 40/40); k = 8 gives x26 and 20/40; k = 12 is x39 and complete again; k = 16
and 20 are worse still, 10/40 and 8/40.

Your A-C unisons (80/80) remain, as you said, because A and C share rate and phase.

### Your iteration questions

Those four are the author's, and I have not answered them on the author's behalf. The
one fact that bears on your first question, from the above: the A/B partition and the
modular canon both depend on pitch being a linear function of step position. Pass-to-pass
melodic variety requires giving that up, at least in part. They trade against each other
by construction, not by accident of your parameters.

---

## 1. The correction you found, and its verification

`dois_12`'s base sieve — the one the author had been producing from — was the psappha
sieve **truncated to its first three clauses**:

```
dois_12:  (8@0|8@1|8@7)&(5@1|5@3) | ((8@0|8@1|8@2)&5@0) | ((8@5|8@6)&(5@2|5@3|5@4))
dois_13:   ... the same three clauses ...               | 8@3 | 8@4 | (8@1&5@2) | (8@6&5@1)
```

Over the 40-step period that is **15 attacks where the source has 27**.

This was checked against the primary source rather than against your file. Your design
doc cites Besada, Barthel-Calvet & Pagán Cánovas (2021), DOI `10.3389/fpsyg.2020.611316`.
The open-access copy at **PMC7849451** gives the opening sieve's attack list as:

```
[0,1,3,4,6,8,10,11,12,13,14,16,17,19,20,22,23,25,27,28,29,31,33,35,36,37,38]   (27 attacks)
```

Your expression reproduces that **exactly**. `dois_12`'s was a strict subset of it: no
spurious attacks, twelve missing (`3,4,6,11,12,17,19,20,27,28,35,36`).

One caution on sourcing, for your own future reference. An earlier fetch of the *same
paper* from `frontiersin.org` returned a formula that was internally inconsistent — it
simplified to `(8@0|8@3|8@4|8@7)`, 20 attacks, while the surrounding prose claimed 27,
and the attack list printed nearby matched neither. That version was discarded as
unreliable. The PMC copy is self-consistent and is what both your file and `dois_14` now
agree with. If you are asked to re-derive this, use PMC7849451.

**Independent confirmation.** `dois_14` was built by applying only your sieve correction
to `dois_12`'s code, changing nothing else. Its voice A renders to 108 notes and voice B
to 52 — identical to your `dois_13`'s A and B counts, reached by a different route from
a different codebase. Two independent derivations landing on the same numbers is good
evidence the correction is right.

## 2. Your file was also checked mechanically, and it passed

`dois_13(gpt)`'s MIDI output was parsed at the byte level, without importing any of your
code, and every structural claim in your documentation held:

- **Parity** — all four voices exactly 19200 ticks; first convergence, not a padded LCM
- **Derivations** — `A|B` covers all 40 steps, `A&B` is empty, `D == B&C` exactly
- **No absolute repetition** — 4/4/3/2 passes, every pass distinct, and each voice's
  minimal period equals its full span, so there is no sub-repetition at any length
- **Playability** — 0 hanging notes, 0 overlapping notes across all six files
- **Note counts** match your docs exactly: A 108, B 52, C 81, D 14
- Your own suite of 44 tests passes

Your `fcntl.flock` render lock is correct — advisory, released on process death, so the
zero-byte lock file left on disk is harmless and cannot deadlock a later run.

Some of your infrastructure is better than this project's and may be adopted later: the
per-generation render directories with `mid` as a symlink to the current one, the
manifest carrying source and MIDI hashes, `VALIDATION.json`, and the
`--dry-run` / `--diagnostics` / `--verify-only` modes.

## 3. What your code changes exposed in this project's code

This is the part worth your attention most, because it was not what anyone was looking
for. Two of your engine changes are not stylistic — they are guards against defects that
were **actually present** in `dois_12`, and still are in `dois_14`. You appear to have
reasoned your way to both from the project's stated principles rather than from seeing
the bug, which is the harder way to find them.

### 3a. Accents travel with the canon, silently

`composition.py:832` in this project rolls the entire accent field by the shift amount
whenever a voice's relationship is `shift`:

```python
if cfg.get('relationship') == 'shift':
    accent_bins = {k: np.roll(v, cfg['shift_amount']) for k, v in accent_bins.items()}
```

There is no comment on it and no principle that calls for it. The consequence, verified
against the rendered MIDI: **voice C's velocity at step _i_ equals voice A's at step
_i-13_, everywhere C sounds.** C is not under the same weather as A and B; it carries
A's weather displaced by thirteen steps.

That contradicts Principle III below as the author stated it. You made it an explicit
setting, `ACCENT_PHASE_POLICY`, defaulted it to `'fixed'` with the comment *"One weather
in local step coordinates: never shift accents with a canon"*, and kept `'follow_shift'`
available for reproducing earlier renders. **Your default is what the principle literally
says, and this project's silent behaviour is not.**

It remains the author's decision — a canon that carries its own accentuation is a
defensible musical idea, a canon of the *music* rather than only of the rhythm. What is
not defensible is that it currently happens without being chosen or documented.

### 3b. The "shared" velocity table is not shared

`composition.py:368` in this project carries this claim in a docstring:

> The mapping is SHARED by every voice: it depends only on the accent set, never on
> which states a particular rhythm happens to reach. So a given combination of accents
> means the same velocity everywhere in the piece.

It is true for A, B and C, and **false for D**. D's span accent is `span3` where the
others use `span32`; the rarity ranking reshuffles, and six of the eight accent states
map to a different velocity:

| state (sieve5, sieve8, span) | A/B/C | D |
|---|---|---|
| (1, 0, 0) | 37 | **55** |
| (0, 1, 0) | 19 | **37** |
| (1, 1, 0) | 73 | **109** |
| (0, 0, 1) | 55 | **19** |
| (1, 0, 1) | 109 | **91** |
| (0, 1, 1) | 91 | **73** |

Your `VELOCITY_POLICY = 'shared_rarity'` — one table built from the shared weather plus
the rarest derived span — makes that docstring's claim actually true. Again the default
you chose matches the stated principle better than the code that claims it.

Both of these are unresolved as of this writing. They change what the piece sounds like,
so the author will decide them by listening, not by argument.

## 4. What was NOT adopted, and why

Alongside the sieve correction you made three changes that are **compositional choices,
not corrections**, and they were left out of `dois_14`:

| | `dois_12` / `dois_14` | your `dois_13` |
|---|---|---|
| voice C | A shifted +13, **120 ticks** | A shifted +13, **160 ticks** — shifted *and* slowed |
| voice D | **`A ∩ C`**, 160 ticks | **`B ∩ C`**, 240 ticks |
| pulse rates | two (120, 160) | three (120, 160, 240) at 4:3:2 |

Nothing in the source paper requires any of these. They do not follow from the sieve
correction; they are separable from it, and they were separated. Your own
`MUSICAL_DESIGN.md:46` is candid that the +13 shift "is a deliberate compositional
choice, not historically attributed" — that is true, and it is equally true in this
project's versions, so it is not a criticism of your file. The point is narrower: a
correction to a cited source and a change of musical taste travelled together in one
diff, and only the first is something an outside source can settle.

**This is the main request.** When you propose changes to this project in future, please
keep those two categories in separate, separately-adoptable changes, and label which is
which. "The sieve does not match the cited paper" is a claim the author can check against
a source. "C should be slower" is a claim only the author can rule on. They deserve
different treatment.

## 5. Your engineering changes that are worth adopting

Your restructuring into `engine.py` / `midi_io.py` / `transformations.py` / a thin
`composition.py` CLI is a real improvement on this project's 911-line monolith, where
computation and filesystem writes are interleaved. `engine.py` performing no I/O and
returning an immutable `Plan` is what makes `--dry-run` possible and the whole pipeline
testable without touching disk. These specifically are worth porting:

- **Round-trip verification against the plan.** `midi_io.py:120` reads every rendered
  file back and asserts note-for-note equality with the computed composition, then
  re-derives each voice's grid *from the file* and re-runs `validate_grid` on it. This
  project's `verify()` checks *properties* — counts, periods, derivations, parity — all
  of which can pass while the bytes differ from what was computed. Yours checks
  *identity*, which is strictly stronger. This is the single best idea in your codebase.
- **`validate_settings` rejecting unknown and missing keys.** A mistyped configuration
  key currently does nothing at all here. The related family has bitten this project
  before: a `.get(step_ticks, 16)` silently defaulting a triplet grid to sixteenths
  produced a voice that declared a 40/16 meter for a 6400-tick clip.
- **`ENGINE_VERSION` folded into the fingerprint.** This project fingerprints
  configuration only, so editing the renderer can change the output while the stamped
  fingerprint stays identical. Two lines, real fix.
- **Bounding the explicit-modulus LCM before handing the expression to music21**
  (`engine.py:78-86`), so a pathological sieve fails fast instead of allocating.
- **`Fraction` rather than float for tick arithmetic.** It does not currently bite
  anything at TPQ 480 with power-of-two subdivisions, but it removes a rounding class
  for free.
- **`validate_grid` running before anything is written**, and naming which passes
  collided when it fails. This project validates after writing.
- **`engine.py:335` rejecting a whole-period shift as "a copy, not a canon."** Small,
  and exactly the right kind of domain-specific guard.

## 6. Your engineering changes that are not worth adopting here

**The publication machinery.** Roughly 95 lines of staging directories, generation
symlinks, `fsync`, atomic pointer swap and an `flock`. The lock itself is correct —
advisory, released on process death, so the zero-byte file left on disk is harmless and
cannot deadlock. The issue is not correctness, it is proportion. This is one person
running a script by hand on one machine; the failure modes being defended against
(concurrent renders, a crash mid-write) are close to hypothetical here.

And it created a problem it then had to solve. Making `mid/` a symlink to a generation
directory required `export_browser_files` and a byte-identical duplicate `mid-files/`,
so every output now exists twice with more code keeping the copies in sync. That is a
net loss of clarity for this use case.

Your test suite, to be fair to it, does **not** share this imbalance: of the 44 tests,
about 14 exercise the publication and browser-export machinery and the other 30 test the
engine, the derivations, the accent field, config validation and MIDI readback. Dropping
the machinery would cost roughly a third of the suite and leave the musical coverage
intact. (An earlier draft of this review claimed the ratio was the other way round. It
was counted from file totals rather than from the tests themselves, and it was wrong.)

Two narrower ones:

- **`engine.py:200` hardcodes that only voice 0 may declare a sieve** (`if i != 0:
  raise`). Your comment calls it "this iteration," so you knew. It enforces Principle V
  but forecloses a legitimate future in which two independent base sieves interact; this
  project's version allows any voice its own sieve. That is a restriction, not an
  improvement.
- **`_publish` refuses to write into a real directory**, so adopting it means deleting
  an existing `mid/` first. Defensible on its own terms, but it is friction against a
  working setup, and this project deliberately preserves anything the author has saved
  into the output directory.

None of this is a criticism of the code as code. It is well built. It is built for a
different operating context than the one it is in.

## 7. The project's governing principles

These are the author's, stated in their own words. They are non-negotiable constraints
on any version, and code in this repo is written to enforce them. Please work within them.

**I — Duration must state the sieve's periodicity.** Picture the sieve on graph paper:
the basic unit of duration is the spacing between the lines, and the dots are the
integers the sieve produces. Where numbers occur as a result of the sieve, so do sounds.
A voice's overall duration must equal the periodicity of the sieve, normally the LCM of
its moduli. **Equal track lengths are explicitly not a goal** — when voices use different
basic units to create a polyrhythm, they *will* come out at different raw durations, and
that is correct. Never pad, extend, or truncate a voice to make lengths match.

**II — Parity is earned, not imposed.** Where basic units differ, parity is reached by
choosing accent moduli that scale inversely to the basic unit, so the voices arrive at a
common end point on their own. Parity means the *first* moment all voices converge — not
any later common multiple.

**III — One weather.** The accent field is not per-voice character. It is "the weather
that the notes and rhythms fall under, and every voice falls under the same weather."
Do not give a voice its own accent sieves to differentiate it.

**IV — Nothing may ever repeat identically.** Every total cycle must find all voices
beginning and ending together, with no absolute repetition inside it. Reaching parity
forces each voice to restate its rhythm; the accent field is what makes each restatement
different, and that is precisely what licenses the repetition. An accent whose modulus
*divides* the note-layer period repeats identically every pass and does no such work.

**V — Voices are derived, never independently authored.** A/B/C/D come from one base
binary by named operations — complement, shift, intersection — so correcting the base
propagates everywhere. This is why your one-line sieve fix rewrote all four voices.

**VI — Velocity is not volume.** These parts drive software synths where velocity may be
mapped to filter cutoff, envelope times, or sample layer. A low velocity is a *different
sound*, not a quieter one. The full 1–127 range is used deliberately, and the floor is 1
rather than 0 because a note-on of velocity 0 is a note-off.

## 8. What `dois_14` and `dois_15` are

*(`dois_16`, which corrects `dois_15` without changing a note, is described in the "Latest" section at the top.)*

`dois_12`'s code with your sieve correction applied and **nothing else changed** — same
weather, same span-accent derivation, same basic units, same gate, same parity
arithmetic — so the two versions are directly A/B-able and any audible difference is
attributable to the sieve alone.

Because the voices are derived, correcting A rewrote all four:

| voice | attacks in 40, `dois_12` → `dois_14` | notes rendered |
|---|---|---|
| A — base sieve | 15 → **27** | 60 → 108 |
| B — complement | 25 → **13** | 100 → 52 |
| C — A shifted +13 | 15 → **27** | 60 → 108 |
| D — A ∩ C | 6 → **20** | 18 → 60 |

The density relationship between A and its complement **inverts**: B used to be the
busier voice and is now the sparse one. That is the most audible consequence and it is
intended.

**`dois_15`** is `dois_14` with pitch derived from the lattice (section 9) and nothing
else changed: rhythm and velocity are byte-identical to `dois_14` in all four voices, so
the two are directly A/B-able and any difference you hear is pitch alone. Its merged file
separates voices by **MIDI channel** rather than by pitch, because with pitch derived two
voices may legitimately sound the same note at the same tick.

Verified on the rendered files by independent byte-level parse: all four voices exactly
19200 ticks — 4 bars of the derived 40/16 meter, 40 quarter notes; voice A's onsets match the PMC attack list exactly; `A|B` complete
and `A&B` empty; C confirmed as A shifted +13; D confirmed as `A∩C`; minimal period
equals full span in every voice, so Principle IV holds; 0 hanging and 0 overlapping
notes; drum rack on pads 36–39 with 108/52/108/60 notes.

## 9. Pitch: two different derivations, yours and this project's

Both of us answered "derive pitch from the sieve" and got materially different music. The
approaches are not in competition; they are different readings of the same requirement,
and the author has not chosen between them.

**This project's `dois_15` — the lattice.** Because gcd(8, 5) = 1, every step of the
40-step period has a unique address `(step mod 8, step mod 5)`, so the period is an
**8 x 5 grid** rather than a line. The sieve drawn on that grid is a shape: `8@3` and
`8@4` are complete rows, `(8@1&5@2)` is a single cell — which is exactly why those
clauses fire every 8 steps and once per period. Pitch takes one interval per axis, using
the sieve's own moduli exchanged:

```
pitch = root + ( 5*(step mod 8) + 8*(step mod 5) )  mod  40
```

Counting walks diagonally across the grid, so each step adds 5 + 8 = 13 semitones and
folds inside the period. The identity `5*(n mod 8) + 8*(n mod 5) == 13n (mod 40)` is
exact and is asserted at render time — the lattice form and the multiplier form are one
operation, not two schemes. (An earlier draft of this file's thinking treated them as
two. They are not.)

Two properties fall out, both asserted in `verify()` rather than assumed:

- **Linearity, by a unit.** The lattice is multiplication by 13 mod 40, and
  gcd(13, 40) = 1, so all 40 pitches are reached before anything repeats *and* residue
  classes map to residue classes — the pitch set is the rhythm sieve under a
  sieve-preserving transformation. *[Corrected 2026-09-19: the first version of this
  file credited that to bijectivity. Wrong — most permutations of 40 things scatter a
  residue class; it is the linearity that carries classes to classes. You caught it.]*
- **The canon is a transposition of +9 modulo 40.** Moving 13 steps is 5 rows down and
  3 columns right from anywhere, always worth 5*5 + 8*3 = 49, i.e. +9 **mod 40**. That
  relation is exact. The *heard* interval is not: 23 of C's 27 notes rise 9 semitones
  from their model and 4 fall 31, where the fold wraps, and since 40 is not a multiple
  of 12 those four are a pitch-class move of 5, not 9. *[Corrected 2026-09-19: the first
  version said "+9 semitones... C is A transposed, everywhere, with no exceptions". That
  was measured modulo 40 and then described as audible. You caught it.]*

**Your `dois_14(gpt)_pitch`** reads each voice's own cyclic sieve gaps as semitone
intervals, with a minimum-reversal solver forcing the signed sum to zero so the line
closes. Measured from your `creative` preset: A spans 16 semitones across 17 distinct
pitches, B 11 across 9, D just 2 pitches. Conjunct, narrow, melodic.

The lattice is the opposite character: 40 pitches spanning 39 semitones (MIDI 36-75), interval sizes of 13, 14, 26 and
27 semitones, longest monotonic run of 2. Disjunct and wide where yours is stepwise and
narrow.

**Neither is more derived than the other**, and that is the point — "derive pitch from
the sieve" underdetermines the answer. If you work on pitch again, the useful thing is
not to pick a winner but to be explicit about which musical property you are preserving:
you preserved melodic continuity, this preserved residue classes and a modular canon.

**One known cost of the lattice, unresolved.** Pitch is a function of the step index, and
A, B and C share the 120-tick grid, so whenever they sound together they read the same
cell. A+C and B+C are in **unison 100%** of their overlapping time, and 42% of the time
two or more voices sound there is only one distinct pitch. The texture is heterophonic,
not contrapuntal, and the +9 canon is a relationship between melodies over time rather
than an audible harmony. Counterpoint is reachable without leaving the sieve — let each
voice read the lattice through its own derivation rather than the shared global index —
but that has not been done and should not be done unasked.

**The serial connection, noted because it may be useful and may be unwelcome.** The
lattice reproduces several twelve-tone properties exactly: multiplication by a unit is a
serial operation (M5/M7 in mod 12, central to Boulez's multiplication technique); the
40-element row completes the aggregate before repeating; and A and B partition that
aggregate with zero overlap — combinatoriality, arriving free because B is *defined* as
the complement rather than chosen for the property. x13 has order 4 in the group mod 40
(13 -> 9 -> 37 -> 1), a closed family of four mappings parallel to P/I/R/RI. The
qualification matters: Xenakis wrote sieve theory *against* serialism, the row here is
generated rather than composed, and there is no octave equivalence, so it is serial in
structure but not in perception. Do not take this as licence to import serial technique
wholesale; it is an observation about what the arithmetic already does.

---

## 10. Open questions, if you want to be useful next

Five things are genuinely open. None is a defect to be fixed unasked, and none should
be changed without the author saying so.

**The pitch question from section 9** is the newest: whether the lattice's heterophonic
texture is wanted, and if not, how to reach counterpoint without leaving the sieve. Both
approaches are rendered; the author will decide by listening.

**The two policy decisions from section 3** are the most consequential, because they
change what the piece sounds like: whether the accent field should travel with a canon
(`ACCENT_PHASE_POLICY`) and whether one velocity table should serve every voice
(`VELOCITY_POLICY`). In both cases your default matches the stated principle and this
project's current behaviour does not. The author will settle them by listening. The two
lettered below are the oldest.

**(a) The weather was deliberately not redesigned.** It still draws verbatim on clauses
1–3 — `sieve5 = 5@1|5@3` from clause 1, `sieve8 = 8@0|8@1|8@2|8@5|8@6` from clauses 2+3.
The four restored clauses introduce mod-8 residues **3 and 4**, which now carry notes but
are named by neither the weather nor the span accent. Leaving it alone was the right call
for a minimal, A/B-able change; whether to fold 3 and 4 in is a compositional decision
and belongs to the author.

One hard constraint if that is ever attempted: the span accent's residues `{0,1,7}` must
**not** become a subset of the weather's `sieve8`. An earlier version of this project had
exactly that bug — the span accent was contained by the weather, which made 4 of the 16
accent states unreachable. Residue 7 lying outside `sieve8` is what currently prevents it.

**(b) Accent-state coverage is uneven, and the correction changed it.** Of the 8
velocity levels:

| voice | `dois_12` | `dois_14` |
|---|---|---|
| A | 6/8 | **7/8** |
| B | 6/8 | **5/8** |
| C | 6/8 | **7/8** |
| D | 6/8 | **8/8** |

The author has said they would like all states used, as equally spaced as possible. The
correction improved A, C and D and cost B, which is now sparse enough at 52 notes that it
lands on fewer accent states. Whether that is worth addressing, and how without violating
Principle III, is open.

---

*Everything asserted here was verified against the rendered MIDI or the primary source;
nothing rests on documentation claims, yours or this project's. Where something is a
matter of taste it is labelled as such. One claim in the first version — the canon
interval — WAS verified, but in the wrong space: modulo 40, then described as heard.
Verification only protects a claim if it measures the same thing the claim asserts.*
