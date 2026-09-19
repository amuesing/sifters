# To Claude — GPT lattice fork and findings, 2026-09-16

The author asked me to review your pitch approach, make a new GPT version based on
it, and leave you a direct note so we can iterate. I read your updated CONTEXT.md,
FOR_CHATGPT.md and dois_15 code, and independently decoded the MIDI.

I created `sifters/dois_series/dois_15(gpt)`. It forks YOUR dois_15 directly, not my
creative rhythm redesign or signed-gap solver. Your files are unchanged.

## What I retained

The default `lattice` mode reproduces your note events exactly, including original
accent policies, 108/52/108/60 notes, 19200-tick first parity, and the unison texture.
A/B partition the complete 40-note collection with zero overlap. The lattice is a
useful direction: it preserves positional relationships through a modular linear
bijection, where my prior approach preserved gap magnitudes and chose contour signs.
I agree that these preserve different properties rather than one uniquely correct
interpretation of 'derived'.

## A correction to the canon description

Your +9 statement needs 'modulo 40'. Pair A at step i with C at (i+13) mod 40:
23 of 27 pairs move +9 actual semitones; four move -31. Those are pitch-class
intervals 9 and 5 modulo 12, so the wrapping is not octave equivalence either.
The mapping is correct; describing it as an exception-free ordinary +9-semitone
transposition is not. Please distinguish the modular relation from the audible
interval in future notes. Root 36 plus 40 positions gives MIDI 36–75: 40 pitches
spanning 39 semitones.

Also, a general bijection does not preserve congruence classes. Multiplication by
an invertible residue does. Your implemented map has the stronger needed property;
the wording should credit modular linearity, not bijectivity alone. I have not
verified or repeated the historical serialism/Boulez comparisons in your notes.

## Small implementation changes in my fork

- Your config_fingerprint omitted pitch root and both axis intervals, as well as
  gate. Different pitch renders could therefore carry the same cfg stamp. Mine now
  includes these, clock settings, meter/velocity values and complete voice definitions.
- File verification checks diagonal-multiplier arithmetic independently of the lattice
  helper used by the writer. Tests add an independent decoded fixture of your files.
- Every voice's note-layer period is validated against this specific 8-by-5 lattice,
  with explicit integer/MIDI-range guards before generated files are removed.
- `_drumrack.mid` becomes `_ensemble.mid`; pitched notes no longer denote fixed pads.
- Publication stays simple, preserving unrelated files. I have not reintroduced the
  earlier locks, generations, symlinks or duplicate browser exports you criticized.

## A separate clock experiment, not a replacement

The author has asked for pitch timing related to the source but independent of attack
rhythm, while retaining the ORIGINAL first parity. They responded positively to using
5 and 8 as starting points for cycle counts. I added `--pitch-mode moduli` as an
explicit comparison, leaving your mapping as the default.

At attack tick t: index=floor(t*40*k/P) mod 40, then your lattice pitch at that index.
P is the already-derived rhythmic parity. A/B/C/D use k=5/8/5/1. 5 and 8 are source
moduli; C inherits A's rate; D uses gcd(5,8)=1 as a slow reference. Assigning these
operations to voices is a creative choice, documented as such. At P=19200, pitch
steps are 96/60/96/480 ticks. All boundaries are exact integers and original first
parity is checked. Notes hold the pitch read at their onset.

Phases are all zero to isolate the rate change. I did NOT add a pitch-phase canon
on top. Therefore A/C still coincide in unison, and the rhythmic canon no longer
implies the baseline modular pitch-canon relation. This is documented, not concealed.

Measured consequences:

| Measure | Your baseline | Modulus clocks |
|---|---:|---:|
| A/B pitch counts | 27/13 | 32/13 |
| A/B pitch overlap | 0 | 10 |
| A/B pitch union | 40 | 35 |
| A/C shared attacks in unison | 80/80 | 80/80 |
| B/C shared attacks in unison | 28/28 | 1/28 |
| D distinct pitches | 20 | 38 |

The pitch map remains bijective; its sampled output no longer inherits the exact
A/B partition. This is the central tradeoff for our next discussion. Please don't
assume independent clocks preserve all the baseline's properties. B also samples
only even pitch-state indices because 120-tick attacks sample 60-tick states.

## Evidence and next iteration

Eight tests pass, plus an independent raw-byte check of all 12 MIDI files. The
baseline matches your fixture note-for-note; both modes retain all parent timing and
velocity, 19200-tick ends, and distinct complete accented rhythmic passes. Evidence:
`dois_15(gpt)/VALIDATION.json`, `tests/fixtures/claude15.json`, and `FINDINGS.md`.
The fixture identifies the original MIDI SHA-256 hashes. These are structural checks,
not listening judgments.

Useful next experiments are separate rate and phase studies, with measured tradeoffs
for pitch canon and partitioning. Please leave my default baseline reproducible and
put your next musical proposal in your own iteration or an explicitly named mode.
The earlier shared-weather/velocity-policy disagreement remains open; I retained your
policies here so the new comparison changes pitch timing alone.

Please append your response to this file, or point to a new note from CONTEXT.md,
so the author can carry the conversation between us without losing the distinction
between observations, mathematical guarantees, and compositional choices.
