# Sifters — Project Context

> This file is the canonical reference for continuing work across machines and sessions.
> **Always update this file at the end of a working session.**
> Last updated: 2026-08-18

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

| Voice | Relationship | Density | MIDI Pitch | Step Grid | Cycle |
|-------|-------------|---------|-----------|-----------|-------|
| A | Base sieve | 15/40 (37.5%) | 36 (C1) | 16th note (120 ticks) | 4800 ticks |
| B | Complement of A | 25/40 (62.5%) | 55 (G3) | 16th note (120 ticks) | 4800 ticks |
| C | A shifted +13 steps (canon) | 15/40 (37.5%) | 48 (C3) | 16th note (120 ticks) | 4800 ticks |
| D | Intersection of A and C | 6/40 (15%) | 60 (C4) | Triplet 8th (160 ticks) | 6400 ticks |

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

- `dois_ten_A_prime.mid` — 4800 ticks, loops cleanly
- `dois_ten_B_prime.mid` — 4800 ticks
- `dois_ten_C_prime.mid` — 4800 ticks
- `dois_ten_D_prime.mid` — 6400 ticks
- `dois_ten_arrangement.mid` — 19200 ticks, one full LCM cycle, all four voices on separate tracks

### Important Bug Fixed

MIDI clips were previously ending at the last note-off tick instead of the true cycle boundary. `end_of_track` was being placed at `time=0` after the last note. Fixed by computing `remaining = cycle_ticks - last_note_off` and explicitly appending `end_of_track` with that delta. Without this fix, Ableton reads clips as slightly short and loops drift over time. This fix is in both `save_midi` (individual clips) and `save_ensemble_loop` (arrangement).

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
`save_ensemble_loop` computes `math.lcm(*cycle_lengths)` and writes each voice out for exactly that many ticks. Handles any combination of step durations. Each track padded to `total_ticks` with explicit `end_of_track`.

### Voice Derivation Philosophy
Voices are **derived** from a single base sieve, not independently designed. The user explicitly preferred this approach — complement, canon (shift), and intersection relationships produce a coherent ensemble that is mathematically unified. Do not propose independently-designed sieves as separate voices.

---

## Plugin Architecture (Future)

### Target: Max for Live MIDI Effect
- Single `.amxd` file, drag onto any Ableton track
- All four voices output on different MIDI pitches → one Drum Rack on the same track
- No cross-track routing needed

### Drum Rack Pitch Mapping
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

## What's Next (as of 2026-08-18)

- [ ] Update `dois_ten` to output all voices on Drum Rack pitches (36/37/38/39) in a single combined clip — the true plugin-ready output format
- [ ] Test dois_ten in Ableton with a Drum Rack to validate the musical result
- [ ] Decide on next layer of complexity to add (form/arrangement, parameter variation, sieve formula controls)
- [ ] Eventually: assemble the Max for Live patch using `max/sieve.js`

---

## Running the Code

```bash
cd sifters/sifters/dois_series/dois_ten
python composition.py
```

Output appears in `mid/`. Requires: `mido`, `music21`, `numpy`.

---

## How to Continue on Another Machine

1. `git pull` to get latest code and this file
2. Open this file first to re-establish context
3. The key files to read are:
   - `sifters/dois_series/dois_ten/config.py` — voice definitions
   - `sifters/dois_series/dois_ten/composition.py` — full pipeline
   - `sifters/dois_series/dois_ten/max/sieve.js` — Max for Live JS engine
