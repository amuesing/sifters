# dois_46

The current version. Everything musical is derived from the sieve in `config.py`: the
rhythms, the accent field the velocities are built from, the parity point, the meter, the
pitch lattice, the canon distance, the wavetables, the form, and now the instrument. Change
the sieve, or any voice's basic unit, and all of it recomputes.

**`dois_46` renders the instrument with the music.** Every render now also writes Serum 2
presets for every voice: a drum whose pitch, decay and strike come from the voice's own
rhythm, and FM pairs, the drum frequency-modulated by the voice's complement (the table of
every step it leaves out) at ratios from the sieve's numbers. Both were worked out and
measured in Serum in `dois_44_studies` (the percussion kit and study 6); here they are part
of the engine, written in Serum's own file format with nothing but Python's standard
library, and checked like everything else. The music is `dois_45`'s, note for note.

## Two pieces

| | `dois_45` | `eight_five` |
|---|---|---|
| settings | `config.py` | `config.py`, with `pieces/eight_five.py` laid over it |
| D's basic unit | triplet eighth, 160 ticks: **4:3** | quintuplet eighth, 192 ticks: **8:5**, the sieve's own moduli |
| parity | 19,200 ticks, 20 s; A/B/C state their rhythm 4x, D 3x | 38,400 ticks, 40 s; 8x and 5x |
| span moduli | 32 and 3 | 64 and 25 |
| form | 13'20" | 26'40" |
| renders into | `mid/`, `wavetables/`, `tuning/`, `presets/` | an `eight_five/` folder inside each |

A piece names only what it changes (`TITLE`, settings, and a `VOICES` dict of changes to
named voices); everything else is `config.py`'s.

## Run and use

With Python and the pinned versions installed (`pip install -r requirements.txt`):

```sh
python3 compose.py                        # dois_46
python3 compose.py --piece eight_five     # eight_five
python3 compose.py --suggest-span         # reports on the span residues, writes nothing
python3 compose.py --install-serum        # also installs the tables and presets in Serum
python3 -B -m unittest discover -s tests  # 136 tests, about a minute
```

Each kind of file has its own folder (`eight_five`'s go in an `eight_five/` folder inside
each):

- **`mid/`**
  - `<title>_static_*`: fixed pitches A=36, B=37, C=38, D=39;
  - `<title>_lattice_*`: pitches derived from the sieve's lattice;
  - `<title>_canon_*`: the lattice read at each note's source step, so C is a literal
    canon of A;
  - `<title>_lattice_form.mid`, `<title>_canon_form.mid`: the form, four tracks, 40
    sections.
- **`wavetables/`**: the Serum wavetables, `<title>_wavetable_*.wav`, each with a `.txt`
  sidecar: each voice's table, its sweep, and its complement (`_not_A` and so on).
- **`tuning/`**: `<title>_tuning.tun`, `.scl` and `.kbm`, the 40-step period as one octave.
- **`presets/`**: 32 Serum presets, `<title> kit <voice> <accents|lattice>` and
  `<title> FM <voice> <accents|lattice> <1-1|8-5|13-1>` (see below).

Each mode has four `_prime` voice files, a four-track `_arrangement`, and a single-track
`_ensemble` with the voices on separate MIDI channels. For `dois_46` every file ends at
19,200 ticks (40 quarter notes, 20 seconds at 120 BPM) in 40/16; the voices play 108, 52,
108 and 60 notes.

## The four voices

| voice | derivation | basic unit |
|---|---|---|
| A | the psappha sieve itself: 27 attacks in 40 steps | sixteenth |
| B | the complement of A: the 13 steps A leaves out | sixteenth |
| C | A shifted by the lattice's diagonal, 13 steps: a canon | sixteenth |
| D | the intersection of A and C, counted in steps | triplet eighth |

A and B tile every sixteenth between them. **D is an intersection of step NUMBERS, not of
moments**: it takes the 20 steps where A and C both attack and plays them on its own
grid, so in time only 10 of D's 60 notes land where A and C sound together. D is the
convergence pattern re-timed at 4:3.

**C's distance is derived**: `'diagonal'` is the lattice's diagonal, sum(P/m) over the
sieve's moduli, 5 + 8 = 13. The same number turns steps into pitches and orders the
wavetable frames, so one derived number drives the canon, the lattice and the timbres.

## Where each idea lives

