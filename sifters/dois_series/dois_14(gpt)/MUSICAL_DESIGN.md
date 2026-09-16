# Musical decisions and their reasons

This version separates a source correction, accent-policy choices and a creative
realization. Creative liberties are authorized, but their purpose must remain
explicit. The default creative version retains the reasoned 4:3:2 proposal from
our last iteration; this update makes its alternatives independently auditionable
rather than introducing another unexplained musical change.

## 1. Source correction — factual, common to every preset

The complete opening Psappha sieve is:

```text
((8@0|8@1|8@7)&(5@1|5@3))
|((8@0|8@1|8@2)&5@0)
|((8@5|8@6)&(5@2|5@3|5@4))
|8@3|8@4|(8@1&5@2)|(8@6&5@1)
```

It selects 27 of 40 positions. Earlier versions omitted the last four terms and
selected 15. The corrected attack list, including position 22, is pinned in tests.
Source: [Besada, Barthel-Calvet and Pagán Cánovas (2021), opening sieve S](https://pmc.ncbi.nlm.nih.gov/articles/PMC7849451/),
DOI 10.3389/fpsyg.2020.611316. Claude independently confirmed this source and the
correction in FOR_CHATGPT.md. This is a use of the opening sieve as material, not a
reconstruction of the full Psappha score.

`reference` reproduces Claude's dois_14 with A/B/C at 120 ticks and D=A intersect C
at 160 ticks. All 328 notes, including velocities, durations, channels and pitches,
match the independent fixture from its actual MIDI. Titles/provenance are new.

## 2. Fixed weather — an explicit interpretation of Principle III

`fixed-weather` changes only C's velocities: it shifts C's rhythm, but no longer
shifts the accent field with it. All voices sample the same field at local step i.
This implements the metaphor of rhythms passing under weather. The alternative,
carrying accentuation with C, is a valid canon of the entire music, but is labeled
and confined to the reference preset rather than silently called shared weather.

Equal step numbers occur at different real times on unequal grids. The common
field is in step coordinates, not a synchronized absolute-time modulation signal.
The fixed-phase choice changes neither rhythmic attacks nor the parity point.

## 3. Shared state table — remove an undocumented difference

`shared-weather` keeps fixed phase and changes only D's velocities relative to the
previous preset. The historical per-grid rarity rule gave the same accent state
different values on D's grid. A common table makes the same state mean the same
synth control value everywhere.

Weather weights remain 1 minus their densities: 3/5 for `5@1|5@3`, 3/8 for
`8@0|8@1|8@2|8@5|8@6`. The common span weight is the largest rarity among the
ensemble's required span sieves, here 29/32. This is an explicit design rule, not a
mathematical consequence of the source. It preserves rarity-based ordering without
letting each grid reinterpret the span's expressive meaning.

Every possible combination is ranked, whether or not a particular voice reaches
it; note density cannot change the table. Values are evenly spaced over 1–127.
These are timbre/articulation controls, not assumed loudness. All eight occur across
the creative ensemble; A/B/C/D use 7/5/8/3 states. Per-voice equal coverage is not
forced by inventing private weather or deleting source notes.

| weather5 | weather8 | span | velocity |
|---|---|---|---|
| off | off | off | 1 |
| off | on | off | 19 |
| on | off | off | 37 |
| off | off | on | 55 |
| on | on | off | 73 |
| off | on | on | 91 |
| on | off | on | 109 |
| on | on | on | 127 |

## 4. Creative realization — preserve clarity as the source becomes denser

| Voice | Derivation | Unit | Raw period | Passes to first parity | Notes |
|---|---|---|---|---|---|
| A | Complete sieve | Sixteenth, 120 ticks | 4800 | 4 | 108 |
| B | Complement of A | Sixteenth, 120 ticks | 4800 | 4 | 52 |
| C | A shifted +13 | Eighth-note triplet, 160 ticks | 6400 | 3 | 81 |
| D | B intersect C | Eighth, 240 ticks | 9600 | 2 | 14 |

A and B retain exact interlocking: at gate 1.0, every sixteenth slot belongs to
exactly one of them. The corrected source makes A dense and B sparse naturally.
C gives the same geometry a slower clock as well as a phase displacement. +13
retains the established offset and changes both mod-5 and mod-8 residues.

D extracts seven positions where shifted C lies in B's step pattern, then gives
that pattern a slower clock. Restoring the sieve made A intersect C dense (20
attacks per 40 steps); B intersect C restores a sparse countervoice without arbitrary
thinning. Its seven positions are 2,9,21,24,26,30,32. D does not necessarily fall in
actual-time gaps: the set operation precedes the change of clock.

The 120/160/240 units give 4:3:2 pulse rates. Their raw periods meet FIRST at
LCM(4800,6400,9600)=19200 ticks. Adding the slow voice introduces no longer parity
requirement. Shared start means a common time origin, not an attack on every pad
at time zero. Initial and final rests belong to the pattern.

Each grid's smallest required span modulus is derived, not selected to extend the
piece: 32 for A/B, 3 for C, 16 for D. Clause 1's residue source {0,1,7} is filtered
below each modulus. The weather remains static within the 40-step note layer.
Measured accented periods and all complete passes are checked, so repetition is
earned exactly to the first convergence. This does not prohibit every recurring
short fragment; it prohibits identical complete rhythmic passes and a shorter
period for an entire accented voice.

## 5. Why retain the existing weather?

The mod-5 clause and the mod-8 subset remain meaningful parts of the complete sieve.
The recovered residues 3 and 4 now add rhythm without needing dedicated accents.
Adding every mod-8 class would make that field constant; making {0,1,7} a subset
of weather8 would destroy the span/weather independence used in earlier designs.
The current pair preserves all eight ensemble states and avoids arbitrary pruning
for the sake of a metric. A wider palette is a listening-led future choice.

## Audition

Start with reference, then fixed-weather, then shared-weather: the tests establish
exactly which velocities change at each transition. Finally compare creative to
shared-weather: A/B stay identical, while C and D change relationship in time.
Try velocity as a consistent timbre parameter across your patches. Form, entrances
and larger development remain in the DAW. Structural verification is complete;
there is no claim that these presets have been auditioned on your instruments or
that this is an objectively optimal artistic choice.
