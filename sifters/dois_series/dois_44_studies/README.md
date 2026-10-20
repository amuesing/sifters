# dois_44 studies — six ideas, built to be heard

The ideas the review raised but did not build, each made audible on `dois_44` and changed
in one way only, and a sixth that grew out of the percussion kit: FM pairs. **None of this is a version of the piece.** Each study says exactly where
it departs from the project's principles, in three lists:

- **Holds** — what stays as the principles require;
- **Diverges** — where it breaks or extends a principle, and which one;
- **Chosen** — what came from me rather than from the sieve.

`python3 studies.py` rebuilds everything here in about five seconds, borrowing `dois_44`'s
engine (now in `../archive/dois_44`, where the studies keep using it) without writing
into it. `python3 studies.py --install-serum` copies the study
wavetables into Serum, under **sifters → dois_44 experiments**.

## Listening

`audio/` holds a preview of every study, with `dois_44` rendered the same way beside it —
play them in pairs. Every preview is set to the same loudness (RMS), so differences are
not just level. The audio is not in git: `python3 studies.py` rebuilds all fourteen files
in about five seconds.

The previews are sketches, not renders of your patches, and Serum made none of them:
`preview.py` synthesises them in Python. Wavetable previews read the real tables the way
Serum does with pitch tracking off: one fixed pitch per voice (A 110 Hz, B 165 Hz, C 131
Hz, D 82 Hz), the note or the velocity choosing the frame, each frame band-limited to its
pitch, with a 3 ms attack and a 40 ms release and nothing else — no filter, unison or
effects. Pitched previews use a plucked tone of eight decaying harmonics, two octaves
above the MIDI. For the real thing, load the MIDI in `mid/` with your own Serum patches.

| study | listen to | then |
|---|---|---|
| 1. second moving accent | `1a_dois44_velocity_8_states` | `1b_second_accent_velocity_16_states` |
| 2. orchestration by clause | `2a_dois44_one_timbre_per_voice` | `2b_clauses_a_timbre_per_clause` |
| 3. FM wavetables | `3a_dois44_additive_table` | `3b_fm_grid_table`, `3c_pm_by_sieve_table` |
| 4. prolation canon | — | `4_prolation_canon` (100 s) |
| 5. four multipliers | `5a_dois44_lattice_*`, `5b_dois44_canon_*` | `5c_four_multipliers_*` |

Study 5 comes twice: `_12tet` as the MIDI sounds by default, `_40step` in `dois_44`'s tuning
with the sieve's period as an octave.

---

## Serum 2 renders

`serum_render.py` plays the same MIDI through **Serum 2 itself**, into `audio_serum/`, with
the same file names and loudness as the Python previews. It loads Serum with Spotify's
pedalboard library, which hosts VST3 instruments in Python and renders offline: no DAW,
no Serum window. Each patch is Serum's init patch with oscillator A's wavetable, pitch
tracking, pitch and mod routings written into Serum's saved state (`serum_state.py`).

```sh
python3 -m venv ~/serum-venv && ~/serum-venv/bin/pip install pedalboard zstandard cbor2 mido numpy
~/serum-venv/bin/python serum_render.py      # about 20 seconds for all fourteen
```

Found while building it, on Serum 2.1.5:

- **With pitch tracking off, the oscillator plays MIDI note 0, 8.18 Hz.** OCT and SEM move
  it from there; OCT +4 is 130.8 Hz. The User Guide does not say this.
- **NOTE is mod source 17 and VELO is 16**, and at 100% each puts value *v* exactly on frame
  *v* of a 128-frame table — checked by measuring which harmonics sounded.
- Serum's state is an `XferJson` container: a JSON header, then the patch as zstd-
  compressed CBOR, a map of modules (`Oscillator0`, `ModSlot0`…). A `.SerumPreset` file is
  the same container.