| File | Purpose |
|---|---|
| `config.py` | The piece: sieve, voice relationships, durations, accents and pitch settings. |
| `pieces/` | Other pieces, each naming only what it changes from `config.py`. |
| `compose.py` | Runs the steps below in order, and loads a piece. |
| `sieve.py` | Evaluates sieves, measures their real periods, derives each voice. |
| `accents.py` | The weather, the span accent's modulus, and velocity from accent states. |
| `span.py` | The span accents' residues: one set per modulus, half of every block. |
| `pitch.py` | The static, lattice and canon pitch rules, and their checks. |
| `form.py` | The form: one section per step of the sieve. |
| `tuning.py` | The lattice's period as one octave: `.tun`, `.scl` and `.kbm`. |
| `wavetable.py` | The Serum wavetables and the voices' complements, and installing them into Serum. |
| `serum.py` | The Serum presets: each voice's drum and FM pairs, written in Serum's own format. |
| `serum_init.json` | Serum 2.1.5's init patch, which every preset starts from. |
| `midi.py` | Staging, timing, meter, and writing and reading MIDI. |
| `check.py` | Verifies every rendered file, recomputing what it checks its own way. |

A **step** is one position on a voice's grid; a **note layer** is the voice's shortest
repeating rhythm. The **weather** is the accent field every voice shares; the **span
accent** is the one accent that moves, distinguishing the restatements parity forces. One
**velocity table**, shared by every voice, maps each combination of accents to a velocity,
so a combination means the same velocity everywhere. Velocity is a control signal, not
just loudness.

## The lattice

**The sieve decides WHEN a voice sounds; the lattice decides what PITCH that step gets.**
Every step of the 40-step cycle has an address, its place in the 8-cycle and in the
5-cycle; because 8 and 5 share no factor, no two steps share one, so each can carry its
own pitch:

```text
pitch = root + (5 × (step mod 8) + 8 × (step mod 5)) mod 40
      = root + (13 × step) mod 40
```

The renderer uses the first form and the verifier the second, so neither vouches for
itself. In `lattice` every voice reads it at its own step, so voices that attack together
are in unison (A and C share 80 attacks). The lattice needs exactly two coprime moduli and
a range that fits MIDI; `static` needs neither.

## The canon set and the tuning

`canon` reads the lattice at the step each note comes FROM: a shift reads back by its
distance, a retrograde reflects, an augmentation divides; a complement or intersection
keeps its step. Here only C differs: its note at step *n* is A's at step *n* − 13, so the
canon is a canon in pitch as well as rhythm, and where A and C meet they sound 31 lattice
steps apart instead of a unison.

With the period as an octave each lattice step is 30 cents:

| lattice move | steps | 12-TET (untuned) | 40 steps to the octave | nearest ratio |
|---|---|---|---|---|
| one step of the sieve | ×13 | a minor ninth | 390 cents | 5/4 (386) |
| the canon's displacement | +9 | 9, or −31 at the fold | 270 cents | 7/6 (267) |
| C against A, canon set | 31 | 31 | 930 cents | 12/7 (933) |

Load `<title>_tuning.tun` in Serum (Global → TUN FILE → Load Tuning; it is saved with the
preset), or the `.scl` and `.kbm` into the free MTS-ESP MINI to retune every instance at
once. Verified in Serum 2: notes land exactly 30 cents apart. Tuning only matters where
pitch is heard; with pitch tracking off, a note number picks a frame, not a frequency.

**Held notes.** `ARTICULATION = 'held'` makes every note last until its voice's next
attack, so the sieve's gaps become durations and envelopes and wavetable position have
time to move. Every note then abuts the next, so a device that will not retrigger needs
the default, `'step'`.

## The form

```
section:  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9
A         x x . x x . x . x . x x x x x . x x . x x . x x . x . x x x . x . x . x x x x .
B         . . x . . x . x . x . . . . . x . . x . . x . . x . x . . . x . x . x . . . . x
C         x x x . x . x . x x x x . x x . x x . x . x . x x x x x . x x . x x . x x . x .
D         x x . . x . x . x . x x . x x . x x . x . . . x . x . x . x . . . x . x x . x .
```

The form is the rhythm read again, one section per step: voice X plays a parity statement
in section *s* exactly when its rhythm attacks at step *s*. Each section reads the lattice
*s* steps further on, a transposition by 13 × *s*, so no two of the 40 are alike: with the
40-step tuning a chain of major thirds through every pitch class; with NOTE → WT POS a walk
through the wavetable's registers. The static set has no pitch to move, so it has no form.
`check.check_form` rebuilds every section from the voice's own file and requires all 40 to
differ.

## Serum wavetables

**The rule.** Frame *i* reads one period of the voice's sieve from *i* + 1 and sounds it
from just above its cut *c* = 13 × *i* mod 40: harmonic *c* + *h* sounds, at full strength,
when *i* + *h* is in the sieve. Every member of the sieve sounds once in every frame. The
reading gives 40 different frames; the cut gives each its own register (brightness), with
neighbours 13 harmonics apart. One gain for the whole table keeps every frame at the same
RMS, so VELO changes colour, never loudness. 128 frames, one per note or velocity value;
the sweep table follows the voice's parity statement, one frame per step.

