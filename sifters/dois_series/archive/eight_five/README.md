# eight_five

A piece of its own, made from the same sieve as the `dois` series: **psappha's voices with
D running against the others at 8:5** — the sieve's own two moduli — instead of 4:3.

Everything else is `dois_44`, engine and all: A is the psappha sieve, B its complement, C
its canon at the lattice's diagonal, D the intersection of A and C. Only D's basic unit
moved, from a triplet eighth (160 ticks) to a quintuplet eighth (192). Every number below
follows from that one setting.

## Why 8:5

The `dois` series sets the sixteenth against the triplet eighth, 4:3 — a ratio the sieve
does not contain; the author chose it. Psappha's sieve is written in moduli 8 and 5, so its
own ratio is 8:5, and a quintuplet eighth (five in the time of two quarter notes) against a
sixteenth is exactly that.

## What follows from it

| | `dois_44` (4:3) | `eight_five` (8:5) |
|---|---|---|
| D's step | 160 ticks, triplet eighth | 192 ticks, quintuplet eighth |
| first convergence (parity) | 19,200 ticks — 20 s at 120 BPM | **38,400 ticks — 40 s** |
| passes: A, B, C / D | 4 / 3 | **8 / 5** — the moduli again |
| span moduli | 32 / 3 | **64 / 25** |
| closest passes anywhere | 8 steps apart | 7 steps apart |
| per voice (weakest–strongest pair) | A 17–19, B 8–9, C 18, D 12–15 | A 13–19, B 7–8, C 13–17, D 11–13 |
| velocity table | 1 19 37 73 55 91 109 127 | the same |
| the form | 40 × 20 s = 13'20" | 40 × 40 s = **26'40"** |

The restatement counts come out as the sieve's moduli: eight passes of the sixteenth voices
against five of D. The span accents fill half of every block their passes cycle through
(`dois_42`'s rule): 32 of 64, and 10 of 25 — half of each five-position block, rounded down.
The mod-25 set is the best of all 100,000 half-full sets; the mod-64 set comes from a local
search among 5.8 × 10^14, which says so when it runs and may have missed a better one.

**D in time.** The quintuplet grid meets the sixteenth grid only every 960 ticks — once per
half note — so one D step in five lands on a sixteenth. D is still the intersection of A
and C counted in steps, re-timed, as in `dois_44`; the re-timing is just further from the
sixteenths' grid.

## Files

`python3 compose.py` writes into `mid/`, as the `dois` versions do:

- `eight_five_static_*`, `eight_five_lattice_*`, `eight_five_canon_*`: each voice's own
  file, the four-track arrangement and the one-track ensemble — 38,400 ticks, 8 bars of
  40/16;
- `eight_five_lattice_form.mid`, `eight_five_canon_form.mid`: the forms, 40 sections;
- `eight_five_wavetable_*`: the Serum wavetables. **Only D has a sweep table**: A, B and C
  state themselves over 320 steps, more than Serum's 256 frames;
- `eight_five_tuning.tun`, `.scl`, `.kbm`: the 40-step period as one octave.

`python3 compose.py --install-serum` puts the tables in Serum under **sifters →
eight_five**. Everything about using them is in `dois_44/README.md`.

## Tests

`python3 -B -m unittest discover -s tests` — 7 tests about this piece: it renders and every
set verifies, the 8:5 arithmetic above, the residues pinned in `config.py` are the ones the
search derives, the forms, and the sweep tables. The engine is `dois_44`'s, unchanged, and
its 110 tests live there.

## Status

Not yet heard. Every check is structural.