- **A loaded tuning file is kept in the patch as `tuningName` and `tuningData`**: the
  file's name without `.tun`, and its bytes, unchanged, as a list of integers. Read from a
  preset saved in Serum with `dois_44_tuning.tun` loaded; written back the same way, it
  retunes Serum exactly (30.0 cents a key, 1200.0 over 40 keys). The 40-step versions of
  study 5 are rendered this way, with OCT +2 so that note 36 sits at 261.6 Hz as in the
  Python previews (the file puts it at 65.4 Hz).

**Unofficial.** Xfer does not document the state format, so the script refuses any Serum
version but the one it was read from.

The Serum renders match the Python previews closely wherever both play the same tables —
median brightness within a few percent — which is the check that Serum loaded the tables
and landed on the same frames. The pitched studies differ by design: Serum's init patch is
a bright, sustained tone at the written pitch.

## A percussion kit

`percussion.py` builds four Serum 2 drums, one per voice, by one rule — as one weather
covers all four voices — with each voice's own rhythm supplying the numbers:

| part | from | A | B | C | D |
|---|---|---|---|---|---|
| body | the voice's own `dois_44` wavetable, pitch tracking off | `A.wav` | `B.wav` | `C.wav` | `D.wav` |
| pitch | attacks per second, five octaves up | 172.8 Hz | 83.2 Hz | 172.8 Hz | 96 Hz |
| decay | the median gap between attacks | 0.125 s | 0.375 s | 0.125 s | 0.333 s |
| strike | pitch falls 390 ¢ (the lattice's ×13 in 40 steps) over one step | 0.125 s | 0.125 s | 0.125 s | 0.167 s |

Each voice comes in two patches: **accents** (VELO → WT POS, each accent state its own
frame) for the static set, and **lattice** (NOTE → WT POS) for the lattice and canon sets
and their forms. In both, VELO → level runs from 0.35 to 1.0.

```sh
~/serum-venv/bin/python percussion.py --install   # renders audio_kit/, writes presets/
```

`presets/` holds each patch twice: `.SerumPreset`, which `--install` copies into Serum's
`Presets/User/sifters/dois_44 studies kit`, and `.vstpreset`, each checked by loading it
into Serum. The
`.SerumPreset` header matches Serum's own presets key for key. `kit_summary.json` holds
the derived numbers.

- **Holds:** one rule for every voice; pitch, decay and strike length from each voice's own
  rhythm, the strike's depth from the lattice; the MIDI is `dois_44`'s, unchanged. C is A
  rotated, so the rule gives it A's pitch and decay — a canon on one drum, told apart by
  its wavetable.
- **Diverges — pitch.** The accents patches ignore the note, so none of `dois_44`'s pitch
  reaches them, and on the form (which changes only pitch and presence) their sections
  would repeat. The form is rendered with the lattice patches.
- **Chosen:** the five octaves; having a strike at all, and its shape (Serum's default
  envelope curve); the level range. Everything else is Serum's init patch.

The kit needs no tuning: with pitch tracking off, a note only picks a frame. Serum's
browser opens the `.SerumPreset` files.

## 1. A second moving accent — 16 velocity states

**What.** `dois_44` has one moving accent per grid, the span accent. This adds a second,
on the smallest modulus that moves against the 40-step rhythm without lengthening the
voice's statement — 16 for the sixteenth voices, 6 for D — filled halfway by the rule of
`dois_42`. Two accents that move give each attack four on/off combinations across the
passes instead of two, and the velocity table grows from 8 states to 16:

```
1  9  18  26  35  43  51  60  68  77  85  93  102  110  119  127
```

| how many steps differ between passes | `dois_44` | study |
|---|---|---|
| A | 17–19 | **17–27** |
| B | 8–9 | **8–13** |
| C | 18 | **18–27** |
| D | 12–15 | **20** in every pair |

The closest pair stays 8 (B), because two of B's passes still share both accents; nearly
every other pair moves further apart. With VELO → WT POS, 16 velocities pick 16 frames.

- **Holds:** the length (both moduli divide the statement, so parity is untouched); one
  weather; every note, onset and pitch.
- **Diverges — Principle IV.** The span accent is no longer the only accent that moves.
  Principle IV says the accent that moves and the accent that buys parity are one accent;
  here a second one moves and buys nothing.
- **Diverges — the full-profile requirement (`dois_35`).** A and C reach all 16 states,
  but **B reaches 14 and D 12**: two accents that move are more states than their attacks
  can meet.
- **Chosen:** "the smallest modulus other than the span accent's own" for the second
  accent; 16 evenly spaced levels.

Files: `mid/study1_second_accent_{static,lattice}_*`.

## 2. Orchestration by the sieve's clauses

**What.** The psappha sieve is written as seven clauses, and they never overlap, so every
attack of A was made by exactly one of them:

| clause | attacks |
|---|---|
| `(8@0\|8@1\|8@7)&(5@1\|5@3)` | 6 |
| `(8@0\|8@1\|8@2)&5@0` | 3 |
| `(8@5\|8@6)&(5@2\|5@3\|5@4)` | 6 |
| `8@3` | 5 |
| `8@4` | 5 |
| `8@1&5@2` | 1 |
| `8@6&5@1` | 1 |

Each clause gets its own pad, 36–42 — on a drum rack its own sample, in Serum (NOTE →
WT POS) its own frame. C takes the clause of the attack it copies, 13 steps earlier, so
the canon carries A's colours with it. B (43) and D (44) stay whole. This is how
`starbird` orchestrated the sieve as a drum kit, and how the early `psappha` project
accented it.

- **Holds:** rhythm, velocities, parity, one weather — only which pad or frame each attack
  goes to has changed.
- **Diverges — "the sieve is a set of steps".** Clauses belong to how the sieve is
  WRITTEN, not to the steps it selects: the same 27 steps written as another union would
  be orchestrated differently. Here the spelling is the published one, so it carries
  meaning, but it is a fact about the expression.
- **Diverges — the voices.** B has no clauses (it is what the sieve leaves out), so the
  complement pair stops being symmetrical in colour.
- **Chosen:** pads in written order; D kept whole rather than given its A-clause or its
  C-clause.

Files: `mid/study2_clauses_*`.

## 3. FM wavetables

**What.** Two tables, both 128 frames, one gain, harmonics within two periods:

- **FM grid** (`fm grid` in Serum): frame *i* is a sine carrier at the fundamental,
  phase-modulated by a sine at harmonic (*i* mod 8) + 1 with depth (*i* mod 5) + 1 radians
  — the step's address on the sieve's 8 × 5 grid, row as ratio and column as depth, the
  same address the pitch lattice reads. 40 distinct frames; brightness spans **4.4
  octaves**, **1.2 between neighbours** (the additive table of `dois_44`: 1.5 and 0.55).
  Bell-like to brassy to hollow — classic two-operator FM.
- **PM by sieve** (`pm sieve A`–`D`): each voice's own `dois_44` frame, scaled to ±*d*
  radians, modulates a sine carrier — the sieve's register and pattern turned into
  sidebands. *d* is the deepest modulation that keeps 99.9% of every frame's energy within
  two periods of harmonics: 1.45 rad for A, 1.31 B, 1.66 C, 1.56 D, found by bisection.
  Denser and noisier, but with less variety: brightness spans 0.8 octave, 0.26 between
  neighbours.

The preview plays the `dois_44` lattice set through each table with NOTE → WT POS.

- **Holds:** the MIDI (the same lattice set); 40 distinct frames per table; one level per
  table; the two-period bound.
- **Diverges — FM grid:** it uses the sieve's MODULI (the grid) and not its members, so it
  is the same table for every voice — B is no longer the complement of A in timbre.
- **Diverges — both:** FM needs a carrier and a modulator shape, which the sieve does not
  supply.
- **Chosen:** sine operators; the carrier at the fundamental; for the grid, one radian of
  depth per column step. (PM's depth is derived; the grid's is not.)

Files: `tables/study3_*.wav` (and in Serum).

## 4. A prolation canon

**What.** The sieve at every divisor of its period at once: eight layers stating it 1, 2,
4, 5, 8, 10, 20 and 40 times, on steps of 2400, 1200, 600, 480, 300, 240, 120 and 60 ticks
(the fastest a thirty-second note). They begin together and end together after 96,000
ticks — 100 seconds at 120 BPM — when the slowest has stated the sieve once. In the
lattice version every layer reads the lattice at its own step, so it is a canon in pitch
too: one melody at eight speeds. This is the original `sifters` prototype's
`factorize` mode, which the `dois` series never carried over.

- **Holds — Principle I:** every layer states the sieve a whole number of times; the
  length is the first moment all eight end together.
- **Diverges — Principle III ("nothing may repeat identically"):** there is no span
  accent, only the weather, which marks every pass the same way — **the fast layers repeat
  their rhythm identically, up to 40 times**. The span accent each layer would need is as
  long as its whole statement (modulus 1600 for the fastest), beyond the engine's search.
  This study is for hearing the texture first.
- **Diverges — the voices:** every layer is the base sieve; B, C and D play no part.
- **Chosen:** a thirty-second note as the fastest step; one pad per layer (36–43,
  slowest lowest) in the static version; a 4-level velocity table from the weather alone.

Files: `mid/study4_prolation_{static,lattice}_{arrangement,ensemble}.mid`.

## 5. Four lattice multipliers

**What.** The lattice multiplies a step by 13 (mod 40), and 13 has order four: 13, 13² =
9, 13³ = 37, 13⁴ = 1. That closed family — the sieve's own parallel to prime, inversion,
retrograde and retrograde-inversion — is shared out, one map per voice, each read at the
voice's own step:

| voice | map | one step of the sieve moves | in 12-TET | in the 40-step tuning | |
|---|---|---|---|---|---|
| A | ×13 | +13 | a minor ninth up | 390 ¢, a major third (5/4) | the lattice itself |
| B | ×37 = ×13⁻¹ | −3 | a minor third down | 90 ¢ down | the complement takes the inverse |
| C | ×9 = ×13² | +9 | a major sixth up | 270 ¢ (7/6) | the canon takes the lattice twice |
| D | ×1 = ×13⁴ | +1 | a semitone up | 30 ¢ up | the convergence takes it undone |

(Where a move would leave MIDI 36–75 it folds back by 40, so a step sometimes goes the
other way: +13 becomes −27. In the 40-step tuning the fold is an octave, so it is the same
pitch class.)

| A and C where they meet | `lattice` set | `canon` set | study |
|---|---|---|---|
| unisons | 80 of 80 | 0 of 80 | 8 of 80 |

Four melodic characters from one lattice. In 12-TET: A leaping by minor ninths, B
falling by minor thirds, C rising by sixths, D creeping up by semitones. In the 40-step
tuning: A by major thirds, B in 90-cent steps down, C by 7/6, D by 30-cent microtones.

- **Holds:** rhythm and velocity; no number from outside the lattice — the four maps are
  the group its own multiplier generates.
- **Diverges — one lattice:** each voice reads a different map, so pitch no longer means
  one thing per step, and C is no longer a transposition of A's melody (the canon set
  keeps that).
