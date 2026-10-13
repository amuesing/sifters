# dois_44

The current version. Everything musical is derived from the sieve in `config.py` — the
rhythms, the accent field the velocities are built from, the parity point, the meter, the
pitch lattice, the canon distance and now the form. Change the sieve, or any voice's basic
unit, and all of it recomputes. Three pitch modes are exported from one rhythm.

**`dois_44` gives the piece a form, read from the sieve.** Until now the piece was one
parity statement — 20 seconds — and form was left to the DAW. Now the lattice and canon
sets also come as a form of 40 sections, one per step of the sieve's period:

- **who plays:** voice X plays in section *s* exactly when X's rhythm has an attack at step
  *s* — the rhythm read again, one level up. A plays 27 sections and B the other 13; C
  plays 27, D 20;
- **what changes:** each section reads the lattice *s* steps further on — a transposition
  by 13 × *s*, all 40 different — so no two sections are alike;
- **how long:** 40 × 19,200 ticks, 160 bars of 40/16, 13 minutes 20 seconds at 120 BPM:
  the sieve's period stated once more, at the top level.

The static set has no form: with no pitch to move, sections with the same voices would
repeat. Every file that existed is unchanged.

`dois_31`–`dois_43` hardened the engine, rebuilt the wavetables, made the passes as
different as the sieve allows and gave pitch a canon and an octave; each is recorded under
its own "What dois_NN changed" below.

## The four voices

| voice | derivation | basic unit |
|---|---|---|
| A | the psappha sieve itself — 27 attacks in 40 steps | sixteenth |
| B | the complement of A — the 13 steps A leaves out | sixteenth |
| C | A shifted by the lattice's diagonal, 13 steps — a canon | sixteenth |
| D | the intersection of A and C, counted in steps | triplet eighth |

A and B tile every sixteenth between them. **D is an intersection of step NUMBERS, not of
moments**: it takes the 20 steps where A and C both have an attack, then plays them on its
own triplet grid. The triplet grid meets the sixteenth grid only once per quarter note, so
in time only 10 of D's 60 notes land where A and C are actually sounding together, and 40
land where neither plays. D is the convergence pattern re-timed at 4:3 — the polyrhythm
heard as a translation of the canon's agreement, not as a doubling of it.

**C's distance is derived.** `shift_amount = 'diagonal'` takes the lattice's diagonal,
sum(P/m) over the sieve's moduli: 5 + 8 = 13 for psappha, the number every version since
`dois_03` wrote by hand. The same number turns steps into pitches in the lattice and orders
the wavetable frames, so one derived number now drives the canon, the pitch lattice and the
timbres. A number in its place still works.

## Where each idea lives

| File | Purpose |
|---|---|
| `config.py` | Your sieve, voice relationships, durations, accent choices and pitch settings. |
| `compose.py` | Coordinates the steps above. `--suggest-span` searches for accent residues without writing MIDI. |
| `sieve.py` | Evaluates sieves, measures actual periods and derives voice rhythms. |
| `transformations.py` | Complement, shift, intersection and the other available rhythm operations. |
| `accents.py` | Derives the weather and span moduli and turns accent combinations into velocities. |
| `span.py` | The span accents' residues: one set per modulus, half of every block, searched exactly. |
| `pitch.py` | Static, lattice and canon pitch rules, plus pitch validation. |
| `tuning.py` | The lattice's period as one octave: `.tun`, `.scl` and `.kbm`. |
| `form.py` | The form: one section per step of the sieve, each voice where its rhythm has an attack. |
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
`SPAN_RESIDUES = None`); naming either explicitly still works.

## Run and use

With Python, numpy, music21 and mido installed:

```sh
python3 compose.py
python3 compose.py --suggest-span
python3 -B -m unittest discover -s tests -v
```

Exports go into **this folder’s `mid/`**, regardless of the directory you run from:

- `dois_44_static_*`: fixed pitches A=36, B=37, C=38, D=39.
- `dois_44_lattice_*`: pitches derived from the sieve’s lattice.
- `dois_44_canon_*`: the lattice read at each note's source step — C a literal canon of A.
- `dois_44_tuning.tun`, `.scl`, `.kbm`: the 40-step period as one octave, for the lattice
  and canon sets.
- `dois_44_lattice_form.mid`, `dois_44_canon_form.mid`: the form, four tracks, 40 sections.
- `dois_44_wavetable_*`: the Serum wavetables, each with a `.txt` sidecar — see below.

