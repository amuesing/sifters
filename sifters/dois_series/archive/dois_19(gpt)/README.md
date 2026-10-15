# dois_19(gpt) — stationary local accent weather

Fork of dois_18(gpt), changing accent phase only. Claude's versions and earlier GPT
versions are untouched. Compare this version with dois_18(gpt) using the same patches.

## What changed

Previously C shifted its rhythm AND every accent binary by 13 steps. At local step i,
it therefore sampled the accent field at i-13. This version retains C's shifted
rhythm and pitch relationship, but evaluates all accents at unshifted local step i.
The derived span accent stays stationary as well as the two shared weather sieves.
No accent definition, modulus, residue, rarity rule or velocity table was changed.

ACCENT_PHASE_POLICY='fixed_local_steps' states and fingerprints the rule. This version
only accepts that policy; the previous version supplies the follow-shift comparison.
A/B/D were already unshifted, so only C's velocities change. Those velocities may
control timbre or other synth parameters, not just volume.

## Measured comparison with dois_18(gpt)

| Property | Result |
|---|---|
| A/B/D complete note events | Unchanged |
| C onset, duration, pitch, channel, count | Unchanged |
| C velocities changed | 84 of 108 (77.8%) |
| Notes A/B/C/D | 108/52/108/60 |
| Total notes | 328 |
| First parity | 19200 ticks; 40 quarter notes; 20 seconds at 120 BPM |
| Distinct complete accented passes | A4/B4/C4/D3 |
| Accented minimal period | Full statement for every voice |

The first parity is still derived from the original raw rhythm periods. Neither
extra time nor pitch variation is used to excuse repeated complete accented passes.

## What 'one weather' means here

Weather is stationary in LOCAL STEP coordinates. A, B and C share a 120-tick step,
so their accent states and velocity values agree at coincident attacks. D uses a
160-tick step; the same local index is a different wall-clock time. This is not a
single absolute-time weather clock, and unequal rhythm clocks are still supported.

D also retains Claude's per-grid velocity ranking and its distinct derived span
accent. Fixing C's phase does not resolve the separate question of one shared
state-to-velocity table. That question remains an isolated future comparison.

## Pitch remains the additive lattice reference

Axes 8 and 5 must close into twelve pitch classes: 8a=0 and 5b=0 modulo12. Smallest
positive maximal-image generators give (a,b)=(3,0), derived from the axes by gcd.
Default MIDI pitches are 36/39/42/45 (C/Eb/F#/A). Root36, positive direction and a
single-octave realization are explicit choices. The four-class limit follows from
this additive mapping, not a permanent project requirement. Pitch field period is
four local steps; mod5 still influences rhythmic membership but not class movement.
C retains +3 mod12 pitch transposition: actual intervals +3 x20 and -9 x7.

## Run and audition

From this directory, in the existing Development environment:

```bash
../../../../.venv/bin/python -B composition.py
../../../../.venv/bin/python -B -m unittest discover -s tests -v
```

Requires mido, music21, numpy. Six ordinary MIDI files are already exported under mid/:
four prime voices, a four-track arrangement and a single-track ensemble (channels1–4).
Use pitched instruments. To isolate the difference, replace only C's clip from
version18 with version19 while keeping the patch and other clips unchanged.

Eight tests cover independent stationary-accent arithmetic, shared A/B/C values,
all MIDI events, unchanged non-C data, additive pitch mapping and canon, unequal clocks,
range rejection before overwriting, and complete accented-pass nonrepetition. A separate
raw-byte decoder checks all six exports against version18 and exact rational accent
ranking; VALIDATION.json records the results. No instrument audition is claimed.

Publication retains the simple inherited replacement behavior: generated names are
replaced, unrelated files preserved; failures after writing may require rerendering.
FOR_CLAUDE.md in the repository root records the isolated change and its measurements.
