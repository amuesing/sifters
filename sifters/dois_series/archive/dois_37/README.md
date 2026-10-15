# dois_37

The current version. Everything musical is derived from the sieve in `config.py` — the
rhythms, the accent field the velocities are built from, the parity point, the meter and
the pitch lattice. Change the sieve, or any voice's basic unit, and all of it
recomputes. Both pitch modes are exported from one rhythm.

**`dois_37` adds Serum wavetables** — one per voice, one frame per accent state, in the
same order as the velocity table. Route velocity to wavetable position in Serum and the
accents choose the TIMBRE instead of the loudness. The MIDI is unchanged. See "Serum
wavetables" below.

**`dois_36` made the engine work for any combination of base durations**, not only
the sixteenths-against-triplet of this piece. Nine combinations were rendered: before
it, three were refused and one would have taken three hours; now all nine render with
every voice sounding all eight velocities. **This piece's twelve files are note-for-note
and velocity-for-velocity identical to `dois_35`** — every change here only matters for
other durations. See "What dois_36 changed".

It is `dois_30` with five corrections and two deliberate musical changes. **No note has moved since `dois_30`** — every
onset, duration, pitch and channel is identical, asserted field by field from the files.
`dois_34` moved 124 of the 656 velocities by widening the residue search, and `dois_35`
moved 83 more by requiring that every voice can sound every velocity. Both moved only
velocities. The rest was housekeeping: `dois_31` fixed three
defects ChatGPT found in `dois_30(gpt)`, `dois_32` separated three failures that had been
sharing one message, and `dois_33` made sure nothing that goes wrong can reach `mid/` at
all. See "When a setting is wrong", "When a sieve cannot work" and "Where the files go".

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

- `dois_37_static_*`: fixed pitches A=36, B=37, C=38, D=39.
- `dois_37_lattice_*`: pitches derived from the sieve’s lattice.

Each mode has four `_prime` voice files, a four-track `_arrangement`, and a single-track
`_ensemble` with voices on separate MIDI channels. The prime files are convenient for
routing voices separately in a DAW.

With the current settings, each file ends at 19,200 ticks: 40 quarter notes, or 20 seconds
at 120 BPM. The declared meter is 40/16. Voice note counts are 108, 52, 108 and 60.
Gate remains 1.0; audition articulation on the intended instrument.

## Serum wavetables

Four files land in `mid/` beside the MIDI: `dois_37_wavetable_A.wav` through `_D.wav`.
Each holds **8 frames of 2048 samples** — one single cycle per accent state — as 24-bit
mono WAV with Serum's frame-size marker.

**Setting it up in Serum:**

1. Drag `dois_37_wavetable_A.wav` onto an oscillator's wavetable display.
2. In the mod matrix, route **Velocity → that oscillator's WT Pos**, amount 100%, with
   the wavetable position knob at its start.
3. Play `dois_37_static_A_prime.mid` (or the `lattice` file — Serum takes pitch from MIDI,
   which the Grandmother could not) into that instance.

Each note's velocity then selects its frame. The eight velocities are spaced evenly from
1 to 127, and the eight frames are spaced evenly across the table, so velocity level k
lands on frame k. (Serum reads velocity as v/127, so the lowest level sits about 5% of a
frame past frame 0 — close enough not to matter, but not exact.)

**How each frame is built**, for one voice and one accent state:

- **its spectrum is the voice's own rhythm.** Step n of the note layer sets harmonic
  n+1: a rest is a missing partial, and the layer's period (40 here) is the number of
  harmonics. A and B are complements, so their timbres are too — between them every
  harmonic sounds exactly once. The fundamental always sounds, because the pitch comes
  from the MIDI and a rhythm resting on step 0 would otherwise make it ambiguous;
- partials fall off as 1/h, like a sawtooth;
- **each accent firing in that state lifts the harmonics whose steps it marks**, in
  proportion to its rarity — the same rarity that ranks the velocity table. So a rarer
  state, with more and rarer accents firing, is more strongly coloured;
- each frame is normalised on its own, so frames differ in colour, not level.

**One thing to know before you listen:** the frames do NOT run dark to bright as
velocity rises. An accent lifts the harmonics its own residues mark, and those can be
low ones, so brightness goes up and down across the table — on A, frame 3 is the darkest.
Rarer means more coloured, not brighter. If you want a dark-to-bright sweep instead,
that is a different design, and an easy change.

`WAVETABLE_EMPHASIS` in `config.py` sets how strongly an accent colours its harmonics.
It is a choice, not derived: at 0 every frame is the plain rhythm and identical.