- **Chosen:** which voice gets which power. The pairing above — complement with inverse,
  canon with square, convergence with identity — is a reading, not a derivation.

Files: `mid/study5_multipliers_*`.

## 6. FM pairs: the kit, modulated by each voice's complement

**What.** The percussion kit with a second oscillator as a live FM modulator in Serum:
warp `kFM_OSC` on oscillator A takes oscillator B, which plays the voice's **complement**,
a table of every step the voice leaves out, built by the voices' own table rule. What a
voice leaves out modulates what it keeps. "not A" is byte for byte B's table and "not B"
A's, so A and B modulate each other; "not C" and "not D" are new. The FM depth has an
envelope of its own, decaying over the voice's median gap like the drum's ring, and
velocity scales it: every stroke starts bright and settles, and the accent weather is
heard as brightness. Ratios (modulator to carrier) come from the sieve's numbers: 1:1,
8:5 from its moduli, 13:1 from its lattice diagonal.

| B's loudest stroke, kHz | 0–15 ms | 15–40 | 40–80 | 80–150 | 150–300 |
|---|---|---|---|---|---|
| kit | 3.4 | 3.1 | 2.9 | 2.8 | 2.8 |
| FM 1:1 | 11.2 | 10.2 | 11.3 | 4.9 | 2.8 |
| FM 8:5 | 11.4 | 11.6 | 10.9 | 5.1 | 2.8 |
| FM 13:1 | 10.5 | 12.1 | 8.7 | 3.5 | 2.8 |
| baked | 0.4 | 0.4 | 0.3 | 0.2 | 0.1 |

