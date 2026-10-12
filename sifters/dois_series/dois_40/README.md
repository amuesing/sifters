# dois_40

The current version. Everything musical is derived from the sieve in `config.py` — the
rhythms, the accent field the velocities are built from, the parity point, the meter and
the pitch lattice. Change the sieve, or any voice's basic unit, and all of it
recomputes. Both pitch modes are exported from one rhythm.

**`dois_40` rebuilds the Serum wavetables so every frame sounds very different.** After
listening, the author found `dois_39`'s frames too alike — and measured, they were: 71-85%
of every frame's energy sat in the fundamental, and frames correlated at 0.95-0.98. Now a
note number or a velocity is a whole number, and the sieve itself says what each whole
number sounds like. Route NOTE (with pitch tracking off) or VELO to wavetable position and
each note, or each accent state, selects its own timbre. The MIDI is unchanged. See
"Serum wavetables", and "What dois_40 changed" for the designs tried and measured first.

`dois_31`–`dois_39` hardened the engine (refusals, generality across sieves and base
durations, staged exports) and took the wavetables through three designs; each is
recorded under its own "What dois_NN changed" below.

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
| `check.py` | Verifies structure and exported events, including an independent velocity calculation and every wavetable frame. |
| `wavetable.py` | The Serum wavetables, and installing them into Serum's own folder. |

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

**In one line: the sieve decides WHEN a voice sounds; the lattice decides what PITCH that
step gets.** (ChatGPT's phrasing, from its 2026-10-05 review — the clearest either of us
has written.)

Every step of the 40-step cycle has an address: where it sits in the 8-step cycle and
where it sits in the 5-step one. Because 8 and 5 share no factor, no two steps have the
same address, so each address can carry its own pitch. Here are the first eight steps,
with the lattice's root at MIDI 36 (C1):

| step | in the 8-cycle | in the 5-cycle | offset | MIDI note |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 36 |
| 1 | 1 | 1 | 13 | 49 |
| 2 | 2 | 2 | 26 | 62 |
| 3 | 3 | 3 | 39 | 75 |
| 4 | 4 | 4 | 12 | 48 |
| 5 | 5 | 0 | 25 | 61 |
| 6 | 6 | 1 | 38 | 74 |
| 7 | 7 | 2 | 11 | 47 |

A voice that attacks on step 5 plays MIDI 61, whichever voice it is. That has two
consequences worth hearing for: voices that attack on the same step are in UNISON (A and
C share 80 attacks, all unisons), and the canon voice C, shifted 13 steps, is not a
transposition — most of its notes rise 9 semitones from A's, but four fall 31.

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

- `dois_40_static_*`: fixed pitches A=36, B=37, C=38, D=39.
- `dois_40_lattice_*`: pitches derived from the sieve’s lattice.
- `dois_40_wavetable_*`: the Serum wavetables, each with a `.txt` sidecar — see below.

Each mode has four `_prime` voice files, a four-track `_arrangement`, and a single-track
`_ensemble` with voices on separate MIDI channels. The prime files are convenient for
routing voices separately in a DAW.

With the current settings, each file ends at 19,200 ticks: 40 quarter notes, or 20 seconds
at 120 BPM. The declared meter is 40/16. Voice note counts are 108, 52, 108 and 60.
Gate remains 1.0; audition articulation on the intended instrument.

## Serum wavetables

### The rule

A note number is a whole number. A velocity is a whole number. A sieve is a rule about
whole numbers. So each voice's table has a frame for every whole number from 0 to 127,
and the sieve decides what each one sounds like:

> **frame *i* sounds harmonic *h*, at full strength, if *i + h* is in the voice's sieve** —
> for *h* = 1 to the sieve's period (40); every other harmonic is silent.

Frame *i* reads one period of the sieve, starting just after *i*, as a set of harmonics.
Nothing else is decided: no rolloff, no emphasis, no smoothing, no forced fundamental. Every
harmonic starts in phase in every frame, and each frame is scaled to the same peak, so
frames differ in colour, not level.

Neighbouring whole numbers read the sieve one step apart, so the set of harmonics changes
at every step — including whether the fundamental and the lowest harmonics are there at
all. That is where the variety comes from.

| | `dois_39` | `dois_40` |
|---|---|---|
| energy in the fundamental | 71–85% | whatever the sieve gives — none in some frames |
| neighbouring frames differ by | ~1–5 dB | 39–45 dB *(a missing harmonic counted as missing)* |
| the 8 velocity levels differ by | 0.6 dB at the closest | 21–42 dB |
| distinct timbres | 8 | 40 — one per step of the sieve's period |

The table holds 40 distinct timbres and then repeats, three times across 128 frames,
because the sieve repeats every 40 steps. Neighbouring frames always differ.

The voices' relationships carry over into timbre. **B**, the complement, holds exactly
the harmonics A's frame lacks. **C**, the canon, holds A's timbres 13 frames along.
**D**, the intersection, is sparser.

### Getting them into Serum 2

```sh
python3 compose.py --install-serum
```