**Getting them in.** `python3 compose.py --install-serum` finds the presets folder your
Serum uses (from `~/Library/Preferences/Serum2Prefs.json`) and copies the tables into
`Tables/sifters/<title>/` as `A.wav`, `A sweep.wav` and so on. Rescan or restart Serum and
they appear under **sifters → dois_45** (and **sifters → eight_five**).

**Using them.**

1. Load `A` and turn **pitch tracking off** (right-click the oscillator's label).
2. **Raise OCT to +4.** With tracking off the oscillator plays MIDI note 0, 8.18 Hz; OCT +4
   is 130.8 Hz. Anything up to about 276 Hz keeps every frame's top harmonic below Nyquist.
3. Route **NOTE → WT POS** (lattice or canon MIDI) or **VELO → WT POS** (any set) at 100%:
   value *v* lands exactly on frame *v*. Leave KEY/SCALE off, or notes move to other frames.

For the sweep table, automate WT POS from 0 to 1 across the clip and turn on **Disable
Smoothing** (Global → Quality). Every frame of every table is read back, measured with an
FFT and matched to the rule by `check.py`; six tests break a table and require the run to
be refused.

## Serum presets

`--install-serum` puts every piece's presets in Serum's browser under **User → sifters →
dois_46** (and **dois_46 eight_five** for the second piece), beside its tables under
**sifters → dois_46**, so a voice's MIDI plays straight into its instrument. Pitch tracking
is already off and the pitch already set.

**Every folder and preset is labelled with its version**: a piece's folder carries the
version beside the piece's name, and so does each preset's name (`dois_46 eight_five FM D
accents 1-1`), so two versions' presets can never share a folder or a name. Installing
replaces the files in that one folder, so a preset a render no longer makes cannot linger
beside the new ones; other versions' folders are left alone.

**The drum** (`<title> kit A accents`): one rule for every voice, its own rhythm supplying
the numbers.

| part | from | A | B | C | D |
|---|---|---|---|---|---|
| body | the voice's own table | `A` | `B` | `C` | `D` |
| pitch | attacks per second, `KIT_OCTAVES_UP` (5) octaves up | 172.8 Hz | 83.2 Hz | 172.8 Hz | 96 Hz |
| decay | the median gap between attacks | 125 ms | 375 ms | 125 ms | 333 ms |
| strike | the pitch falls d/P of an octave (13/40: 390 cents) over one step | 125 ms | 125 ms | 125 ms | 167 ms |

Velocity takes the level from `KIT_LEVEL` (0.35) to 1. **accents** presets let velocity
pick the frame, for the static set; **lattice** presets let the note pick it, for the
lattice and canon sets and their forms.

**The FM pair** (`<title> FM A accents 1-1`): the drum with a second oscillator as a live
FM modulator, playing the voice's **complement** (`not A` is B's table byte for byte, so A
and B modulate each other). The FM depth has an envelope of its own over the voice's
median gap, scaled by velocity: each stroke opens near 11 kHz and settles back to its own
colour, and the accent weather is heard as brightness. The ratio (modulator to carrier) is
one of the sieve's numbers: 1:1, its moduli 8:5, its diagonal 13:1.

**How they are written.** Serum's preset format is undocumented; it was read from Serum's
own files (`dois_44_studies/serum_state.py`): a JSON header, then the patch as CBOR,
zstd-compressed, with an MD5 of the compressed bytes. `serum.py` writes it with its own
CBOR encoder, pinned to RFC 8949's examples, and Python 3.14's zstd. Every patch starts
from Serum 2.1.5's init patch (`serum_init.json`). `check.py` reads every preset back with
a reader of its own and recomputes each derived number: the pitch from OCT/SEM/FINE, the
decays, the strike, the ratio and every routing. Serum itself, loading these files,
renders them sample for sample like the studies' patches.

## What is derived, and what you still choose

Derived from the sieve, for any sieve:

- each voice's rhythm and the period it actually closes on;
- **the weather**: one accent per modulus the sieve uses, on the half of the residues its
  attacks favour, chosen so that every voice meets every on/off combination of the accents
  (the whole velocity profile in every voice);
- **the span accent's modulus**: the SMALLEST M with lcm(layer, M) equal to the steps the
  voice needs to reach parity (a voice that reaches parity in one pass uses its own layer);
- **the span accents' residues**: half of every block, the closest passes furthest apart,
  exhaustively up to two million candidate sets per modulus and by local search beyond
  (see `span.py`). `config.py` and `pieces/eight_five.py` pin the answers, and the tests
  fail if the search ever stops agreeing;
- the parity point, the meter, the lattice's axes and intervals, C's canon distance and
  the wavetables' frame order;
