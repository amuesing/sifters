# Sifters: A Data Synthesizer for Musical Composition

Sifters is a data-driven system for developing musical compositions, using logical sieves
as the foundation for creative exploration. The core idea behind Sifters is to synthesize
data that generates musical forms, all derived from a single logical source. This approach
draws inspiration from Iannis Xenakis’ analysis of Psappha (1975), where logical sieves are
used to determine rhythmic and structural elements. In this system, the sieve functions
similarly to an oscillator in an analog synthesizer, guiding the generation of musical
material.

The commit history in this repository chronicles my ongoing exploration of logic-based
operations applied to musical composition within the Python programming environment. Each
standalone folder within `sifters/` corresponds to a unique track intended to be realized
through Ableton; `dois_series/` holds one piece's successive versions.

> **Current version: [`dois_47`](sifters/dois_series/dois_47/)**, with its own
> [README](sifters/dois_series/dois_47/README.md): a 20-second, four-voice starting point
> for a composition in Ableton. Everything in it is derived from the sieve in its
> `config.py`: rhythm, accents and velocity, the parity point, meter, wavetables, and a
> Serum preset for every voice (its drum, FM-modulated by its complement). Change the
> sieve and all of it recomputes.
>
> **Two parallel lines share the numbering.** Bare `dois_NN` are Claude's; `dois_NN(gpt)`
> are ChatGPT's, most recently `dois_30(gpt)`. The numbers do not correspond between
> them, and each line's work is committed separately.

**Quick start:**

```bash
cd sifters/dois_series/dois_47
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python3 compose.py --install-serum   # renders and verifies it all, then installs it in Serum
```

Then, in Ableton at 120 BPM:
1. drag `mid/dois_47.mid` into the arrangement: four tracks, A, B, C, D;
2. on each track, load Serum with the preset of the same name, `dois_47 A` to
   `dois_47 D`, under **User → sifters → dois_47**;
3. loop the 20 seconds.