That finds the presets folder your Serum actually uses — read from Serum's own
preferences, `~/Library/Preferences/Serum2Prefs.json`, not assumed (`dois_39` assumed the
default and installed where Serum never looked) — and copies the tables into
`Tables/sifters dois_40/` as `A.wav`, `A sweep.wav`, and so on. One folder per project and
version, directly inside `Tables`: Serum scans no deeper (User Guide p. 345). Restart Serum
and they appear in the oscillator's wavetable menu under **sifters dois_40**, loading with
no import step. A plain render never writes outside the project.

If you drag a WAV instead, Serum always offers import methods (p. 292). Type **2048** in
the Wavetable Editor's formula field first and release on **Constant Framesize**; the
`.txt` beside each WAV also tells Serum the frame size (p. 295).

### Using them

1. Load `A` from **sifters dois_40**.
2. **Turn pitch tracking off**: right-click the oscillator's label, untick *Enable Pitch
   Tracking*; set the pitch with OCT/SEM (p. 35).
3. Route a source to **WT POS**, amount 100%, knob at its start:
   - **NOTE → WT POS** with the **lattice** MIDI: its notes cover every residue of the
     sieve's period, so every step gets its own timbre — the lattice becomes a lattice of
     timbres;
   - **VELO → WT POS** with either set: each accent state's velocity selects its own
     timbre (1 → frame 1, 19 → frame 19 … 127 → frame 127);
   - both, on two oscillators.

NOTE and VELO at their default straight line put value *v* exactly on frame *v*. Serum
does not blend frames (the file asks for none), so each note plays its frame. If one ever
lands a frame off, reshape the curve on that routing in the matrix (p. 211). The static
set is not for NOTE — each voice plays one fixed note and would sit on one frame.

**The sweep table** (`A sweep`) follows the voice's whole parity statement: frame *k* is
the frame for the velocity the piece gives step *k*, frame 0 at a rest, closing on its
first frame. Automate WT POS from 0 to 1 across the 40-quarter-note clip, and turn on
**Disable Smoothing** (Global → Quality, p. 320) so the steps stay crisp.

**For the lattice files, leave KEY/SCALE off** — Serum conforms incoming notes to a scale
(p. 268), which would move them onto other frames.

### What to expect

Bright and buzzy: up to 40 harmonics at equal strength, starting in phase. Not tied to the
played pitch — each frame has its own harmonic make-up, so some have a strong fundamental
and some none. That is what the author asked for: frames that sound very different, and
complexity wherever the sieve supplies it.

### Checked from the files

Every frame of every table is read back by a reader separate from the writer and measured
with an FFT, against the rule rebuilt from the sieve: exactly the harmonics *h* with
*i + h* in the sieve, each at the same strength, all in phase, nothing above one period.
The sweep is checked against the velocities read back out of the written MIDI. Five tests
break a table — the factory flag, an extra harmonic, unequal strength, a frame out of
phase, a sweep out of step — and each must refuse the run with nothing reaching `mid/`.
Installation is tested on stand-in folders and a stand-in preferences file.

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
- The exhaustive search stops at five residues. On this sieve that is now MEASURED,
  not assumed: four cost two steps of pass difference, and six gains nothing — the best
  six-residue set also reaches 6. A different sieve could differ; it has not been
  measured there.
- **Above 300,000 candidates the search is local, and may miss the best set.** It
  improves one set a step at a time and stops when no single change helps. It says so
  when it runs, and its results can be weaker: for 120 against 180 the closest passes
  differ at only 2 steps, against 6 for this piece. It is deterministic, so the same
  settings always give the same answer. Measured against the exhaustive search on this
  sieve, it reaches the same 6 steps in 0.2 seconds — evidence, not proof, that 120/180's
  weak result is the material rather than the search.
- A sieve too sparse for its span accent to inflect every pass is refused, with the
  reason. That is a real limit of the material, not a bug.
- A sieve may exist for which NO weather lets every voice sound every velocity. The run
  is then REFUSED, naming the voices that fall short. Until `dois_36` it printed a
  warning and used the densest weather anyway — and nothing downstream would have
  noticed. For moduli too large to search fully, the weather search keeps only each
  modulus's densest choices and says the refusal is not a proof.
- **Listening has begun, and drove this version.** The author heard `dois_39`'s tables
  in Serum and found the frames too alike; `dois_40` answers that, and was measured before
  it was built. `dois_40` itself has not yet been heard, and every check here is still
  structural.

## What dois_40 changed

The author listened to `dois_39`'s tables in Serum: *"each step seems pretty similar to each
other one … less like a distorted sine wave."* Measured, they were right: 71–85% of each
frame's energy sat in the fundamental (88–96% in three harmonics), and frames correlated at
0.95–0.98. The 1/h rolloff gave the low harmonics nearly everything, and accent states only
nudged a few harmonics' loudness.

The author then set the terms: the table need not be pitch-centric; complexity and noise
are welcome where the sieve supplies them; NOTE (pitch tracking off) and VELO will drive
wavetable position. Five designs were built and measured before choosing:

