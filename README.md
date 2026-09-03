# Sifters: A Data Synthesizer for Musical Composition

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
```

draws on moduli 8 and 5, so it closes after LCM(8,5) = **40 steps**. That 40-step period is the unit the whole project is built on.

## How a sieve becomes music

Two decisions turn a set of integers into sound, and both matter:

**The basic unit** — how much time one step occupies. Picture the sieve plotted on graph paper: the basic unit is the spacing between the lines, and the dots are the integers the sieve produced. Choosing a different unit for one voice against another is what creates polyrhythm.

**The duration** — a voice's total length must equal the *periodicity of its sieve*, normally the LCM of all its moduli. This is not a formatting detail. A clip that stops anywhere else misstates the sieve, and one padded out to match another voice's length states a convenience rather than a structure.

It follows that **voices are not all the same length, and should not be**. When two voices use different basic units, their durations differ — that is the polyrhythm being honest about itself.

## Repository structure

```
sifters/
  dois_series/     the main line of development, dois through dois_ten
  amen/            Amen break analysis — compression indices
  psappha/         the Xenakis sieve on its own
  sixty/  third/  starbird/    earlier standalone pieces
archive/           superseded work
CONTEXT.md         detailed working reference — state, decisions, verification
```

Most projects share the same shape: `config.py` defines the voices, `composition.py` runs the pipeline, `transformations.py` holds binary operations, and generated MIDI lands in `mid/`.

## Current work: `dois_ten`

A stripped-down, plugin-oriented version: one 40-step beat, four voices, no arrangement layer.

Every voice is **derived from a single base sieve** rather than independently written, so the relationships between them are exact by construction rather than by coincidence:

| Voice | Derivation | Basic unit | Pad |
|---|---|---|---|
| A | the psappha sieve itself | 16th note | 36 |
| B | complement of A | 16th note | 37 |
| C | A shifted 13 steps — a rhythmic canon | 16th note | 38 |
| D | intersection of A and C — where they converge | **triplet 8th** | 39 |

A and B together fill all 40 steps with no gaps and no collisions, because they are complements. D sounds only where A and C coincide. D's triplet unit against the others' sixteenths gives a 4:3 polyrhythm.

**Accents.** Four accent sieves overlay each voice. Velocity is the sum of the weights of the accents firing, and an accent's weight is derived from how *rarely* it fires — an accent covering two-thirds of the steps says little and lifts a note barely; a sparse one lifts it a lot.

Because an accent's modulus need not divide 40, the accent layer takes several passes of the rhythm to come back around: the same figure is re-accented on each pass, and a voice has not fully stated itself until rhythm and accents realign.

**Parity.** Accent moduli are chosen so that voices on *different* basic units still arrive at the same period — 480 steps × 120 ticks for the sixteenth voices, 360 × 160 for the triplet voice, both 57600 ticks. The step counts invert the unit ratio exactly. Parity is earned through the choice of sieve, never imposed by padding.

Output is six MIDI files: one per voice, a four-track arrangement, and a single-track version with all voices on Drum Rack pads 36–39. Each per-voice file is identical note-for-note to its track in the ensemble files, so it can be used to verify them.

## Running it

```bash
cd sifters/dois_series/dois_ten
python composition.py
```

Requires `mido`, `music21`, `numpy`. Output appears in `mid/`. (`sifters/amen/compression_indices.py` additionally uses `matplotlib`.)

The first run after a reboot can take about a minute before printing anything — that is macOS verifying numpy's compiled extensions on first load, not the script hanging.

## Further reading

`CONTEXT.md` is the working reference: current state, the reasoning behind each decision, the bugs found and their root causes, and the verification methods that caught them. Read it before changing any duration, meter or accent.