Rendered: strokes at every accent state and the static set in every version; the canon
set and the lattice set with held notes at 1:1; eight_five's static set at every ratio,
with D's drum re-derived for its grid (80 Hz, ringing 400 ms).

**Baked FM** (`fm_tables.py`): a table per voice whose frame number is the FM depth,
swept by the same envelope. The depth is bounded the way every sifters table is, 99.9%
of the energy within two periods of harmonics. With the voice's own frame as carrier that
bound allows 0.03 rad, no FM at all, because the frame already fills half the band; so
the baked carrier is a sine and the voice's frame its modulator, which allows 2.2-2.35
rad: a low drum that the sieve bends, settling into the pure sine. Live FM has no such
ceiling, which is why the live pairs reach 11 kHz.

**Presets**: 28, named `sifters FM <voice> <accents|lattice> <1-1|8-5|13-1>` and
`sifters FM <voice> baked 1-1`, tagged sifters and FM pair, in `presets/fm_pairs/` as
`.SerumPreset` and `.vstpreset`, and in Serum under **User → sifters → dois_44 studies FM
pairs**. Every
`.vstpreset` is loaded back into Serum and checked for its FM pair.

```sh
~/serum-venv/bin/pip install music21==10.5.0     # fm_pairs.py also builds tables
~/serum-venv/bin/python fm_pairs.py              # about 30 seconds
```

