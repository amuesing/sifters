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
          sieve.js        ← JavaScript port of sieve engine for Max for Live
```

---

## Current Focus: `dois_ten`

The active project. A stripped-down, plugin-oriented version that generates a single **40-step rhythmic beat** from the psappha sieve. No arrangement layer, no shift library — just the four core voices at their prime.

### Four Voices

| Voice | Relationship | Density | Pitch / Drum Pad | Step Grid | Cycle |
|-------|-------------|---------|-----------|-----------|-------|
| A | Base sieve | 15/40 (37.5%) | 36 (C1) — pad 1 | 16th note (120 ticks) | 4800 ticks |
| B | Complement of A | 25/40 (62.5%) | 37 (C#1) — pad 2 | 16th note (120 ticks) | 4800 ticks |
| C | A shifted +13 steps (canon) | 15/40 (37.5%) | 38 (D1) — pad 3 | 16th note (120 ticks) | 4800 ticks |
| D | Intersection of A and C | 6/40 (15%) | 39 (D#1) — pad 4 | Triplet 8th (160 ticks) | 6400 ticks |

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

### Precomputed Velocity Arrays (exact, from Python)

```javascript
vel_A = [127,127,0,0,0,0,0,0,63,0,127,0,0,127,63,0,127,0,0,0,0,0,127,1,0,127,0,0,0,63,0,127,0,127,0,0,0,127,63,0]
vel_B = [0,0,64,64,64,64,64,64,0,64,0,64,64,0,0,64,0,64,64,64,64,64,0,0,64,0,64,64,64,0,64,0,64,0,64,64,64,0,0,64]
vel_C = [0,0,63,0,127,0,127,0,0,0,127,63,0,127,127,0,0,0,0,0,0,63,0,127,0,0,127,63,0,127,0,0,0,0,0,127,1,0,127,0]
vel_D = [0,0,0,0,0,0,0,0,0,0,64,0,0,64,64,0,0,0,0,0,0,0,0,64,0,0,0,0,0,64,0,0,0,0,0,0,0,0,64,0]
```

### Polyrhythm and LCM

D uses triplet eighth notes (160 ticks/step) while A/B/C use sixteenth notes (120 ticks/step). This creates a 4:3 polyrhythm. Full alignment:

```
A/B/C cycle: 40 × 120 = 4800 ticks
D cycle:     40 × 160 = 6400 ticks
LCM:         19200 ticks = 40 quarter notes = 10 bars at 4/4, 120 BPM
```

A/B/C repeat **4 times**, D repeats **3 times** before all voices land on beat 1 together. This is not coincidental — 40 quarter notes mirrors the 40-step sieve period.

### Generated Files

**Every file is 19200 ticks — 10 bars of 4/4 at 120 BPM.** See "Every output is one
LCM span" below.

- `dois_ten_A_prime.mid` — voice A alone, its 4800-tick cycle repeated 4x
- `dois_ten_B_prime.mid` — voice B alone, 4x
- `dois_ten_C_prime.mid` — voice C alone, 4x
- `dois_ten_D_prime.mid` — voice D alone, its 6400-tick cycle repeated 3x
- `dois_ten_arrangement.mid` — 19200 ticks, one full LCM cycle, all four voices on separate tracks
- `dois_ten_drumrack.mid` — 19200 ticks (10 bars of 4/4), one full LCM cycle, all four voices merged onto a **single track** at Drum Rack pitches 36/37/38/39. This is the plugin-ready format: drop it on one Ableton track holding a Drum Rack.

### Drum Rack Output (added 2026-08-27)

The drum rack clip holds the same material as the arrangement, merged onto one MIDI
track. Same notes, same pitches, one track instead of four:

- **One track, not four.** All voices become a single absolute-time event stream.
- **Meter and tempo come from the shared header**, same as every other track — see
  "Uniform meter and tempo" below. The LCM cycle is exactly 10 bars of 4/4.
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

Verified on 2026-08-27 by reading the file back with mido: 1 track, 19200 ticks,
4/4, no hanging notes, no same-pitch overlaps, hits per pad 60/100/60/18 (= 4×15,
4×25, 4×15, 3×6), onset positions equal to the documented sieve steps on each voice's
own grid, and per-pad velocities identical to the `vel_A`–`vel_D` arrays hardcoded in
`max/sieve.js`. The Python output and the Max engine are therefore in sync.

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
relationship that produces the 19200-tick LCM.

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

### Every output is one LCM span (2026-08-31)

**Every generated file is 19200 ticks — 10 bars of 4/4 at 120 BPM.** No exceptions:
the four per-voice files, the 4-track arrangement and the merged drum rack clip are all
the same length, meter and tempo, so any combination of them can be dropped onto tracks
and looped side by side forever without drifting.

Each voice fills that span by repeating its own cycle a whole number of times:

| Voice | Cycle | Reps | Total | Notes |
|---|---|---|---|---|
| A | 4800 | 4x | 19200 | 60 |
| B | 4800 | 4x | 19200 | 100 |
| C | 4800 | 4x | 19200 | 60 |
| D | 6400 | **3x** | 19200 | 18 |

**Why the LCM and not something shorter.** A voice's cycle is 40 steps of its own grid:
4800 ticks at a 16th (120) and 6400 at a triplet 8th (160). A shared length must be a
common multiple of both or it cuts someone mid-cycle — at 4800, D is cut 75% through its
first pass; at 6400, A/B/C are cut a third into their second. 19200 is the smallest
length that holds whole cycles of all four, and it is exactly 10 bars.

**"Prime" now means un-shifted, not one cycle.** Previously each `_prime` file was a
single cycle (hence 4800/4800/4800/6400, which are 2.5, 2.5, 2.5 and 3-1/3 bars — none a
whole number of bars, and none can be). They are now the full span. The name still
distinguishes the prime form from the shifted variants used in earlier dois versions.

**One code path builds all of it.** `voice_events` produces a voice's absolute-time
events repeated to fill the span; `make_track` turns any event list into a track with
the shared header and `end_of_track` on the boundary; `save_tracks` writes a file. A
per-voice file is one track from one voice, the arrangement is four tracks, the drum
rack is one track from all four voices' events merged. This replaced `save_midi`,
`save_ensemble_loop` and `save_drum_rack_loop`, which duplicated the same event-building
and delta-time logic three times over — composition.py went from 340 to 239 lines.

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

Its `PITCH_A`–`PITCH_D` constants (36/37/38/39) match the derived `root` values in
`config.py`, and its velocity arrays were verified equal to the Python output.
Re-verified 2026-08-28 by parsing the constants straight out of `sieve.js`.

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
- A and B are complements, so their gates should tile time continuously: across the full
  19200 ticks there are **zero gaps and zero overlaps**, 160 notes covering every tick.

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

As of 2026-08-31 there is no remaining difference: every file is the same 19200-tick
span, so a per-voice file, its arrangement track and its drum rack pad are now identical
note-for-note. Verified again after that change — all three match for all four voices.

## What's Next (as of 2026-08-31)

- [x] Update `dois_ten` to output all voices on Drum Rack pitches (36/37/38/39) in a single combined clip — the true plugin-ready output format *(done 2026-08-27: `dois_ten_drumrack.mid`)*
- [ ] Test dois_ten in Ableton with a Drum Rack to validate the musical result — load `mid/dois_ten_drumrack.mid` onto one track with a Drum Rack; pads 1-4 are A/B/C/D
- [x] Write an explicit `set_tempo` into the generated files *(done 2026-08-30 — 120 BPM on every track)*
- [x] Give every generated track the same time signature *(done 2026-08-30 — 4/4 everywhere)*
- [x] Render each voice at the full 19200-tick LCM *(done 2026-08-31 — every file is now
      10 bars of 4/4; the one-cycle prime clips are gone)*
- [ ] Decide on next layer of complexity to add (form/arrangement, parameter variation, sieve formula controls)
- [ ] Eventually: assemble the Max for Live patch using `max/sieve.js`

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
   - `sifters/dois_series/dois_ten/max/sieve.js` — Max for Live JS engine
