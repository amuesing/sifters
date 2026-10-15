# dois_31

The current version. Everything musical is derived from the sieve in `config.py` — the
rhythms, the accent field the velocities are built from, the parity point, the meter and
the pitch lattice. Change the sieve and all of it recomputes. Both pitch modes are
exported from one rhythm.

It is `dois_30` with three defects fixed — all three found by ChatGPT in
`dois_30(gpt)`, and none of them musical. **Every note, velocity, gate and pitch of the
twelve exports is identical to `dois_30`**, asserted from the files by
`tests/test_preflight.py`. What changed is what happens when a setting is wrong; see
"When a setting is wrong" below.

Its structure is ChatGPT's, adopted from `dois_26(gpt)` and credited: small modules,
qualified `config.NAME` settings, a named `Voice`, and no mutation of the composition
settings. The long historical commentary lives in `../dois_26(gpt)/DESIGN_HISTORY.md`
and in `CONTEXT.md` at the repo root, not in the code.

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

- `dois_31_static_*`: fixed pitches A=36, B=37, C=38, D=39.
- `dois_31_lattice_*`: pitches derived from the sieve’s lattice.

Each mode has four `_prime` voice files, a four-track `_arrangement`, and a single-track
`_ensemble` with voices on separate MIDI channels. The prime files are convenient for
routing voices separately in a DAW.

With the current settings, each file ends at 19,200 ticks: 40 quarter notes, or 20 seconds
at 120 BPM. The declared meter is 40/16. Voice note counts are 108, 52, 108 and 60.
Gate remains 1.0; audition articulation on the intended instrument.

## What is derived, and what you still choose

Derived from the sieve, for any sieve:

- each voice's rhythm and the period it actually closes on;
- **the weather** — one accent per modulus the sieve uses, firing on the residues that
  sieve favours (count the attacks on each residue, keep the densest half);
- **the span accent's modulus** — forced by the parity arithmetic: the smallest M where
  `lcm(layer, M)` equals the steps that voice needs to reach parity. Voices with longer
  basic units need fewer steps and so get smaller moduli;
- **the span accent's residues** — searched, keeping the set that puts every voice at
  its ceiling and then makes the passes differ most;
- the parity point, the meter, and the lattice's axes and intervals.

Still yours: the sieve, how the voices relate (complement, shift, intersection), the
basic units, tempo, root note, gate and velocity range. Naming `WEATHER` or
`SPAN_RESIDUE_SOURCE` explicitly in `config.py` overrides the derivation and is checked
the same way.

## When a setting is wrong

Everything here is checked BEFORE a single file is replaced, so a refusal leaves the
twelve renders you already have untouched:

| What you set | What happens |
|---|---|
| a `WEATHER` accent whose period does not divide the note layer | refused, naming the accent, its measured period and the layers it fights. Such an accent is a span accent, not weather: in `dois_30` a `7@0` accent replaced all twelve files with 134400-tick renders — seven times parity — and only then failed verification. |
| `SPAN_RESIDUE_SOURCE` residues that leave two passes of a voice identical | refused, naming the voice and the pass pair, and pointing at `--suggest-span`. In `dois_30` this path raised `NameError`: it called a function that had been deleted. |
| a sieve whose span accent cannot inflect every pass | refused with the reason — a real limit of the material. |
| a pitch mode that cannot render for this sieve | refused before any mode writes. |

The weather check measures the expression's TRUE period rather than trusting its
modulus, so `7@0|7@1|7@2|7@3|7@4|7@5|7@6` — which calls itself mod 7 and is actually
constant — is correctly allowed.

`tests/test_preflight.py` renders twelve real files, then breaks the config, and requires
every byte of the twelve to survive.

## Known limits

- Exports are written directly. Bad SETTINGS can no longer replace them — that is what
  dois_31 added — but an interruption or a disk failure partway through a write still
  can. Atomic export is not implemented.
- The span residues are found by search, not counted off the sieve. They cannot be
  counted: the sieve's density at the span modulus is necessarily periodic with
  `gcd(layer, modulus)` — 8 here, not 32 — so counting can never produce a set that
  spans the modulus. The span accent has to be independent of the note layer, and that
  independence is what makes it move across the passes.
- A sieve too sparse for its span accent to inflect every pass is refused, with the
  reason. That is a real limit of the material, not a bug.
- No listening judgment is claimed anywhere. Every check here is structural.

## What dois_31 changed

Three defects, all found by ChatGPT in `dois_30(gpt)` and reproduced here before being
fixed. Its `require_static_weather` and `require_first_parity` are adopted with the
reasoning kept in their docstrings.

1. **A weather named in config skipped the static check.** `derive_weather` enforces it
   for the weather it derives; `config.WEATHER or derive_weather(...)` meant an explicit
   one went straight past. Now checked for both, against every voice's note layer.
2. **The refusal for duplicate passes could not run.** It called `search_residue_source`,
   deleted earlier in `dois_30`, with a name that was not in scope, and formatted
   `tuple(None)`. Three errors in one branch, in code whose only job is to explain.
3. **The test helper's overrides silently did nothing.** Its patterns matched
   `WEATHER = {...}` and `SPAN_RESIDUE_SOURCE = (...)`, but both have defaulted to
   `None` since `dois_27`. `re.sub` returns its input unchanged when nothing matches, so
   every test that asked for an explicit weather quietly re-ran the default config — which
   is why (1) and (2) were never seen. `project_copy` now reads each setting back out of
   the written file and raises if it did not land, and a test proves the helper fails
   when an override stops matching.

`require_first_parity` is adopted too, though with a static weather and a derived span
modulus I could not construct a config that reaches it. It guards a future change to
that derivation rather than a reachable error today; its docstring says so.