**Checked from the files.** Every frame of every wavetable is read back with Python's
own `wave` module (not the writer's parser), measured with an FFT, and compared with a
spectrum rebuilt from config, in the order of the independently rebuilt velocity table.
Two tests deliberately break a wavetable — two states swapped, one state lost — and
require the run to refuse with nothing reaching `mid/`. macOS's `afinfo` reads the files
as valid 24-bit WAV.

**What I could not check:** that Serum itself accepts the frame-size marker. Serum
recognises a chunk beginning `<!>2048`; the eight characters of flags after it are
written as zeros because I do not know what they mean. If Serum asks how to import the
file, choose 2048-sample frames and it will cut it correctly either way.

## What is derived, and what you still choose

Derived from the sieve, for any sieve:

- each voice's rhythm and the period it actually closes on;
- **the weather** — one accent per modulus the sieve uses, firing on the residues that
  sieve favours (count the attacks on each residue, keep the densest half) AND chosen so
  that every voice's attacks meet every on/off combination of those accents, which is
  what lets the whole velocity profile sound in every voice. Where the two pull against
  each other the requirement wins and the densest candidate satisfying it is taken; on
  psappha that costs one attack of density in the mod-8 accent and nothing in mod-5;
- **the span accent's modulus** — forced by the parity arithmetic: the SMALLEST M where
  `lcm(layer, M)` equals the steps that voice needs to reach parity. Smallest matters: a
  larger modulus would also reach parity, and overshoot on the way. Voices with longer
  basic units need fewer steps and so get smaller moduli. One exception: a voice that
  reaches parity in a SINGLE pass would get modulus 1, an accent that never switches, so
  it takes its own layer as the modulus instead — still ending after exactly one pass;
- **the span accent's residues** — searched, keeping the set that puts every voice at
  its ceiling and then makes the passes differ most. The search range is the span
  accent's own modulus, since `span_accent` discards anything at or above it. Set sizes
  run to five, which is a choice: the search has to stop somewhere, and five is where
  measuring said the returns were. `config.py` pins the answer for this sieve so a
  render does not repeat a 37-second search; `tests/test_derivation.py` fails if the
  search stops agreeing with the pinned value. When trying every set would take more
  than 300,000 tries, a step-by-step search runs instead and says so — see below;
- the parity point, the meter, and the lattice's axes and intervals.

Still yours: the sieve, how the voices relate (complement, shift, intersection), the
basic units — any combination of them — tempo, root note, gate and velocity range. Naming `WEATHER` or
`SPAN_RESIDUE_SOURCE` explicitly in `config.py` overrides the derivation and is checked
the same way.

## Parity is a minimum, not a target

Parity means voices of different basic units **end at the exact same time**, and the
accents must get them there at the **earliest moment that is possible** — not a multiple
of it. For this sieve:

```
A, B, C   40 steps x 120 ticks = 4,800
D         40 steps x 160 ticks = 6,400
                          LCM  = 19,200 ticks   <- nothing shorter works
```

Three things have to hold for that to mean anything, and `tests/test_requirements.py`
asserts each one from the project itself rather than trusting the arithmetic:

1. **the parity point is minimal** — checked by brute force over every tick count below
   it, because an LCM is only minimal if it really is an LCM;
2. **each accent profile is exactly that long** — A/B/C 160 steps, D 120 steps, all four
   19,200 ticks. Not 38,400, not any other multiple;
3. **each span accent uses the smallest modulus that reaches it** — no modulus below 32
   gets A/B/C there, none below 3 gets D there.

A fourth test covers the way this could be broken from the other side: a weather accent
whose period did not divide the note layer would extend the profile past parity. That is
what `require_static_weather` refuses, and the test states the requirement positively.

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

## Where the files go

Renders are written into a **staging folder** beside `mid/`, and they only move into
`mid/` once every pitch mode has been written AND verified. Before `dois_33` each mode
was written straight into `mid/` and checked afterwards, so a mode that failed
verification had already replaced your files by the time you were told, and a crash
between the two modes left six new files beside six old ones.

The staging folder is a sibling of `mid/`, so it is on the same filesystem and the move
is a rename rather than a copy. `os.replace` is atomic per file: a reader sees the old
file or the new one, never a half-written one. The twelve are not swapped as one
transaction — that would need a directory swap, which would take the other files in
`mid/` with it — but every byte is written and verified before the first replace, so what
remains is a handful of directory operations with no work between them. A failure at any
earlier point leaves `mid/` exactly as it was, and the staging folder is removed either
way.

Files in `mid/` that this run did not produce are never touched, and are reported.

## Known limits

- The span residues are found by search, not counted off the sieve. They cannot be
  counted: the sieve's density at the span modulus is necessarily periodic with
  `gcd(layer, modulus)` — 8 here, not 32 — so counting can never produce a set that
  spans the modulus. The span accent has to be independent of the note layer, and that
  independence is what makes it move across the passes.
- The exhaustive search stops at five residues. Four was measured as too few (it cost
  two steps of pass difference); six and beyond have not been measured, and each size
  multiplies the work. `largest` is no longer arbitrary — it is the span accent's own
  modulus — but `most` still is.
- **Above 300,000 candidates the search is local, and may miss the best set.** It
  improves one set a step at a time and stops when no single change helps. It says so
  when it runs, and its results can be weaker: for 120 against 180 the closest passes
  differ at only 2 steps, against 6 for this piece. It is deterministic, so the same
  settings always give the same answer.
- A sieve too sparse for its span accent to inflect every pass is refused, with the
  reason. That is a real limit of the material, not a bug.
- A sieve may exist for which NO weather lets every voice sound every velocity. The run
  is then REFUSED, naming the voices that fall short. Until `dois_36` it printed a
  warning and used the densest weather anyway — and nothing downstream would have
  noticed. For moduli too large to search fully, the weather search keeps only each
  modulus's densest choices and says the refusal is not a proof.
- **No listening judgment is claimed anywhere. Every check here is structural, and no
  version of this piece has been auditioned on the instrument it is written for.**

## What dois_37 changed

Serum wavetables, above — `wavetable.py`, `check.check_wavetables`, three settings in
`config.py`, and `tests/test_wavetables.py`. They are staged and verified with the MIDI
and committed with it, so a wavetable that fails its check never reaches `mid/`.
Nothing about the MIDI changed: its note events are still identical to `dois_35`'s.
66 tests.

## What dois_36 changed

The author's rule: *"I want the code to be useful for any given sieve, or combination of
base durations."* Every sieve tested until now used the same units — three voices on
sixteenths, one on a triplet eighth — so the second half had never been tried. Nine
combinations, rendered through the real pipeline:

| units (A, B, C, D) | passes per voice | before `dois_36` | now |
|---|---|---|---|
| 120, 120, 120, 160 — this piece | 4, 4, 4, 3 | renders | renders, unchanged |
| 120, 120, 120, 120 | 1, 1, 1, 1 | **refused** | 8/8 every voice |
| 120, 120, 120, 240 | 2, 2, 2, 1 | **refused** | 8/8 every voice |
| 120, 120, 120, 80 | 2, 2, 2, 3 | renders | 8/8 every voice |
| 120, 120, 160, 160 | 4, 4, 3, 3 | renders | 8/8 every voice |
| 240, 120, 120, 160 | 2, 4, 4, 3 | renders | 8/8 every voice |
| 160, 160, 160, 120 | 3, 3, 3, 4 | renders | 8/8 every voice |
| 480, 120, 120, 160 | 1, 4, 4, 3 | **refused** | 8/8 every voice |
| 120, 120, 180, 160 | 12, 12, 8, 9 | **~3 hours** | 8/8 every voice, in a second |

Five things had to change, each with its own test in `tests/test_any_durations.py`.

**1. A voice that reaches parity in one pass.** Its span accent got modulus 1 — firing
on every step, never off — so half the velocity profile was out of reach. It now takes
its own layer as the modulus, which still ends it after exactly one pass. Not its
smallest factor: a 2-step accent was measured and left those voices at 7 of 8, because
whether a step is even is already fixed by the 8-step weather cycle.

**2. A bug in the checker, not the music.** It measured a file's length from where its
last note ended, so a single-pass voice finishing on a rest came back one step short and
failed on correct music. With several passes, later passes had always restored the
length, which is why it never showed. It now reads where the file actually ends.

**3. Ceilings that promised the impossible.** A voice's ceiling was "twice the weather
combinations it meets", which assumes every attack recurs. Over several passes it does,
and the span accent can mark it on one pass and not the next. In one pass an attack
happens once — on or off, not both. With every voice on the same unit, B met the
both-accents combination at exactly one attack: its real maximum was 7 while the count
promised 8. Ceilings, and the weather's requirement, now count how often each
combination OCCURS across all passes. On this piece every voice repeats, so nothing
changes here.

**4. Searches too large to run.** 120 against 180 puts parity at 57,600 ticks and asks
for 64.6 million candidate sets. Above 300,000 a local search runs instead — start from
the best single residue, take whichever one change helps most, stop when none does —
and says plainly that it may have missed the best. 120/180 now renders in about a
second.

**5. No more silent fallback** (from ChatGPT's review, 2026-10-05). If no weather can give
every voice the whole profile, the run is refused rather than rendered short.

Also from that review: the pitch lattice and the weather now read the sieve's moduli
through **one** function, cross-checked against music21's own parse of the expression.

58 tests. The current piece is note-for-note and velocity-for-velocity unchanged; only
its title and provenance stamp differ.

## What dois_35 changed

**Three requirements, stated by the author, now asserted from the rendered files** in
`tests/test_requirements.py`:

1. every repeat of every voice has a unique velocity pattern, even though its rhythm and
   its pitches repeat exactly — with a companion test confirming the rhythm really does
   repeat underneath, so requirement 1 cannot be satisfied by accident;
2. the entire velocity profile is expressed: all eight levels, **in every voice**;
3. the accent profile lasts exactly as long as that voice needs to reach parity — and
   the test checks it does not close sooner either, which would mean the accents repeat
   inside the parity span.

1 and 3 already held, from `dois_27` and `dois_32`. **2 did not, and could not.** The
weather was chosen one modulus at a time, each taking the residues that modulus favours.
That is blind to what the COMBINATION does to each voice: B never had a single attack
where the mod-8 and mod-5 accents fired together, so two of the eight velocities could
never sound in it however the span accent was set. Its ceiling was 6, not 8.

Choosing the weather is now a search with that requirement in it — the same shape the
span residues already used. Of the 700 densest-half candidates on psappha, **642** let
every voice meet every combination, so the requirement is barely a constraint; the blind
rule simply happened to land on one of the 58 that fail. The densest candidate that
satisfies it is `mod8 = 8@1|8@3|8@4|8@5`, `mod5 = 5@1|5@3` — one attack less dense than
the blind choice, mod5 unchanged, and every voice now reaches 8 of 8. The span residues
and the pass-difference score are untouched: still `(0, 9, 10, 21, 31)`, still 6.

It generalises. The 7x5 and 11x3 sieves also reach 8/8 in every voice under the new rule,
where 7x5 previously left B and D short.

Ranking matters, and I got it wrong first. Scoring each modulus separately and taking
them in order is not the same as ranking whole weathers by total density; the lazy
version picked an equally dense weather that cost a step of pass difference. `favour()`
in `accents.py` records that.

83 of the 656 velocities moved. No note moved.

## What dois_34 changed

**The search bounds were mine, so I measured them.** On the psappha sieve:

| bound | candidates | best weakest-pass-difference | time |
|---|---|---|---|
| up to 4 residues below 16 — `dois_30` to `dois_33` | 2,516 | 4 | 1.5s |
| up to 4 residues below 32 | 41,448 | **4**, the same set | 23s |
| up to 5 residues below 32 | 242,824 | **6**, at (0, 9, 10, 21, 31) | 158s |

So the "below 16" never bound anything — widening it to the span accent's own modulus
changes nothing here, and it is now derived rather than chosen. The bound that was
costing something was the set SIZE: a fifth residue takes the two most similar passes
anywhere in the piece from 4 steps apart to 6. That moves **124 of the 656 velocities**,
which is 372 of the 1,968 note events across the twelve files. No note moves; velocity is
the only thing the span accent can touch.

**Then it had to be made affordable.** 158 seconds per render was not shippable, and the
test suite would have taken an hour. Two changes, both exact rather than approximate:

- `sieve.py` evaluates a union of ONE modulus — `M@a|M@b|...` — with numpy instead of
  music21. That is the shape the search builds for every candidate, so parsing them was
  the slowest thing in the program. `tests/test_fast_path.py` asserts the two agree on
  every union of every modulus up to 40, over every span used here, and that anything
  else still goes to music21.
- `nominal_period` takes the same shortcut, and `true_period` is cached.

A render went from 1.8s to **0.3s**, and the full search from 158s to 37s.

**The answer is pinned.** `config.SPAN_RESIDUE_SOURCE` carries the residues the search
derives, so renders cost 0.3s instead of 37s. `tests/test_derivation.py` runs the real
search and fails if it ever chooses differently — the pin is a cache, not a decision.
Changing the sieve means setting it back to `None`; the test helper does that
automatically, and the preflight refuses residues that do not suit a new sieve.

## What dois_33 changed

Two things, neither musical.

**The ceilings are now verified.** `state_ceilings` claims each voice can reach
2 x (the weather combinations occurring at its attack steps) velocity states, and every
version since `dois_28` has searched for residues that put every voice AT that number —
so a wrong claim would mean refusing sieves that work, or settling for less than they can
give. Nothing checked it. `tests/test_ceilings.py` now brute-forces the same search space
on two different sieves and requires the claim to be exact in both directions: never
exceeded, and always reached. It is, on both. The sweep costs under three seconds.

**Exports are staged.** See "Where the files go" above. This closes the last item that
was on the known-limits list.

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