Each mode has four `_prime` voice files, a four-track `_arrangement`, and a single-track
`_ensemble` with voices on separate MIDI channels. The prime files are convenient for
routing voices separately in a DAW.

With the current settings, each file ends at 19,200 ticks: 40 quarter notes, or 20 seconds
at 120 BPM. The declared meter is 40/16. Voice note counts are 108, 52, 108 and 60.
Gate remains 1.0; audition articulation on the intended instrument.

## The form

```
section:  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9
A         x x . x x . x . x . x x x x x . x x . x x . x x . x . x x x . x . x . x x x x .
B         . . x . . x . x . x . . . . . x . . x . . x . . x . x . . . x . x . x . . . . x
C         x x x . x . x . x x x x . x x . x x . x . x . x x x x x . x x . x x . x x . x .
D         x x . . x . x . x . x x . x x . x x . x . . . x . x . x . x . . . x . x x . x .
```

That is the sieve (section numbers shown mod 10): the form is the rhythm read again, a
section per step. A and B, the
complement pair, never share a section and between them fill all 40; C enters 13 sections
after A's pattern would, and D only where A and C both play.

**Why every section differs.** Inside a section each voice plays exactly its parity
statement — the same onsets, lengths and velocities as its `_prime` file — and the only
thing the section changes is where it reads the lattice: the note at step *n* of section
*s* is the note its mode gives step *n* + *s*. In the lattice that is a transposition by
13 × *s* (mod 40), different for every *s*, so two sections with the same voices are still
two different transpositions. With the 40-step tuning, that is a chain of major thirds
through all 40 pitch classes, closing where the form closes. With NOTE → WT POS and pitch
tracking off it is a walk through the wavetable's registers instead.

**What is checked** (`check.check_form`, from the file): every section rebuilt from the
voice's own `_prime` file and the sieve — present exactly where the layer has an attack,
the statement unchanged, the pitches recomputed at *n* + *s* — and all 40 sections
different. A test removes the transposition and requires the run refused.

**What it is not.** It is one way to make a form from the sieve, and the plainest: the
same sieve, the same reading, one level up. Entrances are abrupt — a voice is in a
section or not — and the form makes no other dynamics. It is offered as material, like
the statement: the DAW can still cut, extend or reorder it.

## The canon set and the tuning

**Canon.** The lattice gives every step a pitch; `lattice` lets every voice read it at the
step where it sounds. `canon` lets every voice read it at the step its note comes FROM —
a shift reads back by its distance, a retrograde reflects, an augmentation divides; a
complement or intersection keeps its step, because that step is where its note comes from.
For this piece only C differs: C's note at step *n* is A's note at step *n* − 13. Heard:

| | `lattice` | `canon` |
|---|---|---|
| A and C where they sound together | unison, 80 of 80 | 31 steps apart, 80 of 80 |
| C's melody | A's melody shifted +9 (mod 40) | A's melody, note for note, 13 steps later |

So the canon is a canon in pitch as well as rhythm, and the pair is counterpoint rather
than heterophony — the question CONTEXT.md had left open since `dois_15`. The checker reads
both files back and requires every one of C's 108 notes to be A's 13 steps earlier.

**Tuning.** With the period as an octave each lattice step is 30 cents:

| lattice move | steps | 12-TET semitones (untuned) | 40 steps to the octave | nearest simple ratio |
|---|---|---|---|---|
| one step of the sieve | ×13 | 13 (a minor ninth) | 390 cents | 5/4 (386) |
| the canon's displacement | +9 | 9, or −31 at the fold | 270 cents, always | 7/6 (267) |
| C against A, canon set | 31 | 31 | 930 cents | 12/7 (933) |

Load `dois_44_tuning.tun` in Serum (Global → TUN FILE → Load Tuning, p. 320), or load the
`.scl` and `.kbm` into the free MTS-ESP MINI to retune every Serum instance at once
(p. 321). Tuning only matters where pitch is heard: with pitch tracking off and NOTE → WT
POS, a note number picks a frame, not a frequency.

The one choice is that the period spans an octave. Not yet heard: the files follow the
AnaMark and Scala formats and are read back by parsers of their own, but no tuned note has
been played.