- each voice's drum (pitch, decay, strike) from its rhythm, its FM modulator (its
  complement), and the FM ratios (the sieve's own numbers).

Still yours: the sieve, how the voices relate, the basic units, tempo, root note, gate and
velocity range; and for the presets, `KIT_OCTAVES_UP`, `KIT_LEVEL` and `FM_PEAK_DEPTH`. Naming `WEATHER` or `SPAN_RESIDUES` overrides the derivation and is checked
the same way.

## Parity is a minimum, not a target

```
A, B, C   40 steps x 120 ticks = 4,800
D         40 steps x 160 ticks = 6,400
                          LCM  = 19,200 ticks   <- nothing shorter works
```

`tests/test_requirements.py` asserts from the project itself that the parity point is
minimal (by brute force), that every accent profile is exactly that long, and that each
span accent uses the smallest modulus that reaches it.

## When something cannot work

Everything is checked BEFORE a file is replaced, so a refusal leaves your renders as they
were:

| What you set | What happens |
|---|---|
| a `WEATHER` accent whose period does not divide the note layer | refused, naming the accent, its measured period and the layers it fights |
| `SPAN_RESIDUES` that leave two passes of a voice identical | refused, naming the voice and the pass pair, pointing at `--suggest-span` |
| `SPAN_RESIDUES` pinned for another sieve or other basic units | refused, naming the modulus with no set |
| a sieve whose voices cannot have distinct passes | refused with the count that proves it: k attacks allow at most 2^k different passes |
| a pitch mode that cannot render for this sieve | refused before any mode writes |
| a search that finds nothing | says the bounded SEARCH failed, not the sieve, and names any set that meets Principle IV but misses a selection rule |

Renders go to a **staging folder** beside the output folders and move in only once every
file is written and verified; files there that the run did not produce are never touched.

## Known limits

- The span residues are found by search, not counted off the sieve: the sieve's density
  at the span modulus repeats with gcd(layer, modulus), so counting can never span the
  modulus. Above two million half-full sets the search is local and may miss the best;
  it says so (eight_five's 64 is such a case).
- With the span accent on half its positions, the states that include it are as common as
  those without; the velocity ranking is still by rarity.
- A sieve too sparse for its span accent, or one where no weather lets every voice sound
  every velocity, is refused with the reason.
- The presets are written in a format Xfer does not document, read from Serum 2.1.5's own
  files. A later Serum is expected to open them, as it opens older presets, but that is
  untested. The strike's depth rests on a measurement (a pitch mod amount of 1 is about
  1.2 semitones: 390 cents measured as 389).
- A preset plays only with its tables installed (`--install-serum`).
- At the loudest accents the FM's brightness overrides each frame's own register (study 6).
- Every check here is structural. Renders through Serum itself are in
  [`../dois_44_studies`](../dois_44_studies/); what they sound like is the author's to
  judge.

## What dois_46 changed

- **Serum presets, rendered with the music** (`serum.py`): 32 per piece, a drum per voice
  and its FM pairs at three ratios, in `presets/`, installed under User → sifters, in a
  folder labelled with the version (`dois_46`, `dois_46 eight_five`) that installing replaces.
- **Complement tables** in `wavetables/`, the FM pairs' modulators, checked frame by frame
  like the voices' own.
- **Proven:** the MIDI, the voices' tables and the tuning files are identical to
  `dois_45`'s (39 files, provenance aside); the complement tables are byte for byte the
  study's; all 32 presets decode to the study's patches apart from names and table paths;
  and Serum, loading them, renders the same audio sample for sample. 136 tests, 17 new.

## What dois_45 changed

- **One engine, several pieces.** `pieces/eight_five.py` replaces the `eight_five` folder's
  copy of the engine; `compose.py --piece eight_five` renders it.
  Its tests joined this suite (`tests/test_eight_five.py`).
- **Two fewer modules.** `transformations.py` is now the relationship table in `sieve.py`,
  and the `Voice` record lives in `compose.py`. `compose.py`'s long `main()` is split into
  named stages.
- **A folder per kind of file**: MIDI in `mid/`, wavetables in `wavetables/`, tuning files
  in `tuning/` (`config.OUTPUT_DIRS`); each file is routed by its extension.
- **No dead code.** Two unused functions and three re-exported imports are gone.
- **Shorter commentary.** Docstrings keep what each part does and why, without the
  version-by-version history.
- **Up to date.** The tuning and wavetable notes now say what was verified in Serum (notes
  30 cents apart; tracking off plays MIDI note 0).
- **Proven unchanged.** Both pieces' renders were compared with `dois_44`'s and
  `eight_five`'s, every MIDI message and every wavetable byte: identical but for the
  provenance stamp. All 119 tests pass.

Earlier versions are in [`../archive/`](../archive/); `dois_44`'s README records each
change from `dois_31` on.
