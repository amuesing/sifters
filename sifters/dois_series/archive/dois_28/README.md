# dois_28

Forked from `dois_26(gpt)`, ChatGPT's readability refactor of dois_25, whose
structure this keeps and credits. What is new here: **the accents, and so the whole
velocity profile, are derived from the sieve** rather than written by hand. The sieve, rhythm, accents, velocities,
lattice formula, gate and parity are unchanged. Both pitch modes are exported.

## Start here

Read `config.py` first: it describes the composition. Then read `main()` near the
bottom of `compose.py`, which follows this order:

1. Evaluate the source sieve and derive each voice’s repeating rhythm.
2. Find parity: the first shared endpoint of those rhythms at their own step durations.
3. Build shared weather and each voice’s span accent; calculate the shared velocity table.
4. Check that the required rhythm restatements have distinct accent patterns.
5. Choose meters and validate every selected pitch mode before exporting.
6. Assign pitches, write MIDI, then independently verify the results.

## Where each idea lives

| File | Purpose |
|---|---|
| `config.py` | Your sieve, voice relationships, durations, accent choices and pitch settings. |
| `compose.py` | Coordinates the steps above. `--suggest-span` searches for accent residues without writing MIDI. |
| `sieve.py` | Evaluates sieves, measures actual periods and derives voice rhythms. |
| `transformations.py` | Complement, shift, intersection and the other available rhythm operations. |
| `accents.py` | Derives span moduli and turns accent combinations into velocities. |
| `pitch.py` | Static and lattice pitch rules, plus pitch validation. |
| `voice.py` | Names the calculated parts of a voice: `name`, `notes`, `velocities`, `step_ticks`, `accents`. |
| `midi.py` | Timing, meter and MIDI file writing/reading. |
| `check.py` | Verifies structure and exported events, including an independent velocity calculation. |

A **step** is one position on a voice’s grid. A **note layer** is that voice’s shortest
repeating rhythm. **Weather** is the shared accent field, sampled in local step
coordinates. The **span accent** distinguishes the restatements needed to reach parity.
A **velocity table** maps accent combinations to MIDI velocities; velocity can control
synth parameters, not just loudness. It is ONE table, shared by every voice, so an
accent combination means the same velocity throughout. The span residues are chosen so
that every voice uses every state its own rhythm can reach — a voice that lands on only
some weather combinations has a lower ceiling, and is held to that. How OFTEN each state
sounds is deliberately uneven: rare accent combinations are rare events.

The settings stay separate from calculated results. Preparing accents does not add
keys to `config.INSTRUMENT_CONFIGS`. `Voice` holds the data used to render and verify a
pitch mode. Named fields replace positional voice tuples.

## The lattice

For the current 8 × 5 sieve:

```text
pitch = root + (5 × (step mod 8) + 8 × (step mod 5)) mod 40
      = root + (13 × step) mod 40
```

The renderer uses the first formula. The verifier uses the second. This deliberate
independence is retained to catch implementation mistakes. The mapping is invertible
modulo 40 and preserves residue classes modulo 8 and 5. The canon is +9 modulo 40:
23 notes rise 9 semitones and four fall 31 in one note layer. It is not octave-equivalent
transposition modulo 12.

Lattice mode requires exactly two coprime source moduli, their product as every voice’s
note-layer period, and a range that fits MIDI. Static mode does not require that lattice.
Changing the sieve still derives periods, parity, span moduli and default lattice
intervals. Weather and span residues are DERIVED by default (`WEATHER = None`,
`SPAN_RESIDUE_SOURCE = None`); naming either explicitly still works.

## Run and use

With Python, numpy, music21 and mido installed:

```sh
python3 compose.py
python3 compose.py --suggest-span
python3 -B -m unittest discover -s tests -v
```

Exports go into **this folder’s `mid/`**, regardless of the directory you run from:

- `dois_28_static_*`: fixed pitches A=36, B=37, C=38, D=39.
- `dois_28_lattice_*`: pitches derived from the sieve’s lattice.

Each mode has four `_prime` voice files, a four-track `_arrangement`, and a single-track
`_ensemble` with voices on separate MIDI channels. The prime files are convenient for
routing voices separately in a DAW.

With the current settings, each file ends at 19,200 ticks: 40 quarter notes, or 20 seconds
at 120 BPM. The declared meter is 40/16. Voice note counts are 108, 52, 108 and 60.
Gate remains 1.0; audition articulation on the intended instrument.

## What changed and why

- Removed `velocity_profile()`: its per-voice rarity values were unused. Velocities now
  receive the accent masks and shared table directly.
- Stopped adding derived accents to the original composition settings.
- Replaced positional voice tuples with the small `Voice` data class.
- Qualified settings as `config.NAME`, making their source visible.
- Removed unused imports and an unused return value.
- Shortened long historical docstrings and config commentary. The original explanations
  are preserved in `DESIGN_HISTORY.md`; they are historical context, not current API docs.

The musical checks remain. New output filenames and provenance fingerprints differ,
but musical note events must match dois_25. The fingerprint covers source code too,
so a MIDI byte difference can reflect a comment change rather than changed music.

Exports are still written directly: pitch preflight protects against invalid pitch
settings, but a disk failure can interrupt replacement. Atomic export is a separate
future improvement, outside this readability refactor.