It writes `audio_fm/` (not in git), `tables/fm_*.wav`, `presets/fm_pairs/` and
`fm_summary.json`, and installs the tables and presets into Serum's own folders.

Measured in Serum 2.1.5 while building it: oscillator B must be enabled to modulate, but
can sit at volume 0; a mod slot's amount maps straight onto warp depth (50 = 0.5); a source
written `[4, 16]` is envelope 3 scaled by velocity; the coarse pitch is continuous and
reaches at least +64 semitones, so any ratio sits exactly; below depth ~0.15 the FM is
inaudible. On the kit's one-step strike envelope the FM lasted only 15–40 ms, a click,
hence an envelope of its own.

- **Holds:** both operators come from the sieve; every ratio is one of its numbers; the
  FM decays by the drum's own rule; the baked depth is derived; the MIDI is unchanged.
- **Diverges — loud accents converge.** At the top of the velocity range the FM overrides
  each frame's register: B's four loudest strokes span 3.0–4.5 kHz in the kit and
  9.2–10.9 kHz at 1:1.
- **Diverges — the baked carrier** is a sine, not the voice's frame.
- **Diverges — new tables:** "not C", "not D" and the four depth tables are not in the
  piece itself.
- **Chosen:** which of the sieve's ratios; the peak depth (warp 1.0 at velocity 127);
  Serum's FM mode and envelope curve.

Files: `fm_pairs.py`, `fm_tables.py`, `tables/fm_*.wav`, `presets/fm_pairs/`,
`fm_summary.json`.

---

`summary.json` holds every figure quoted for studies 1–5, as `studies.py` measured it;
`fm_summary.json` those for study 6.
