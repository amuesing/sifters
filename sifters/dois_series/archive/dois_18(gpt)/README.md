# dois_18(gpt) — additive pitch classes from the sieve lattice

GPT iteration forked from Claude's dois_17 on 2026-09-21. Claude's files and every
previous GPT iteration remain unchanged. This is the additive pitch-class reference
experiment agreed with the author, not an independent-pitch-clock experiment.

## Derivation

The source sieve provides two coprime cyclic axes: r=n mod 8, c=n mod 5.
We ask for an additive pitch-class map p=p0+a*r+b*c modulo 12 that respects each
axis's wrap. This requires 8*a=0 mod 12 and 5*b=0 mod 12. The allowed movements are
therefore a in {0,3,6,9} and b=0.

Choose the smallest positive generator of the largest available pitch-class image:
a=3, b=0. The renderer DERIVES these values from the axes using gcd(axis,12), rather
than accepting a manually selected scale. An axis of order m allows gcd(m,12) classes;
its smallest positive generator is 12/gcd(m,12), or zero for the trivial one-class image.

Default result:

    pitch class = root class + 3*(n mod 8) mod 12
    MIDI pitch  = 36 + (3*n mod 12)
    MIDI notes  = 36, 39, 42, 45
    names       = C, E-flat, F-sharp, A

Four classes emerge from the closure constraints. They were not imposed as a diminished
scale first. However, ADDITIVITY and using twelve-tone octave equivalence ARE explicit
design choices; the source sieve alone does not uniquely prescribe this system.
The default chooses positive movement 3 over reverse movement 9. The choice favors the
smallest positive generator; neither direction is uniquely demanded by the sieve.

The mod-5 axis still determines which rhythmic cells sound, but contributes no pitch-
class movement. Thus this preserves cyclic/additive structure at the expense of
information: it maps 40 positions onto four classes and is not invertible. The pitch
field repeats every four local steps. A/B's disjoint rhythm sets no longer imply
separate pitch collections. Simultaneous A/C or B/C attacks still share a pitch when
on the same clock. This is a structural reference, not a claim of richer counterpoint.

## Octave and absolute pitch

Pitch class does not specify register. For this comparison all classes are realized
in one octave above configurable PITCH_ROOT=36, preserving the previous root and
introducing no extra octave-generating system. Root and register are compositional
choices, explicitly separate from the class derivation. No pitch bends or microtonal
encoding are used. Out-of-range and non-integer roots are rejected before publication.

## Canon and parity

C remains A shifted 13 local steps. The pitch-class transposition is now 3*13 mod 12
= 3. In the one-octave realization, 20 of the 27 corresponding notes rise three
semitones and seven fall nine. Both are the SAME pitch-class interval, unlike the
older modulo-40 map's +9/-31 split. The verifier checks the predicted modulo-12
interval and reads different rhythm clocks in their respective local coordinates.

All parent onsets, durations, velocities, channels and tempo are retained. Notes per
voice: A108/B52/C108/D60, total328. Parity:19200 ticks, 40 quarter notes, 20 seconds at
120 BPM. A/B/C grids are sixteenths; D uses eighth-note triplets. Meter remains 40/16.
Every complete accented rhythmic pass remains distinct and each accented voice still
has its full-statement minimal period. The short pitch-class cycle neither extends
parity nor substitutes for the accent nonrepetition requirement.

## Run and listen

From this directory:

```bash
../../../../.venv/bin/python -B composition.py
../../../../.venv/bin/python -B -m unittest discover -s tests -v
```

Dependencies: mido, music21, numpy, in the existing Development/.venv environment.
MIDI is already rendered into ordinary mid/ files: four prime parts, a four-track
arrangement, and a single-track ensemble with channels 1–4. Use pitched instruments.
Start with dois_18(gpt)_arrangement.mid and compare against dois_17 with the same patches.
The exporter retains Claude's simple file replacement, preserving unrelated files;
post-write verification cannot recover old files after an unexpected write failure.

## Verification and provenance

Seven tests check independently derived allowed coefficients, additive closure,
maximum image size, all six MIDI files against parent timing/velocity fixtures and
independent pitch math, the canon's actual intervals, unequal rhythm clocks, root
validation, note lifetimes, and accented-pass nonrepetition. The fixture originates
from an independent raw decode of Claude's dois_15 MIDI; its timing/velocity streams
also match dois_17. Original file hashes are recorded in the fixture.

VALIDATION.json records a separate raw-byte check of the installed MIDI. The inherited
fingerprint includes all uppercase config settings, renderer source and dependencies.
Structural verification is complete; no claim is made about auditioning your instruments.

The project root FOR_CLAUDE.md includes the rationale, tradeoffs, and verified results
for Claude's next review. This four-class mapping is not a new governing limitation;
non-additive mappings remain a separate avenue if both axes should affect pitch class.