**Held notes.** `ARTICULATION = 'held'` in `config.py` makes every note last until its
voice's next attack — B's notes ring 2–6 steps, A's 1–2, and each voice tiles its own time.
On Serum that gives envelopes and wavetable motion time to happen; every note then abuts
the next, so a device that will not retrigger needs the default, `'step'`.

## Serum wavetables

### The rule

A single cycle has a harmonic series; the sieve has a period. So a frame can state that
period once, as harmonics:

> **frame *i* reads one period of the voice's sieve from *i* + 1 — as `dois_40` did — and
> sounds it from just above its cut *c* = 13 × *i* mod 40: harmonic *c* + *h* sounds, at
> full strength, when *i* + *h* is in the sieve, for *h* = 1 to 40.**

Every member of the sieve sounds exactly once in every frame: the period, stated once. The
READING gives each frame its own pattern — the sieve has 40 different rotations, so the
table has 40 different frames. The CUT gives each frame its own register: cut 0 starts at
the fundamental, cut 39 starts at harmonic 40, a high band with no fundamental. Register is
what the ear hears as brightness, and it is what `dois_40` lacked.

**Why 13.** It is the lattice's diagonal (5 + 8, derived from the sieve's moduli), the
number that turns steps into pitches. Neighbouring frames sit 13 harmonics apart in
register rather than one, so scrubbing the table, or moving from one note number to the
next, jumps a long way every time. A sieve whose moduli share a factor has no lattice; its
cuts then go in order, and the render says so.

**A cut alone was tried first** — harmonic *m* sounding when *m* mod 40 is in the sieve, the
cut only deciding where the period starts. It changes a frame only when the cut crosses a
member of the sieve, so a voice gets as many distinct frames as it has attacks: 27 for A,
14 for B, and two of B's velocity states landed on the same frame. Reading from *i* keeps
all 40 in every voice.

**What the ear hears,** measured as spectral centroid (brightness) in octaves on voice A:

| | `dois_40` | `dois_41` |
|---|---|---|
| brightness range across the table | 0.17 | **1.53** |
| between neighbouring frames | 0.03 | **0.55** |
| between successive notes of the lattice melody | 0.05 | **0.62** |
| across the 8 velocity states | 0.12 | **1.35** |
| distinct frames, every voice | 40 | 40 |
| level | each frame scaled to its own peak: 0.4–1.2 dB drift | **one gain: equal RMS in every frame** |
| highest harmonic | 40 | 79 |

`dois_40`'s frames all differed — each had its own set of harmonics — but every one lived
in harmonics 1..40, the same register at the same density, so they sounded alike.

**Why two periods and no more.** With pitch tracking off, Serum plays a wavetable at a
fixed pitch that the User Guide does not state. At middle C (261.6 Hz) harmonic 79 is
20.7 kHz, still under Nyquist at 44.1 kHz. The leap prototypes installed before this
version reached harmonic 166: at that pitch about a third of their frames would have
sounded nothing at all, and those prototypes are superseded by this table.

**One level.** Every frame has one harmonic per member of the sieve, all equally strong, so
every frame has the same RMS. One gain, set by the table's loudest peak (0.95), keeps that,
so VELO changes colour and register, never loudness. `dois_40` scaled each frame to its own
peak, which moved the level 0.4–1.2 dB between velocity frames — ChatGPT's measurement.

