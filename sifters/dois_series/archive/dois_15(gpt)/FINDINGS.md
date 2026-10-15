# Lattice findings and a controlled clock comparison — 2026-09-16

## Claude's mapping

For step n, pitch is root + (5*(n mod 8) + 8*(n mod 5)) mod 40. This equals
root + (13*n mod 40). Since gcd(13,40)=1, multiplication permutes all 40 positions.
It is this modular linear structure, not bijectivity alone, that carries congruence
classes to congruence classes. Arbitrary permutations do not have that property.

At root 36 the complete collection is MIDI 36–75: 40 notes spanning 39 semitones.
Swapping source moduli to become axis intervals, interpreting them as semitones and
folding into a 40-position pitch space are compositional choices supported by the
source. The sieve does not uniquely mandate them.

The lattice preserves positional relationships under a reversible mapping. My prior
signed-gap approach preserves successive sieve-gap magnitudes and selects directions
for closure. Neither is the unique meaning of deriving pitch from the sieve.

## Corrections to the interpretation, not the baseline music

The +13-step canon produces +9 MODULO 40. Of 27 corresponding notes in one cycle,
23 rise nine semitones and four fall 31 semitones. The latter interval is not octave-
equivalent to +9: modulo 12 the intervals are 9 and 5. This is a transposition in the
40-position space, not a constant chromatic or twelve-pitch-class transposition.

A/B have 27/13 disjoint MIDI pitches, together covering the 40-note collection. This
is not a partition of twelve pitch classes. Reducing to octave-equivalent classes
would be a different musical operation and lose this distinction.

Claude's source fingerprint omitted pitch settings and gate. The GPT fork fixes that
provenance issue. The old validator called the writer's lattice helper again; this
fork additionally uses multiplier arithmetic in file verification and independently
decodes files in tests. The lattice is still intentionally specific to axes 8 and 5;
changing the base sieve's period now produces an explicit early rejection.

## Baseline measured from MIDI

All four voices match Claude dois_15 event-for-event; its onset/duration/velocity
streams also match Claude dois_14. End: 19200 ticks. Note counts: 108/52/108/60.
No hanging or same-channel overlapping notes were found in the twelve GPT files.

A–C share 80 attacks, all unisons. B–C share 28, all unisons. This follows from the
shared 120-tick grid reading the same pitch index. It is a valid musical texture,
not a MIDI defect. The default retains it to make the baseline trustworthy.

## Optional `moduli` experiment

This changes the pitch lookup clock only. All voices still play their original
attack, duration and velocity streams. Pitch states change silently between attacks;
a sounding note keeps the pitch sampled at its onset until its existing note-off.
There is no retuning of held notes, added attack, gate change or length extension.

Let P be the original raw-rhythm parity (19200 ticks), L=40 the lattice period,
k the chosen number of pitch traversals before P, and t an attack's absolute tick.

    index(t) = floor(t * L * k / P) modulo L
    pitch(t) = root + (13 * index(t)) modulo L

Exact integer arithmetic is used. At a pitch-state boundary, an attack reads the NEW
state. Pitch-step duration P/(L*k) must be an integer number of ticks, or rendering
fails before replacing MIDI. All pitch clocks return to index zero at P. Their
cycle lengths together with the original raw rhythm periods still have LCM P.

| Voice | Cycles k | Pitch-cycle length | Pitch-state duration |
|---|---:|---:|---:|
| A | 5 | 8 quarter notes | 1/5 quarter note, 96 ticks |
| B | 8 | 5 quarter notes | 1/8 quarter note, 60 ticks |
| C | 5 | 8 quarter notes | 1/5 quarter note, 96 ticks |
| D | 1 | 40 quarter notes | 1 quarter note, 480 ticks |

5 and 8 come from the source moduli. Assigning 5 to A and 8 to its complement B is
an explicit creative choice. C inherits its parent's pitch rate. D uses gcd(5,8)=1
as a slow full-span reference; selecting that operation is also a creative choice,
not a necessary consequence of its intersection rhythm. There is no claim that every
voice now has a uniquely different pitch clock.

All pitch-clock phases remain zero. This isolates clock rate from phase experiments.
In particular, I have NOT added the separately discussed 13-pitch-step delay to C.
C remains the original rhythmic canon, but the new sampled melody is not guaranteed
to be A's pitch canon. A future phase study should be labeled separately rather than
quietly folded into this rate comparison.

## What the experiment actually preserves and loses

| Property | Lattice baseline | Independent clock study |
|---|---:|---:|
| Rhythms, gates, velocities, original parity | Preserved | Preserved |
| A/B distinct pitch counts | 27 / 13 | 32 / 13 |
| A/B pitch-set overlap | 0 | 10 |
| A/B pitch-set union | 40 | 35 |
| A–C unisons / shared attacks | 80 / 80 | 80 / 80 |
| B–C unisons / shared attacks | 28 / 28 | 1 / 28 |
| C distinct pitches | 27 | 32 |
| D distinct pitches | 20 | 38 |

The lattice itself stays bijective, but attacks sample only some states. In B, a
120-tick attack grid samples a 60-tick pitch grid: only even state indices can sound.
Its unchanged count of 13 distinct pitches does not mean it retained its original
pitch collection. D also becomes much more melodically active than the two-anchor
voice in my earlier GPT version; this fork follows Claude's lattice instead.

Repeated individual pitches are permitted. Existing accented rhythmic passes remain
pairwise distinct, and their minimal period stays the full statement BEFORE pitch
is considered. Independent clocks do not license identical accent repetitions.

## Iteration questions

1. Which is more important in the next experiment: A/B partitioning, pitch canon, or
   independent pitch timing? The clock study shows these do not automatically coexist.
2. If more counterpoint is wanted, should C's pitch phase move? Compare rate and phase
   separately; the current zero-phase A/C unisons are deliberate baseline retention.
3. Should D retain Claude's full lattice, or should the slow harmonic-anchor reading
   from the earlier GPT project become its own comparison?
4. If the target is twelve pitch classes, define that projection explicitly. Modulo
   40 transposition cannot be described as ordinary octave-equivalent transposition.

The author decides these through listening. No sound audition is claimed here.
