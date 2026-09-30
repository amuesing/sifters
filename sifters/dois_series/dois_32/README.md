# dois_32

The current version. Everything musical is derived from the sieve in `config.py` — the
rhythms, the accent field the velocities are built from, the parity point, the meter and
the pitch lattice. Change the sieve and all of it recomputes. Both pitch modes are
exported from one rhythm.

It is `dois_30` with four corrections, none of them musical. **Every note, velocity,
gate and pitch of the twelve exports is identical to `dois_30`**, asserted from the files
by `tests/test_preflight.py`. What changed is what happens when something is wrong:
`dois_31` fixed three defects ChatGPT found in `dois_30(gpt)`, and `dois_32` separated
three failures that had been sharing one message. See "When a setting is wrong" and
"When a sieve cannot work" below.

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

- `dois_32_static_*`: fixed pitches A=36, B=37, C=38, D=39.
- `dois_32_lattice_*`: pitches derived from the sieve’s lattice.

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
| a sieve whose voices cannot have distinct passes | refused with the count that proves it — see below. |
| a pitch mode that cannot render for this sieve | refused before any mode writes. |

The weather check measures the expression's TRUE period rather than trusting its
modulus, so `7@0|7@1|7@2|7@3|7@4|7@5|7@6` — which calls itself mod 7 and is actually
constant — is correctly allowed.

`tests/test_preflight.py` renders twelve real files, then breaks the config, and requires
every byte of the twelve to survive.

## When a sieve cannot work

Three different things can stop a run, and until `dois_32` they printed the same
sentence — one that told you to change your sieve even when the sieve was fine:

**1. First convergence** is arithmetic. It always exists: it is the LCM of each voice's
raw period, and nothing chooses it.

**2. Accent capacity** is a count, and when it fails it is a PROOF. A voice restates its
note layer to reach parity. The weather is static, so it marks the same attacks the same
way on every pass; only the span accent varies, and it is one binary accent. So a voice
with k attacks in its layer has at most **2^k** distinguishable passes, whatever residues
are used. The sparse 12-step sieve `(4@0|4@1)&3@1|4@2` fails here and is refused with its
own arithmetic:

```
D: 1 attack(s) in a 12-step layer, restated 3x to reach parity,
   but at most 2**1 = 2 different passes are possible — 3 > 2
```

The bound is necessary, not sufficient: being inside it does not make a set reachable.
Only the failure direction proves anything. (ChatGPT's proof, 2026-09-30.)

**3. The search and its selection rules** prove nothing about the sieve. If no candidate
made every pass distinct, the run says the bounded search failed — sets of up to four
residues below 16, at these basic units, with this weather — and that a wider search or
another accent design may still succeed. And if a set DID satisfy Principle IV but none
reached every voice's state ceiling, the run says so, names the working set, and calls
the ceiling what it is: a selection rule chosen in `dois_28`, not a principle.

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

## What dois_32 changed

ChatGPT's note of 2026-09-30 asked that first convergence, accent capacity, and
search/selection failure stop being reported as one thing. They now are three, above.
The capacity count replaces a refusal that said "no residues found" — which cannot
distinguish a sieve that cannot work from a search that gave up — with one that proves
the case when it is provable and claims nothing when it is not. No music changed.

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
