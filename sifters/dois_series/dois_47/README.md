# dois_47

The current version, and the starting point for a composition: twenty seconds of four
percussion voices, derived entirely from one sieve (Xenakis's psappha), and the Serum
instrument each voice plays, derived from the same sieve. Change the sieve in `config.py`
and all of it recomputes.

## Start here, in Ableton

1. **Once:** from this folder, `python3 compose.py --install-serum`. It renders the files
   and installs the presets and wavetables in Serum. (It needs Python 3.14 and
   `pip install -r requirements.txt`.)
2. **New Live Set at 120 BPM.** Optionally set the time signature to **40/16**, so one bar
   is one statement of the sieve's 40 steps; in 4/4 the loop is 10 bars.
3. **Drag `mid/dois_47.mid` into the arrangement.** It holds four tracks, **A, B, C, D**.
   (If Live puts it on one track, unfold the file in the browser and drag the four tracks
   in.)
4. **On each track, load Serum and the preset with the track's name**, from **User →
   sifters → dois_47**: `dois_47 A` on track A, and so on. Each preset is finished: pitch
   tracking off, pitch set, velocity routed.
5. **Loop the 20 seconds and play.** It is quiet: the four together peak around −7 dBFS
   and average around −32 dBFS, so raise the tracks or the master.

## What you are hearing

| track | voice | attacks per 40 steps | grid | its drum |
|---|---|---|---|---|
| A | the psappha sieve | 27 | sixteenths | 172.8 Hz, rings 125 ms |
| B | the complement of A: every step A leaves out | 13 | sixteenths | 83.2 Hz, rings 375 ms |
| C | A, 13 steps later: a canon | 27 | sixteenths | 172.8 Hz, rings 125 ms |
| D | where A and C both strike, replayed on triplets | 20 | triplet eighths | 96 Hz, rings 333 ms |

**The rhythm.** A and B tile every sixteenth between them. D's triplet grid against the
others' sixteenths is a 4:3 polyrhythm; the loop is the first moment all four end
together (**parity**): A, B and C state their 40-step rhythm 4 times, D 3 times.

**The accents.** One accent pattern, read off the sieve, lies over every voice, and one
moving accent makes each restatement different, so the rhythm repeats while the music
never does. The accents become velocity, one of eight values (1, 19, 37 … 127), and the
same accents give the same velocity in every voice.

**The sound.** Each voice is its own drum: its pitch is its attack rate, five octaves up;
it rings over its median gap between attacks; and each stroke falls 390 cents (13/40 of an
octave) over one step. Its wavetable states the sieve in every frame, and a second
oscillator plays the voice's complement as an FM modulator. **Velocity drives all of it at
once:** it picks the wavetable frame (timbre), sets the level, and opens the FM
(brightness). Loud accents open near 11 kHz and settle.

## Developing it in Ableton

- **Velocity is the material.** Editing a note's velocity changes its timbre, loudness
  and brightness together. The eight values the piece uses each pick a different frame.
- **Form is yours to build.** The code makes the loop; arrangement happens here. One
  reading the sieve itself offers: play the loop 40 times and let voice X sound in pass
  *s* when its rhythm strikes at step *s* (A in 27 passes, B in the 13 A leaves, C in 27,
  D in 20). Through these presets that gives only four different sections, so it needs
  something else to change between them; `archive/dois_46` wrote it out with the pitch
  lattice doing that.
- **The notes are on one key per track** (A 36, B 37, C 38, D 39, C1 upward), so the
  file also drops onto a Drum Rack or hardware drum voices as it is.
- **Abutting notes.** A note fills its step, so half of A's and C's notes end on the tick
  the next begins. Serum retriggers them; a device that will not needs
  `GATE_RATIO = 0.5` in `config.py`.

## Changing the piece

Everything specific is in `config.py`: the sieve, how the voices relate (complement,
shift, intersection, union, retrograde, augmentation), each voice's grid, tempo, the
velocity range, the note length, and three chosen numbers for the drums
(`KIT_OCTAVES_UP`, `KIT_LEVEL`, `FM_PEAK_DEPTH`). After changing the sieve or a grid, set
`SPAN_RESIDUES = None` so the accents are derived again. Then run
`python3 compose.py --install-serum` and reload the presets.

A setting that cannot work is refused before anything is written, with the reason: an
accent that would push past parity, accents that would leave two restatements identical,
a sieve too sparse to tell its restatements apart, a note MIDI cannot hold.

## Files

```sh
python3 compose.py                        # render and verify
python3 compose.py --install-serum        # the same, then install in Serum
python3 compose.py --suggest-span         # report on the moving accent, write nothing
python3 -B -m unittest discover -s tests  # 107 tests, about 30 seconds
```

| folder | what a render makes |
|---|---|
| `mid/` | `dois_47.mid`: a track per voice, 19,200 ticks (20 s at 120 BPM), 4 bars of 40/16 |
| `wavetables/` | 8 Serum tables: each voice's, and its complement's (`not A` …), 128 frames |
| `presets/` | 4 Serum presets, `dois_47 A` to `dois_47 D`, one per track |

Every file is read back and checked before it replaces anything; a failed check leaves the
last render as it was. A render of the same code and settings gives the same bytes, in any
folder.

| module | does |
|---|---|
| `config.py` | the piece: sieve, voices, grids, accents, drum constants |
| `compose.py` | runs everything below in order |
| `sieve.py` | evaluates sieves, measures their periods, derives the voices |
| `accents.py`, `span.py` | the shared accents, the moving accent, velocity |
| `midi.py` | timing, meter, writing and reading MIDI, staging |
| `wavetable.py` | the Serum wavetables, and installing them |
| `serum.py`, `serum_init.json` | the Serum presets, written in Serum's own format |
| `check.py` | verifies every file, recomputing what it checks its own way |

## The principles, and how they are held

- **I. A duration states the period.** Each voice's rhythm is its sieve's 40 steps on its
  own grid; nothing is padded or cut.
- **II. Parity at the first convergence.** 19,200 ticks is the first tick all four end
  together; the tests prove nothing shorter works, by brute force.
- **III. One weather, and nothing repeats identically.** One accent pattern over every
  voice; every restatement of every voice is checked to differ.
- **IV. The moving accent is exactly as long as parity needs**, on the smallest modulus
  that reaches it (32 for the sixteenths, 3 for the triplets).
- **VII. The engine is general.** Only `config.py` names this piece; the tests render other
  sieves (7 × 5, three moduli 8 × 5 × 3) and other grids end to end.

Derived, not chosen: every rhythm, the accents and their velocities, parity, meter, C's
13-step distance, the wavetables, and each drum's pitch, decay, strike and modulator.
Chosen: the sieve, how the voices relate, the grids, tempo, velocity range, gate, and the
three drum constants.

## Known limits

- The presets are written in Serum 2.1.5's own format, which Xfer does not document. A
  later Serum is expected to open them, as it opens older presets, but a major update may
  need the format re-read. A preset plays only with its tables installed.
- At the loudest accents the FM's brightness covers each frame's own colour.
- The moving accent's residues come from a search; for very large moduli it is a local
  search and may miss the best (it says so). Psappha's are exhaustive.
- The checks are structural; how it sounds is the composer's to judge.

## What dois_47 changed

- **One starting point.** A render makes 13 files: one MIDI file with a track per voice,
  the 8 tables, and one preset per track, the FM pair at 1:1 that the author chose from
  study 6. Through these presets, which do not play pitch, the lattice and canon sets
  sounded exactly like the static set, and the 13'20" forms had only four different
  sections among their forty. The pitch lattice, the canon set, the forms, the tuning
  files, the sweep tables and sidecars, the other presets, the per-voice and ensemble MIDI
  files, and the second piece, `eight_five`, are gone from the engine. All of it is in
  [`../archive/dois_46`](../archive/dois_46/README.md), which still renders it.
- **More general.** Without the lattice's two-moduli requirement, a sieve in three moduli
  now renders (tested).
- **Same bytes in any folder.** The provenance stamp had hashed the project's folder path,
  so identical music got a different stamp in every checkout.
- **Mistyped options are refused** (`--install` once rendered and installed nothing), a
  Python older than 3.14 is told why it cannot run, and every render ends with what to
  open in Ableton.
- **Proven:** `dois_47.mid` is `dois_46`'s static set message for message, and the tables
  and presets are `dois_46`'s byte for byte and value for value; Serum plays the presets
  sample for sample like `dois_46`'s. 107 tests.

Earlier versions are in [`../archive/`](../archive/); `dois_46`'s README documents the
lattice, canon, form and tuning, and `dois_44`'s records each change from `dois_31` on.
