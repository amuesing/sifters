# Musical design: complete Psappha, three rates, one weather

This is a compositional proposal within the user's principles, not a claim that
one numerical arrangement is objectively the most creative. The implementation
was checked mathematically and against MIDI bytes; it has not been auditioned
through the user's synth patches.

## Correct the source before developing it

The opening sieve S reproduced by Besada, Barthel-Calvet and Pagán Cánovas (2021)
contains 27 attacks in 40 pulses. Earlier project versions omitted four terms and
produced only 15. The complete expression is now the base voice:

```text
((8@0|8@1|8@7)&(5@1|5@3))
|((8@0|8@1|8@2)&5@0)
|((8@5|8@6)&(5@2|5@3|5@4))
|8@3|8@4|(8@1&5@2)|(8@6&5@1)
```

The two unconditional mod-8 classes abbreviate intersections with all five mod-5
residues. The recovered attacks are 3,4,6,11,12,17,19,20,27,28,35,36 (zero-based).
The persistent reference test includes the published 27-position set, including
22, and separately evaluates the congruences without music21.

Source: [Gearing Time Toward Musical Creativity: Conceptual Integration and Material
Anchoring in Xenakis' Psappha](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.611316/full),
section on the opening sieve S, DOI 10.3389/fpsyg.2020.611316. This version uses
that opening sieve as compositional material; the derived four-voice music is not
an attempted reconstruction of the entire score.

## Give each relationship a clear temporal role

| Voice | Definition in step coordinates | Unit, at 480 PPQ | Attacks per 40 steps | Passes | Total notes |
|---|---|---|---|---|---|
| A | Complete sieve S | Sixteenth, 120 ticks | 27 | 4 | 108 |
| B | Complement of A | Sixteenth, 120 ticks | 13 | 4 | 52 |
| C | A shifted +13 steps | Eighth-note triplet, 160 ticks | 27 | 3 | 81 |
| D | B intersect C | Eighth, 240 ticks | 7 | 2 | 14 |

A/B are a continuous interlocking pair: at full gates, exactly one of them occupies
each sixteenth slot. Restoring the full source naturally swaps which member is dense.
C restates the same geometry at a different speed and phase, so its relationship
with A changes through the statement. +13 retains the existing canon offset and
moves both mod-5 and mod-8 residues; it also equals the complete sieve's complement
cardinality. It is a deliberate compositional choice, not historically attributed.

D extracts the part of C's step pattern that lies outside A, then gives it a slower
clock. Its seven positions are 2,9,21,24,26,30,32. This supplies a sparse countervoice
after restoring the source made the old A-intersect-C layer dense (20 attacks).
These set operations happen BEFORE assigning durations: D does not detect actual
silences or simultaneous attacks in the rendered timeline. The voices share the
same time origin and end boundary; some begin with intentional rests.

## First convergence earns exactly one complete statement

Raw rhythm periods are 4800,4800,6400,9600 ticks. Their least common multiple is
19200 ticks: 40 quarter notes, 20 seconds at 120 BPM. The pulse rates are 4:3:2;
adding the slower eighth-note voice introduces no new prime factor into the parity.
Automatic meter remains 40/16 (four bars); the same span is ten bars of 4/4.

The engine derives the smallest span modulus satisfying each grid's required span:

| Voices | Steps to parity | Required span accent |
|---|---|---|
| A, B | 160 | `32@0|32@1|32@7` |
| C | 120 | `3@0|3@1` |
| D | 80 | `16@0|16@1|16@7` |

The common residue source remains clause 1's {0,1,7}, filtered below each derived
modulus. All accents have their measured periods; each full accented voice has
minimal period 19200 ticks and all its complete 40-step passes are distinct.
This does not forbid every repeated short fragment or repeated velocity. It forbids
identical complete rhythmic passes and a shorter period for the full voice.

## Make one weather mean the same thing on every grid

Retain `sieve5 = 5@1|5@3` and `sieve8 = 8@0|8@1|8@2|8@5|8@6`. They are meaningful
clause-derived subsets of the complete source, not a claim to enumerate every
mod-8 class now present. Their periods divide 40, so they colour each rhythmic
pass identically and cannot extend parity. The span residues include positions
both inside and outside weather8, preserving its independence from the span accent.

`ACCENT_PHASE_POLICY = 'fixed'`: every voice samples the same weather at the same
local step index; shifting C no longer drags the accent field with it. On different
units, equal step numbers occur at different absolute times. This is shared weather
in step coordinates, not a globally synchronized time-based modulation signal.

`VELOCITY_POLICY = 'shared_rarity'`: all accented voices use one state-to-velocity
table. Weather weights are 1 minus their densities (3/5 and 3/8). The span's common
weight is the largest rarity among the ensemble's derived span sieves, here 29/32.
This treats span activation as one expressive role rather than changing its value
with the grid. Using the maximum is a documented design choice; it retains the
existing rarity framework while removing per-grid disagreements. Changing the
ensemble's span requirements can change this shared table.

States are ranked by summed weights, with numeric state code breaking ties, then
evenly spaced across the configured MIDI range. Every possible state is ranked,
including those not encountered by a particular voice. The table never depends on
how many notes a voice plays or on which states its rhythm reaches.

| weather5 | weather8 | span | Velocity |
|---|---|---|---|
| off | off | off | 1 |
| off | on | off | 19 |
| on | off | off | 37 |
| off | off | on | 55 |
| on | on | off | 73 |
| off | on | on | 91 |
| on | off | on | 109 |
| on | on | on | 127 |

A/B/C/D realize 7/5/8/3 states respectively; all eight occur across the ensemble.
D's three colours are intentional, not missing notes. Velocity remains available
for timbre, articulation, filter or envelope control rather than assuming volume.
An entirely unaccented single-pass voice uses UNACCENTED_VELOCITY; no dummy span
is introduced. Historical `per_grid_rarity` and `follow_shift` remain supported.

## Alternatives considered

A small exploration compared offsets 1,5,8,13,17 with the original clock layout,
three-rate layouts using A-intersect-C or B-intersect-C, and a 192-tick fifth-based
unit. This is a bounded comparison, not an exhaustive optimization.

Merely restoring the source with the original layout and +13 creates 328 notes
and makes D much denser. The chosen 255-note design gives C more temporal independence
and D more space. Keeping D=A-intersect-C on the slower eighth grid is valid but
produces 40 D notes instead of 14. A fifth-based unit lengthens raw convergence to
96000 ticks; the existing residue family also repeats complete A passes there, so
that candidate was rejected rather than relaxing the principle.

A third weather sieve from the recovered exceptional terms was also inspected.
It adds structurally unreachable combinations and more state bookkeeping; the two
existing fields already reach every combination across this ensemble. The recovered
terms therefore speak through the rhythm itself. No arbitrary thinning, stochastic
humanization, imposed arrangement, or extension beyond parity was added.

## Audition and develop

Begin with the A/B pair to hear the sieve and its complement, bring in C to hear
its slower transformed statement, then D for the sparse countervoice. A shorter
sound on A/B, a related resonant sound on C, and a sustained or contrasting sound
on D can expose these roles. These are sound-design suggestions, not baked-in MIDI
changes. Keep velocity mappings intentional across the patches.

The engine supplies one complete statement. Entrances, exits and larger form remain
in the DAW. The next artistic decision should come from listening to these files.
