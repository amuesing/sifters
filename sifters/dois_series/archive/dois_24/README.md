# dois_24

The production version. One rhythm, rendered two ways.

    python3 compose.py                 render all twelve files and verify them
    python3 compose.py --suggest-span  for a new sieve: the residues its accents need
    python3 -B -m unittest discover -s tests -v

Needs Python with `mido`, `music21` and `numpy`.

## Which file to use

| | |
|---|---|
| `mid/dois_24_static_*` | one fixed note per voice — A=36, B=37, C=38, D=39. Pitch carries nothing; the sieve speaks through rhythm and velocity. **This is the Moog Grandmother set**, which cannot take pitch as a CV source. |
| `mid/dois_24_lattice_*` | pitch read off the sieve's own 8x5 grid, MIDI 36-75. Same rhythm, same velocities — only the pitch differs. |

Within each set: `_A_prime` … `_D_prime` are the single voices, `_arrangement` is the
same four on four tracks, `_ensemble` is all four on one track with **one MIDI channel
per voice** (0-3), for routing a single clip out to hardware.

Every file is 19200 ticks — 20 seconds at 120 BPM, 4 bars of 40/16, equivalently 10 bars
of 4/4. 108/52/108/60 notes. The declared meter is 40/16 because one bar is one pass of
the note layer; Ableton takes its tempo from the project, not the file.

## What is guaranteed

Checked on every run, from the written files rather than from the code that wrote them:

- all four voices end together at the first convergence of their raw rhythms;
- no pass of a voice's note layer is identical to any other;
- one weather: voices sharing a grid carry the same velocity wherever they strike together;
- one velocity table: the same accent combination means the same velocity in every voice,
  every note checked against a table rebuilt from config with exact fractions;
- every note carries the pitch its step earns, recomputed by a different formula than the
  one that wrote it;
- each voice's own file equals its arrangement track and its ensemble channel, cycle for cycle.

Renders are byte-identical when nothing changes, so a diff in `mid/` means the music moved.

## The gate

`GATE_RATIO = 1.0`: a note fills its step, so its note-off lands on the tick the next
note-on begins — 127 such pairs across the four voices, 52% of A and C. This is what lets
A and B tile time continuously between them, and it plays correctly through samplers.
The MIDI spec leaves it to the DEVICE whether a Note On for a sounding pitch retriggers.
If a synth swallows them, set `GATE_RATIO = 0.5` in `config.py` — nothing else changes.

## Changing the sieve

`config.py` describes this composition; every other module works for any sieve
(Principle VII). Change the sieve there and the note layers, parity, span accents, meter
and pitch intervals all recompute. `WEATHER` and `SPAN_RESIDUE_SOURCE` are compositional
choices that stay in config — if they do not suit the new sieve the render refuses before
writing anything and `--suggest-span` names residues that work. A test renders a
different sieve (moduli 7 and 5) end to end.