| design | neighbouring frames differ | distinct | why not |
|---|---|---|---|
| rhythm AND accents, as pulses | large | 4–5 of 8 for B, D | states collapsed onto the same attacks; an empty frame for A |
| attacks raised where the state agrees, smoothed | large | 8 of 8 | still made of choices (the +1/−1 rule, the smoothing, the restored fundamental) |
| fully derived, one step per sample | 3–5 dB | 5 | the sieve repeats, so it buzzes rather than varies; energy above where Serum keeps it at most pitches |
| sieve-seeded noise (40-bit shift register) | ~6 dB | 256 | genuinely noisy, but noise is noise: little to choose between frames |
| **whole number *i* → harmonics *h* with *i + h* in the sieve** | **39–45 dB** | **40 of 40** | — |

The last needs no choices at all, gives the most variety, and turns the note number into a
timbre selector — which makes the lattice set a lattice of timbres. The noise and fully
derived tables remain in Serum's **sifters dois_39 experiments** folder for listening.

Also: `--install-serum` reads Serum's own presets folder from its preferences and installs
to `Tables/sifters dois_40/`, one folder per project and version; `WAVETABLE_EMPHASIS`,
`WAVETABLE_ROLLOFF` and `emphasis_set.py` are gone, because nothing is chosen any more.

80 tests. MIDI note events identical to `dois_35`; renders byte-identical.

## What dois_39 changed

Serum 2 still asked how to import `dois_38`'s tables, so the official Serum 2 User Guide
— on this Mac at `Documents/Production/VSTs/Xfer Records/Serum 2 Presets/` — was read: the
oscillator, Wavetable Editor, import, modulation, voicing and file-structure chapters,
plus a search of all 355 pages. What it changed:

- **The factory flag.** The marker is `<!>2048 BC000000`: B is blending between frames,
  C is the "Serum factory" flag, never to be set on a custom table. `dois_38` copied
  `11000000` from Serum's own files and so labelled these as factory tables. Now
  `00000000`: no blending, not factory.
- **The prompt was Serum's design.** Dragging any WAV shows import choices. The fix is to
  load from Serum's menu: `--install-serum` copies the tables into `Tables/sifters`.
  `.txt` sidecars cover drag-and-drop.
- **Eight velocity frames, not 128.** `dois_38` gave each state a band of 16 identical
  frames for exact alignment, which looked in Serum like a table of near-duplicates. With
  blending off, Serum plays the frame each velocity lands on, and every velocity lands
  within a twentieth of a frame of its own.
- **A listening set** (`emphasis_set.py`): the velocity tables at emphasis 3, 8 and 20.
  Measured first: stronger emphasis sharpens the few harmonics separating the closest
  timbres (11 → 25 dB) but does not spread the difference across the tone.

77 tests. MIDI note events identical to `dois_35`; renders byte-identical.

## What dois_38 changed

**The wavetables, reworked** — everything in "Serum wavetables" above:

- **Serum 2's exact format.** `dois_37`'s marker had zeros where Serum writes flags, so
  Serum asked for a frame size. Serum 2's 288 factory tables were read to find the real
  layout: 32-bit float, `<!>2048 11000000 wavetable (www.xferrecords.com)`. The new
  files' format chunk is byte-for-byte identical to Serum's own.
- **The literal mapping.** Harmonic h sounds if h is in the sieve. `dois_37` mapped step
  n to harmonic n+1, an offset with no reason behind it. Still exactly one period: the
  author pointed out that 40 is the sieve's periodicity, not an arbitrary cutoff, and a
  proposal to extend the pattern to ~1,000 harmonics was withdrawn as padding.
- **128 velocity frames**, so velocity v lands on frame v exactly, with each timbre
  filling a band. `dois_37`'s eight frames left the lowest level about 5% of a frame off.
- **The sweep table**, which carries the span accent's drift — lost in any single frame.
- **Phases: spreading them was tried and measured worse.** Averaged over every frame,
  peak-to-average went from 1.65 in phase to 1.90 with Newman's phases and 1.79 with
  Schroeder's — 1.2 dB quieter at the same peak. Those suit spectra whose harmonics are
  equally loud; a 1/h spectrum in phase is already a sawtooth's shape. In phase stays,
  identical in every frame.

**Three open questions, measured** (the piece is unchanged by all three):

| question | result |
|---|---|
| Does the local span search find what the exhaustive one does? | On this sieve, yes: both reach 6, the local one in 0.2s. |
| Would a sixth residue beat five? | No. The best six-residue set also reaches 6. |
| Is "half the residues" the right size for the weather? | Density cannot decide it: bigger sets always count more attacks. The full-profile requirement can be met at nearly every size, so it does not force half either. Half stays a stated choice. |

**Also:** the lattice explained with a worked example (above); Serum setup and
retrigger notes; `requirements.txt` pinning the library versions the files were rendered
with; and Ableton's `.asd` analysis files ignored by git.

70 tests. The MIDI's note events are identical to `dois_35`'s.

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