**What is convention, not sieve.** Equal strength for every present harmonic, one starting
phase for all of them, and reading residues upward from the cut. The sieve supplies which
harmonics are present; this is the most direct way to sound that. (ChatGPT's
qualification of `dois_40`'s "no choices", which was overstated.)

The table holds 40 distinct frames and then repeats, three times across 128 frames,
because the sieve repeats every 40 steps. **B**, the complement, holds in every frame
exactly the harmonics of the period that A's frame leaves out.

### Getting them into Serum 2

```sh
python3 compose.py --install-serum
```

That finds the presets folder your Serum actually uses — read from Serum's own
preferences, `~/Library/Preferences/Serum2Prefs.json`, not assumed — and copies the tables
into `Tables/sifters/dois_44/` as `A.wav`, `A sweep.wav`, and so on: one `sifters` folder
in Serum's menu, with a folder per version inside it. Serum 2's own factory tables sit at
the same depth (`Tables/S2 Tables/Analog/`), so it scans there. Restart Serum, or use
**Rescan Folders on Disk** in the main menu, and they appear under **sifters → dois_44**,
loading with no import step. A plain render never writes outside the project.

If you drag a WAV instead, Serum always offers import methods (p. 292). Type **2048** in
the Wavetable Editor's formula field first and release on **Constant Framesize**; the
`.txt` beside each WAV also tells Serum the frame size (p. 295).

### Using them

1. Load `A` from **sifters → dois_44**.
2. **Turn pitch tracking off**: right-click the oscillator's label, untick *Enable Pitch
   Tracking* (p. 35). Keep the oscillator's OCT at 0 or below: an octave up doubles every
   frequency, and the top of the register would rise past what Serum can play.
3. Route a source to **WT POS**, amount 100%, knob at its start:
   - **NOTE → WT POS** with the **lattice** MIDI: its notes cover every residue of the
     sieve's period, so every step gets its own register — the lattice becomes a lattice
     of timbres;
   - **VELO → WT POS** with either set: each accent state's velocity selects its own
     frame (1 → frame 1, 19 → frame 19 … 127 → frame 127);
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

Low cuts are full and buzzy, with a fundamental; high cuts are thin, bright bands with
none, closer to a formant or a whistle than a note. Not tied to the played pitch. Every
frame is the whole sieve; what changes from frame to frame is where it starts reading and
how far up the series it sits.

### Checked from the files

Every frame of every table is read back by a reader separate from the writer and measured
with an FFT, against the rule rebuilt in `check.py` — including the cut order, which the
checker finds its own way (the residue congruent to P/m modulo every modulus m) instead of
adding the moduli as the writer does. Checked: exactly the harmonics *c* + *h* with *i* + *h*
in the sieve, each at the same strength, all in phase, nothing else; every frame at the
same RMS and the loudest peak at 0.95. The sweep is checked against the
velocities read back out of the written MIDI. Six tests break a table — the factory flag,
an extra harmonic, unequal strength, a frame out of phase, a sweep out of step, a frame at
another level — and each must refuse the run with nothing reaching `mid/`. Installation is
tested on stand-in folders and a stand-in preferences file.

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
- **the span accents' residues** — one set per span modulus. Pass k of a voice reads the
  accent at (k × layer + i) mod the modulus, so each layer step cycles through one block of
  positions, as many as there are passes, and a set is a choice of which positions of each
  block to fill. Filling every block halfway makes the passes differ most in total (an
  attack whose block holds f of n positions separates f × (n − f) pass pairs), so the
  accent takes half its modulus. Among half-full sets the winner keeps the closest passes
  furthest apart, then the next closest, and so on; ties go to the lowest residues.
  Exhaustive while a modulus has at most two million half-full sets (1,679,616 for 32,
  under a second); beyond that a local search runs and says so. Single-pass voices, which
  have no passes to tell apart, keep the search of `dois_30`–`dois_41`: the smallest set of
  up to five that completes the velocity profile. `config.py` pins the answer;
  `tests/test_derivation.py` fails if the search stops agreeing with it;
- the parity point, the meter, and the lattice's axes and intervals;
- C's canon distance (`'diagonal'`: 13), and the wavetables' frame order, from the same
  lattice diagonal.

Still yours: the sieve, how the voices relate (complement, shift, intersection), the
basic units — any combination of them — tempo, root note, gate and velocity range. Naming `WEATHER` or
`SPAN_RESIDUES` explicitly in `config.py` overrides the derivation and is checked
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
| `SPAN_RESIDUES` that leave two passes of a voice identical | refused, naming the voice and the pass pair, and pointing at `--suggest-span`. In `dois_30` this path raised `NameError`: it called a function that had been deleted. |
| `SPAN_RESIDUES` pinned for another sieve or other basic units | refused, naming the modulus that has no set and telling you to set it back to `None`. |
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
made every pass distinct, the run says the bounded search failed — sets of up to five
residues below the span accent's own modulus, at these basic units, with this weather —
and that a wider search or
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
  independence is what makes it move across the passes. What IS derived since `dois_42` is
  its size and shape: half of every block, by the arithmetic above.
- **Above two million half-full sets for a modulus, the search is local and may miss the
  best.** It improves one block at a time and stops when no single change helps, and says
  so when it runs. 120 against 180 is such a case — moduli 96 and 64 — and still lifts the
  closest passes there from 2 steps apart (`dois_41`) to 6.
- Single-pass voices keep the older search, whose five-residue cap is a choice; above
  300,000 candidates it too is local and says so.
- **Rare states are less rare.** With the span accent firing on half its positions, the
  states that include it are as common as those without. The ranking is still by rarity —
  the velocity table did not change — but A's top velocity now sounds 14 times, not 3.
- A sieve too sparse for its span accent to inflect every pass is refused, with the
  reason. That is a real limit of the material, not a bug.
- A sieve may exist for which NO weather lets every voice sound every velocity. The run
  is then REFUSED, naming the voices that fall short. Until `dois_36` it printed a
  warning and used the densest weather anyway — and nothing downstream would have
  noticed. For moduli too large to search fully, the weather search keeps only each
  modulus's densest choices and says the refusal is not a proof.
- **Listening drives the wavetables, and these versions are not yet heard.** The author
  heard `dois_39`'s and `dois_40`'s tables in Serum and found the frames too alike; `dois_41`
  answers that with a measure of what the ear hears (brightness) rather than of which
  harmonics are present. `dois_42`'s velocities, `dois_43`'s canon set and tuning, and
  `dois_44`'s form are all unheard. Every check here is structural.
- The fixed pitch of a non-tracking Serum oscillator is not documented. Two periods of
  harmonics are safe up to about 276 Hz at 44.1 kHz; raise the oscillator's OCT and the
  highest frames lose their top.

## What dois_44 changed

**A form, in `form.py`**: `<title>_lattice_form.mid` and `<title>_canon_form.mid`, 40
sections of one parity statement each, voice X present in section *s* when its layer has an
attack at step *s*, every section reading the lattice *s* steps on. Checked section by
section from the file (`check.check_form`); a test removes the transposition and the run is
refused. `FORM = True` in `config.py`; the static set has none. Two more files per render,
768,000 ticks each.

`dois_09` was the last version with a form in code: 5 movements × 8 sections — the sieve's
moduli — but presence set by density thresholds chosen by hand (0.30, 0.50, 0.30, 0.15).
Here presence is membership, with nothing chosen.

Also: the provenance stamp is built in one place (`compose.provenance`), since the forms
carry it too.

110 tests. Every file that existed in `dois_43` is unchanged.

## What dois_43 changed

Three things, each new, none changing a file that existed:

1. **The `canon` pitch mode** (`pitch.canon_notes`, `pitch.source_step`): the lattice read
   at each note's source step. A and C, in unison at all 80 meetings in `lattice`, sound 31
   steps apart at all 80 in `canon`; C's 108 notes are A's, 13 steps later. The checker
   recomputes each note's source its own way (`check.origin_of`) and verifies the
   imitation from both files. Six more files per render.
2. **The tuning files** (`tuning.py`): the period as one octave, as AnaMark `.tun` and
   Scala `.scl` + `.kbm`, written when a lattice or canon set is, and read back by
   `check.check_tuning`. A test breaks one note's tuning and requires the run refused.
3. **`ARTICULATION = 'held'`** (`midi.note_lengths`): the sieve's gaps as durations,
   checked from the files when chosen. Default `'step'`.

102 tests. `static` and `lattice` identical to `dois_42`, note for note and velocity for
velocity.

## What dois_42 changed

The review of `dois_41`'s piece found the passes nearly identical: A's four passes differed
at 6–7 of its 27 attacks, B's at 6 of 13. The span accent fired on 5 of its 32 positions,
because `dois_34` capped sets at five residues and broke ties toward FEWER — so the accent
that exists to make restatements differ was as sparse as the search allowed.

**The arithmetic.** Pass k reads position (k × 40 + i) mod 32 at layer step i. 40 mod 32 is
8, so the four passes of a step read four positions 8 apart — one block of four, and the 32
positions make 8 such blocks. An attack whose block holds f filled positions sees the
accent on f passes and off on 4 − f, and so separates f × (4 − f) of the 6 pass pairs: 3 for
f = 1 or 3, **4 for f = 2**. Total difference is therefore greatest when every block is half
full — 16 of 32 residues — and every such set gives the same total. Nothing chose "half";
the total did.

**The choice among half-full sets.** 1,679,616 of them, all tried, in under a second
(`span.py`, meeting in the middle). 302,592 tie on the closest pair, 8; comparing every
pair from the closest up (leximin) leaves 512, all equally good, and the lowest residues
decide: `{32: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 18, 20, 22, 27, 31), 3: (0,)}`.

**One set per modulus.** Up to `dois_41` one shared set was read below each modulus, so D's
mod-3 accent was whatever of that set fell below 3. Now each span accent is derived for
its own modulus: D's is half of a 3-position block, rounded down — one residue, `(0,)`,
which it already had. `SPAN_RESIDUE_SOURCE` is now `SPAN_RESIDUES`, a dict.

**Measured on the other unit combinations the tests render:** all still reach every
voice's ceiling; 120 against 120/240 reaches 13 steps between its closest passes; 120
against 180 goes from 2 to 6.

Also: the residue search moved from `compose.py` into `span.py` (`compose.py` went from 720
lines to under 500); `velocities_of` moved to `accents.py`; a test that patches
`nominal_period` now clears `sieve_moduli`'s cache first, since a cached answer would never
consult the patch; and the tests' docstring still said `dois_40`.

91 tests. Notes identical to `dois_35`; 744 of the 1,968 note events changed velocity, all
in A, B and C. The velocity table itself is unchanged.

## What dois_41 changed

The author, on `dois_40`: *"each frame is so similar."* The `dois_40` README claimed
neighbouring frames 39–45 dB apart. That figure counted a missing harmonic as a huge
difference, which is not how the ear hears it. Measured as brightness, `dois_40`'s 128
frames spanned 0.17 of an octave: every frame lived in harmonics 1..40. Four rules were
measured before choosing, on what the piece actually plays (notes 36–75, velocities 18
apart):

| rule (voice A) | whole table | neighbours | lattice melody | velocity states | distinct frames (B) | top harmonic |
|---|---|---|---|---|---|---|
| `dois_40`: read from i, within 1..40 | 0.17 | 0.03 | 0.05 | 0.12 | 40 | 40 |
| leap prototype: residues in place, start 40·i mod 127 | 2.83 | 0.88 | 0.67 | 2.83 | 14 | 166 |
| slide: residues in place, cut at i mod 40 | 1.52 | 0.04 | 0.68 | 1.38 | 14 | 78 |
| cut alone: residues in place, cut at 13·i mod 40 | 1.52 | 0.61 | 0.65 | 1.31 | 14 | 78 |
| **read from i, sounded from the cut 13·i mod 40** | **1.53** | **0.55** | **0.62** | **1.35** | **40** | **79** |

(octaves of spectral centroid; B, C and D measure alike.) The leap prototype spread
furthest, but its window start came from MIDI's range rather than the sieve, and its top
frames would be silent at middle C. Slide keeps neighbours alike. Every rule that keeps
residues in place gives a voice only as many frames as it has attacks — B's velocity states
then share a frame. Reading from *i* and sounding from the cut keeps all 40, stays inside
two periods, and takes its order from the lattice.

Also:

- **One gain per table** (ChatGPT, 2026-10-12): equal RMS in every frame; checked, and a
  sixth broken-table test.
- **Installation** into `Tables/sifters/<version>/`, at the author's request: one sifters
  folder in Serum's menu. The earlier tables were moved there by hand on 2026-10-11, after
  checking no saved preset referred to them.
- **C's shift is derived**: `'diagonal'` = 13, the same as before, so no note moved. For
  another sieve it now follows that sieve: 12 for the 7 × 5 test sieve, which renders
  with every voice at 8/8, and 14 for the 11 × 3 one, where D = A & C becomes too sparse
  for any weather to give every voice the whole profile — refused, nothing written. At
  the hand-written 13 that sieve rendered; write a number to get it back.
- **Augmentation fixed.** `stretch_binary` was `np.repeat`, which turned each attack into
  `factor` attacks — [1, 0, 1] by 2 gave [1, 1, 0, 0, 1, 1], a roll rather than an
  augmentation. It now spaces them: [1, 0, 0, 0, 1, 0]. No composition used it.
- **`check.py` imported `tile_to`** — it called it without importing it, in a branch no
  current sieve reaches.
- **What D is**, stated: an intersection of step numbers, re-timed (see "The four voices").
- `sieve_moduli` is cached: resolving `'diagonal'` reads the moduli whenever C is rebuilt,
  and the residue search rebuilds it hundreds of thousands of times.
- The configuration comment and this README still described the span search as "up to
  four residues below 16", which `dois_34` replaced. Corrected.

MIDI note events and velocities identical to `dois_40` (and so to `dois_35`); only the
title and provenance stamp differ.

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
