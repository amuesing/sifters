# Sifters — Project Context

> This file is the canonical reference for continuing work across machines and sessions.
> **Always update this file at the end of a working session.**
> Last updated: 2026-08-31

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
      dois_ten/           ← CURRENT FOCUS — simplified 40-step beat, plugin-oriented
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
| A | Base sieve | 15/40 (37.5%) | 36 (C1) — pad 1 | 16th (120 ticks) | 40 steps | **120 steps = 14400 ticks** |
| B | Complement of A | 25/40 (62.5%) | 37 (C#1) — pad 2 | 16th (120 ticks) | 40 steps | 40 steps = 4800 ticks |
| C | A shifted +13 steps (canon) | 15/40 (37.5%) | 38 (D1) — pad 3 | 16th (120 ticks) | 40 steps | **120 steps = 14400 ticks** |
| D | Intersection of A and C | 6/40 (15%) | 39 (D#1) — pad 4 | Triplet 8th (160 ticks) | 40 steps | 40 steps = 6400 ticks |

A and C run three times as long because their accent layer spans three iterations of the
note layer — see "The accent layer spans the note layer" below.

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

### Accent Voicing (A and C only)

Three independent accent sieves overlay the main binary. The count of overlapping accents at each active step determines velocity:

| Overlap count | Velocity |
|---|---|
| 0 | 1 (ghost) |
| 1 — low5 (`5@0\|5@1`) | 32 |
| 1 — wide8 (`8@0\|8@1\|8@2\|8@5\|8@6`) | 63 |
| 1 — mod3 (`3@0\|3@1`) | 94 |
| 2+ | 127 |

B uses flat velocity 64. D uses flat velocity 64.

### Velocity Arrays

A and C carry **120-step** velocity arrays, B and D 40-step. They are not transcribed
into this file — they are long, and every past attempt to keep a copy here drifted out
of date. **The authority is `composition.py` and the `mid/` files it writes.** To read
the arrays, run the script and inspect the output.

### Polyrhythm and LCM

D uses triplet eighth notes (160 ticks/step) while A/B/C use sixteenth notes (120 ticks/step). This creates a 4:3 polyrhythm. Full alignment:

```
A full statement: 120 × 120 = 14400 ticks   (accents span 3 note-layer iterations)
B full statement:  40 × 120 =  4800 ticks
C full statement: 120 × 120 = 14400 ticks
D full statement:  40 × 160 =  6400 ticks
Ensemble period (LCM):       57600 ticks = 120 quarter notes = 30 bars at 4/4, 120 BPM
```

A ×4, B ×12, C ×4, D ×9 before every voice has completed a whole number of statements
and they land on beat 1 together. The 4:3 relationship between the 16th and triplet-8th
grids is still what drives the polyrhythm; the accent span is what multiplies it out to
30 bars.

### Generated Files

Each per-voice file is **exactly one full statement** of that voice — which means they
are deliberately different lengths. See the Governing Principle at the top.

- `dois_ten_A_prime.mid` — 14400 ticks (7.5 bars), 120 steps, 45 notes
- `dois_ten_B_prime.mid` —  4800 ticks (2.5 bars),  40 steps, 25 notes
- `dois_ten_C_prime.mid` — 14400 ticks (7.5 bars), 120 steps, 45 notes
- `dois_ten_D_prime.mid` —  6400 ticks (3-1/3 bars), 40 steps, 6 notes
- `dois_ten_arrangement.mid` — 57600 ticks (30 bars), one full ensemble period, four separate tracks
- `dois_ten_drumrack.mid` — 57600 ticks (30 bars), one full ensemble period, all four voices merged onto a **single track** at Drum Rack pitches 36/37/38/39. This is the plugin-ready format: drop it on one Ableton track holding a Drum Rack.

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
still holds and was re-run on 2026-08-31 against the current 57600-tick files.)*

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

### Uniform meter and tempo (2026-08-30)

**Every track of every generated file declares 4/4 at 120 BPM.** Both values live in
`config.py` and are written by one helper in `composition.py`:

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
10 bars) so all outputs matched in length. **This was wrong** and has been reverted. A
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
| dois_ten | **Current**: Stripped to the essentials. 40-step beat, correct clip lengths, LCM arrangement, plugin-oriented architecture |

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
  covered. (A and B now have different periods — 14400 vs 4800 — so the tiling holds
  per 40-step cycle rather than per file.)

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

As of 2026-08-31 a per-voice file holds exactly one full statement of that voice, while
the arrangement and drum rack hold the ensemble period (57600 ticks). So a per-voice file
matches the **first statement** of its arrangement track and drum rack pad note-for-note,
and the ensemble files then continue repeating it. Lengths differ by design.

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

**10 of the 15 hits per iteration are re-accented across passes.** Step 23 is the clearest:
a ghost at velocity 1 on the first pass, 94 on the other two. Verified that the note layer
is bit-identical across the three iterations, so every difference is the accent layer.

**The span is derived, not set.** `voice_span(rhythm_period, accent_dict)` takes the LCM of
the rhythm period and every accent modulus, so it follows whatever accents are written.
**This is the lever for more depth:** any accent modulus coprime to 40 lengthens the span.

| accents | span | iterations | per-voice length |
|---|---|---|---|
| mod 3 (current) | 120 steps | 3 | 14400 ticks (7.5 bars) |
| mod 9 | 360 steps | 9 | 43200 ticks (22.5 bars) |
| mod 3 + mod 7 | 840 steps | 21 | 100800 ticks (52.5 bars) |

**B and D have no accent layer** — both are flat at velocity 64, so both close after 40
steps. Giving them accent sieves would extend their periods too, and because D is on the
triplet grid its accent span would interact with the polyrhythm rather than just the
rhythm. Not done; worth considering.

## What's Next (as of 2026-08-31)

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
- [ ] Consider giving B and D accent layers of their own, with moduli chosen for how their
      spans would interact (D's would cross the triplet grid)
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
3. The key files to read are:
   - `sifters/dois_series/dois_ten/config.py` — voice definitions
   - `sifters/dois_series/dois_ten/composition.py` — full pipeline
   - ~~`sifters/dois_series/dois_ten/max/sieve.js`~~ — parked; ignore for now