The version's README, under
[Start here](sifters/dois_series/dois_47/README.md#start-here-in-ableton), has the details
and what to develop from there.

## What a sieve is

A sieve is a set of integers described by modular congruences, combined with boolean logic:

```
5@0            every n where n mod 5 == 0
8@1|8@7        union — n mod 8 is 1 or 7
(8@0|8@1)&5@0  intersection
1 - binary     complement
```

`music21.sieve.Sieve` evaluates these into a binary array. **Where a number occurs, a
sound occurs.** The psappha sieve used throughout this project,

```
(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))
|8@3|8@4|(8@1&5@2)|(8@6&5@1)
```

draws on moduli 8 and 5, so it closes after LCM(8,5) = **40 steps**. That 40-step period
is the unit the whole project is built on.

The four terms on the second line are a correction made in `dois_14`: earlier versions of
this repository used the first line alone, which is the expression printed in the
*Frontiers in Psychology* article on Psappha. That article contradicts itself — the
expression it prints gives 15 attacks in 40 steps while its own prose claims 27. The
reading here matches the open-access copy (PMC7849451), and gives 27.
[`CONTEXT.md`](CONTEXT.md) records the check.

## How a sieve becomes music

Two decisions turn a set of integers into sound, and both matter:

**The basic unit** — how much time one step occupies. Picture the sieve plotted on graph
paper: the basic unit is the spacing between the lines, and the dots are the integers the
sieve produced. Choosing a different unit for one voice against another is what creates
polyrhythm.

**The duration** — a voice's total length must equal the *periodicity of its sieve*,
normally the LCM of all its moduli. This is not a formatting detail. A clip that stops
anywhere else misstates the sieve, and one padded out to match another voice's length
states a convenience rather than a structure.

It follows that **voices are not all the same length, and should not be**. When two
voices use different basic units, their durations differ — that is the polyrhythm being
honest about itself.

## Governing principles

These are the rules every version is held to. The READMEs cite them by number, and
`CONTEXT.md` sets each one out in full, with the reasoning behind it. The numbering skips
V and VI.

- **I. [What a duration must express](CONTEXT.md#governing-principle-what-a-duration-must-express).**
  A voice lasts exactly its sieve's period on its own basic unit. Equal track lengths are
  not a goal.
- **II. [Parity through accent choice](CONTEXT.md#governing-principle-ii-parity-through-accent-choice-2026-09-02-restated-2026-10-02).**
  Voices on different units end together at the *first* tick they can, and the accents
  are what earn that length: exactly the minimum, never a multiple.
- **III. [One weather](CONTEXT.md#governing-principle-iii-one-weather-2026-09-05).**
  One accent field covers every voice. It licenses the repetition parity needs, and
  nothing may repeat identically.
- **IV. [The accent span is the parity justification](CONTEXT.md#governing-principle-iv-the-accent-span-is-the-parity-justification-2026-09-05).**
  The accent that moves is exactly as long as parity requires, so every restatement of a
  rhythm sounds different.
- **VII. [The engine is general; only config is specific](CONTEXT.md#governing-principle-vii-the-engine-is-general-only-config-is-specific-2026-09-23-extended-2026-10-03).**
  Any sieve and any combination of basic units must work. Only `config.py` describes this
  composition.

## Repository structure

| Path | What it holds |
|---|---|
| [`sifters/dois_series/dois_47/`](sifters/dois_series/dois_47/) | **The current version**: 13 files a render, one four-track MIDI file, its wavetables, and a Serum preset per track. |
| [`sifters/dois_series/archive/`](sifters/dois_series/archive/) | Every earlier version, unchanged: Claude's `dois_01` to `dois_46` and ChatGPT's `dois_NN(gpt)`, plus `eight_five`, `pitch_studies` and `dois_44_studies`, the lab where the instrument was found. `dois_46` is the last with the pitch lattice, canon, form and tuning. |
| [`sifters/psappha/`](sifters/psappha/) | The Xenakis sieve on its own. |
| [`sifters/amen/`](sifters/amen/) | Amen break analysis: compression indices. |
| [`sifters/sixty/`](sifters/sixty/), [`third/`](sifters/third/), [`starbird/`](sifters/starbird/) | Earlier standalone pieces. |
| [`archive/`](archive/) | Superseded work. |
| [`CONTEXT.md`](CONTEXT.md) | The working reference: state, decisions, verification. |

Every version since `dois_21` has the same shape: `config.py` defines the voices,
`compose.py` runs the pipeline, `tests/` holds the test suite, and generated files land in
`mid/` (from `dois_45`, wavetables have a folder of their own, and from `dois_46` Serum
presets too). Recent versions split the rest into small modules, one per idea
(`sieve.py`, `accents.py`, `span.py`, `wavetable.py`, `serum.py`…). The earlier versions and the
standalone pieces use `composition.py` instead.

## Current work: `dois_47`

One 40-step beat, four voices, no arrangement layer. Every voice is **derived from a
single base sieve** rather than independently written, so the relationships between them
are exact by construction rather than by coincidence:

| Voice | Derivation | Basic unit | Static pitch |
|---|---|---|---|
| A | the psappha sieve itself | 16th note | 36 |
| B | complement of A | 16th note | 37 |
| C | A shifted by the lattice's diagonal, 8 + 5 = 13 steps — a rhythmic canon | 16th note | 38 |
| D | intersection of A and C — where they converge | **triplet 8th** | 39 |

A and B together fill all 40 steps with no gaps and no collisions, because they are
complements. D takes the steps where A and C coincide and replays them on its own triplet
grid, so in time it is the convergence re-timed: only 10 of its 60 notes land where A and
C are actually sounding together. D's triplet unit against the others' sixteenths gives a
4:3 polyrhythm.

**Accents: the weather.** Accents are not written; they are read off the sieve. Each
modulus the sieve uses contributes one accent, on the residues where the sieve's attacks
are densest. The field is the same for every voice (Principle III), and among equally
dense candidates it is chosen so that every voice meets every combination of accents.

**Velocity.** The accents sounding at a step form a combination, and one shared table maps
each combination to a velocity, rarer combinations higher. One combination means one
velocity in every voice. Velocity is a control signal, not just loudness: in Serum it
can pick a wavetable frame.

**Parity.** One statement of the rhythm is 40 steps: 40 × 120 = 4,800 ticks on
sixteenths, 40 × 160 = 6,400 on D's triplets. Parity is the first tick at which every
voice ends together, LCM(4800, 6400) = **19,200 ticks**, 40 quarter notes. To get there
A, B and C play their rhythm four times and D three, so one more accent, the **span
accent**, moves against the rhythm and makes each pass differ: A's four passes differ at
17–19 of its 27 attacks (Principles II and IV). Nothing is padded: a sieve that cannot
earn parity is refused, with the reason.

**Pitch.** Each voice sits on one note (A 36, B 37, C 38, D 39), so a track is one key;
the instrument, not the pitch, carries the sieve. The pitch lattice, a canon in pitch, a
40-step tuning and a 40-section form were built in `dois_15` to `dois_46` and are kept in
the archive; through the chosen instrument they could not be heard, so `dois_47` leaves
them out, and form is built in Ableton.

**Wavetables.** A velocity is a whole number, and a sieve is a rule about whole numbers.
So each voice gets a 128-frame Serum table built from its own sieve: frame *i* reads one
period of the sieve from *i* + 1 and sounds it from just above harmonic 13 × *i* mod 40.
That gives 40 different frames, each in its own register, and velocity picks the frame.

**The instrument.** Each voice is a Serum drum whose pitch is its attack rate, five
octaves up, whose decay is its median gap between attacks, and whose strike falls 13/40 of
an octave; a second oscillator plays the voice's complement as an FM modulator. Velocity
picks the frame, sets the level and opens the FM, so the accents are heard as timbre,
loudness and brightness at once.

**Output**, 13 files: one MIDI file with a track per voice, 8 wavetables (each voice's,
and its complement's), and 4 Serum presets, one per track.

**Change the sieve, or any voice's basic unit, and all of this recomputes**: rhythms,
weather, span accents, parity, meter, the tables and the drums (Principle VII).
`dois_36` rendered nine combinations of basic units, from every voice on one unit to 120
against 180, and the tests keep the three hardest.

**A setting that cannot work is refused before any file is replaced.** The refusal says
what is wrong and what to do about it, and a sieve that genuinely cannot work is refused
with the count that proves it. Renders are staged and only moved into place once every
file has been written and verified, so a failed run never reaches your files.

## Hearing it in Serum

The piece is written for Serum 2. `python3 compose.py --install-serum` installs the tables
and, in Serum's browser under **User → sifters → dois_47**, one preset per voice, named for
its track in the MIDI; nothing else needs setting. To build a patch of your own on the
tables instead, the steps are in the `dois_47` README: with pitch tracking off Serum plays
an oscillator at MIDI note 0, 8.18 Hz, so raise OCT to +4, and route VELO to the wavetable
position at 100%, where a velocity *v* lands exactly on frame *v*.

**To hear it rendered**, [`archive/dois_44_studies`](sifters/dois_series/archive/dois_44_studies/) has
four scripts. Their audio is not kept in git, so each one rebuilds its own:
- `studies.py` makes Python previews of the piece and of five studies, in about five
  seconds, with no synth needed.
- `serum_render.py` plays the same MIDI through Serum 2 itself, offline from Python.
- `percussion.py` builds a kit of four Serum drums derived from the voices' rhythms. With
  `--install` it puts them in Serum's browser under User → sifters → dois_44 studies kit.
  They use the tables
  from step 1.
- `fm_pairs.py` gives each of those drums a live FM modulator in Serum, the voice's own
  complement, at three ratios from the sieve's numbers, and saves them as presets under
  User → sifters → dois_44 studies FM pairs.

The last three need Serum 2 and a few extra Python packages, which the studies README
lists.

## Running it

```bash
cd sifters/dois_series/dois_47
python3 -m venv .venv && source .venv/bin/activate    # once; afterwards just activate
pip install -r requirements.txt          # the exact versions the files were made with
python3 compose.py                       # renders and then verifies every file
python3 compose.py --install-serum       # the same, then installs tables and presets in Serum
python3 compose.py --suggest-span        # searches accent residues, writes nothing
python3 -B -m unittest discover -s tests # the test suite
```

Requires `mido`, `music21` and `numpy`, with the exact versions pinned in the version
folder's `requirements.txt`, and Python 3.14. MIDI appears in `mid/`, wavetables in
`wavetables/` and Serum presets in `presets/`.
(`sifters/amen/compression_indices.py` also uses `matplotlib`.)

The first run after a reboot can take about a minute before printing anything. That is
macOS verifying numpy's compiled extensions on first load, not the script hanging.

## History and further reading

Every earlier version is in [`sifters/dois_series/archive/`](sifters/dois_series/archive/),
unchanged, and still runs from there. `dois_44`'s README ends with a "What `dois_NN`
changed" section for each version from `dois_31` on.

[`CONTEXT.md`](CONTEXT.md) is the working reference. It covers:
- what every version was for, including the detailed account of `dois_10` that used to be
  in this file;
- the reasoning behind each decision;
- the bugs found and their root causes;
- the verification methods that caught them.

Read it before changing any duration, meter or accent.
