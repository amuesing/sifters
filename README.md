# Sifters: A Data Synthesizer for Musical Composition

> **Current version: `dois_38`** — `sifters/dois_series/dois_38/`, with its own README.
> Everything musical is derived from the sieve you put in `config.py`: the rhythms, the
> accent field the velocities are built from, the parity point, the meter, and the pitch
> lattice. Change the sieve and all of it recomputes. Two pitch modes are rendered from
> one rhythm — `static` (one fixed note per voice, for hardware that cannot take pitch as
> a CV source) and `lattice` (pitch read off the sieve's own grid).
>
> **Two parallel lines share the numbering.** Bare `dois_NN` are Claude's; `dois_NN(gpt)`
> are ChatGPT's, most recently `dois_30(gpt)`. The numbers do not correspond between
> them, and each line's work is committed separately.

Sifters is a data-driven system for developing musical compositions, using logical sieves as the foundation for creative exploration. The core idea behind Sifters is to synthesize data that generates musical forms, all derived from a single logical source. This approach draws inspiration from Iannis Xenakis’ analysis of Psappha (1975), where logical sieves are used to determine rhythmic and structural elements. In this system, the sieve functions similarly to an oscillator in an analog synthesizer, guiding the generation of musical material.

The commit history in this repository chronicles my ongoing exploration of logic-based operations applied to musical composition within the Python programming environment. Each sub-directory within `sifters/` corresponds to a unique track intended to be realized through Ableton.

## What a sieve is

A sieve is a set of integers described by modular congruences, combined with boolean logic:

```
5@0            every n where n mod 5 == 0
8@1|8@7        union — n mod 8 is 1 or 7
(8@0|8@1)&5@0  intersection
1 - binary     complement
```

`music21.sieve.Sieve` evaluates these into a binary array. **Where a number occurs, a sound occurs.** The psappha sieve used throughout this project,

```
(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))
|8@3|8@4|(8@1&5@2)|(8@6&5@1)
```

draws on moduli 8 and 5, so it closes after LCM(8,5) = **40 steps**. That 40-step period is the unit the whole project is built on.

The four terms on the second line are a correction made in `dois_14`: earlier versions of this repository used the first line alone, which is the expression printed in the *Frontiers in Psychology* article on Psappha. That article contradicts itself — the expression it prints gives 15 attacks in 40 steps while its own prose claims 27. The reading here matches the open-access copy (PMC7849451), and gives 27. `CONTEXT.md` records the check.

## How a sieve becomes music

Two decisions turn a set of integers into sound, and both matter:

**The basic unit** — how much time one step occupies. Picture the sieve plotted on graph paper: the basic unit is the spacing between the lines, and the dots are the integers the sieve produced. Choosing a different unit for one voice against another is what creates polyrhythm.

**The duration** — a voice's total length must equal the *periodicity of its sieve*, normally the LCM of all its moduli. This is not a formatting detail. A clip that stops anywhere else misstates the sieve, and one padded out to match another voice's length states a convenience rather than a structure.

It follows that **voices are not all the same length, and should not be**. When two voices use different basic units, their durations differ — that is the polyrhythm being honest about itself.

## Repository structure

```
sifters/
  dois_series/     the main line of development, dois_01 through dois_38,
                   interleaved with ChatGPT's dois_NN(gpt) folders
  amen/            Amen break analysis — compression indices
  psappha/         the Xenakis sieve on its own
  sixty/  third/  starbird/    earlier standalone pieces
archive/           superseded work
CONTEXT.md         detailed working reference — state, decisions, verification
```

Most projects share the same shape: `config.py` defines the voices, `composition.py` runs the pipeline, `transformations.py` holds binary operations, and generated MIDI lands in `mid/`.

## Current work: `dois_38`

One 40-step beat, four voices, no arrangement layer. Every voice is **derived from a
single base sieve** rather than independently written, so the relationships between them
are exact by construction rather than by coincidence:

| Voice | Derivation | Basic unit | Static pitch |
|---|---|---|---|
| A | the psappha sieve itself | 16th note | 36 |
| B | complement of A | 16th note | 37 |
| C | A shifted 13 steps — a rhythmic canon | 16th note | 38 |
| D | intersection of A and C — where they converge | **triplet 8th** | 39 |

A and B together fill all 40 steps with no gaps and no collisions, because they are
complements. D sounds only where A and C coincide. D's triplet unit against the others'
sixteenths gives a 4:3 polyrhythm.

**Accents.** Accents are not written; they are read off the sieve. Each modulus the sieve
uses contributes one accent firing on the residues that sieve *favours* — count the
attacks landing on each residue of that modulus and keep the densest half. This field is
the same for every voice (that is what makes a shared velocity meaningful), so it is
called the **weather**. One further requirement decides between equally favoured
candidates: every voice's attacks must meet every on/off combination of these accents,
so that the whole velocity vocabulary can sound in every voice.

**Velocity.** The combination of accents sounding at a step is a bitmask, and one shared
table maps each combination to a velocity, ranked by how rare the combination is: a
common one lifts a note barely, a rare one a lot. Because the table is shared, one
combination means the same velocity in every voice. How often each level occurs is
deliberately uneven — rare events should be rare. Velocity here is a control signal, not
just loudness; on a synthesizer it can be routed to filter or envelope rather than volume.

**Parity.** A voice's rhythm closes at its own period, and voices on different basic
units close at different times. Parity is the moment they all **end at the exact same
time**, and it is the *first* such moment — LCM(4800, 6400) = **19,200 ticks** here, 40
quarter notes, with nothing shorter possible. The accents must reach exactly that and no
multiple of it: reaching parity means some voices restate their rhythm several times, so a
further accent, the **span accent**, is given the *smallest* modulus that does not divide
the rhythm but still lands on parity, and its residues are searched for the set that makes
those restatements differ as much as the sieve allows. Nothing is padded: parity is earned
by the choice of sieve, and refused with an explanation when the material cannot earn it.

**Pitch.** Two modes render from the same rhythm and velocities. `static` gives each voice
one fixed note, for hardware that cannot take pitch as a CV source — a Moog Grandmother is
the intended instrument. `lattice` reads pitch off the sieve's own grid: because 8 and 5
are coprime, every step has a unique address `(n mod 8, n mod 5)`, and
`root + (5·(n mod 8) + 8·(n mod 5)) mod 40` turns that address into a pitch.

**Serum wavetables.** Alongside the MIDI, each voice gets two Serum 2 wavetables. In
each frame, harmonic h sounds if h is in the voice's sieve, for exactly one period of it
— 40 harmonics, the sieve's own periodicity — coloured by the accent sieves firing in
that state. The velocity table holds one frame per MIDI velocity: route velocity to
wavetable position and each note's accents choose its timbre. The sweep table follows
the voice through its whole parity cycle, step by step.

Output is twelve MIDI files, six per pitch mode, plus eight wavetables: one per voice, a four-track arrangement,
and a single-track ensemble. Each per-voice file is identical note-for-note to its track
in the ensemble files, so it can be used to verify them.

**Change the sieve, or any voice's basic unit, and all of this recomputes** — rhythms,
weather, span moduli and residues, parity, meter and the lattice axes. Nine combinations
of base durations are verified to render, from every voice on one unit to 120 against
180. Nothing above is written into the code; only
`config.py` describes this particular composition.

**A setting that cannot work refuses the run before any file is replaced**, naming what
is wrong and what to do about it, so your existing renders survive (`dois_31`, on three
defects ChatGPT found in `dois_30`). And a sieve that genuinely cannot work is refused
with the count that proves it, kept separate from a search that merely found nothing
(`dois_32`). Renders are staged and only moved into `mid/` once every mode has been
written and verified, so nothing that goes wrong reaches your files (`dois_33`).

## Running it

```bash
cd sifters/dois_series/dois_38
python3 compose.py                      # renders and then verifies every file
python3 compose.py --suggest-span       # searches accent residues, writes nothing
python3 -B -m unittest discover -s tests
```

Requires `mido`, `music21`, `numpy` — the exact versions are pinned in the version
folder's `requirements.txt`. Output appears in `mid/`.
(`sifters/amen/compression_indices.py` additionally uses `matplotlib`.)

The first run after a reboot can take about a minute before printing anything — that is
macOS verifying numpy's compiled extensions on first load, not the script hanging.

## Earlier versions

Every `dois_NN` folder still runs, and `CONTEXT.md` describes what each one was for. The
detailed account of `dois_10` that used to be in this file is there, under its own
heading, along with the reasoning that led from it to `dois_38`.

## Further reading

`CONTEXT.md` is the working reference: current state, the reasoning behind each decision, the bugs found and their root causes, and the verification methods that caught them. Read it before changing any duration, meter or accent.
