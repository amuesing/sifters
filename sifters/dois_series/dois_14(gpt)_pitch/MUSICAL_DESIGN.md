# Pitch revision: sieve gaps and pitch-class anchors

## What changed, and why

The initial approach interpreted the 27 selected positions of the 40-step source
sieve as semitone offsets, then distributed that ordered collection across 40 grid
steps. A ascended, B descended, C shifted A, and D ascended more slowly. Because
27 pitches were spread across 40 positions, adjacent attacks could repeat a pitch.
This was an interpolation choice, not a property required by the sieve. The full
initial explanation is preserved in INITIAL_APPROACH.md and its implementation
remains available with --initial-pitch.

The user requested direct derivation with more interesting pitch-class relationships.
The new default therefore uses distances between sieve attacks as melodic intervals,
rather than interpolating a pitch collection. Direction comes from another existing
sieve relationship. D turns its own pitch-class frequencies into slow harmonic anchors.
These are original compositional rules, not a reconstruction of Psappha's pitch practice.

## A and B: retain every gap, compose its direction

For each voice, list its selected positions x within its 40-step layer. A uses the
source sieve; B uses its complement. Include the circular gap from the last selected
position back to the first position in the following period:

    gap[j] = (x[j+1] - x[j]) modulo 40
    next_pitch = current_pitch + sign[j] * gap[j]

A gap is interpreted as a number of semitones. The first pitch is root + (x[0] mod 12).
The roots remain MIDI 48 for A/B/C and 36 for D. Root and semitone interpretation are
explicit musical choices; there is no external major/minor scale, random choice,
quantization, octave folding, or clipping.

For each outgoing interval, membership of the CURRENT attack position in C's shifted
sieve prefers upward motion; absence prefers downward motion. This samples C in local
step coordinates. It does not detect simultaneous notes in clock time, because C runs
at a different speed in the creative preset.

Pure membership directions need not close. The solver keeps all interval magnitudes
unchanged and finds the smallest number of direction reversals that makes their signed
sum exactly zero. Among tied solutions it preserves earlier preferred directions first
(lexicographic order of reversal bits). This deliberately favors establishing the
membership contour early and resolving it later. It can produce a broad arch, rather
than an evenly wandering line. The default needs six reversals in A and one in B.

This is a global contour choice, not a last-note correction: even the circular interval
from the last attack to the next cycle's first attack retains its sieve gap. Closure is
at the same absolute MIDI pitch, a stronger condition than pitch-class closure alone.
If a changed sieve cannot close by choosing signs, rendering fails explicitly. The
solver is limited to sieve periods of 512 steps to bound its work.

A's first cycle is:

    48 49 51 50 52 54 56 57 58 57 58 60 61 63 64 62 61 59 57 58 57 55 53 51 52 51 50

Its final 50 returns to 48 by the closing gap of two semitones. B's cycle is:

    50 53 51 49 55 52 49 52 54 58 60 58 53

B's final 53 returns to 50 by its closing gap of three. Each successive attack in
these default contours, including the circular transition, changes MIDI pitch.
Pitches recur later in the phrase; avoiding all repetition was not the goal.

A's intervals are only one or two semitones. B's complement introduces intervals up
to six semitones. Their differing melodic characters therefore follow directly from
the different gap structures. A/B are not constrained to remain consonant together:
shared derivation gives structural relationships, not a guarantee of tonal harmony.

Pitch assignment is precomputed at absolute grid positions. Rest positions hold the
preceding pitch (including across the cycle boundary); they do not sound or increment
an independent event counter. The relationship between two sounding attacks is the
sieve gap. This intentionally replaces the initial continuously advancing pitch field.

## C: keep the canon audible

C samples A's complete pitch field at i minus its configured rhythmic shift (13 here).
Its rhythm already uses that shift, so the melodic order follows A's canon as well.
In the creative preset its eighth-note-triplet grid stretches the canon relative to
A's sixteenths. C's default fixed accent field remains unshifted: pitch follows the
canon, while accents retain their independent phase policy. Different roots transpose
the canon; the defaults use the same root.

## D: turn pitch-class frequency into harmonic emphasis

For every selected position in D's OWN intersection layer, compute position modulo 12.
Count each class, then rank represented classes by descending frequency. Break ties
by the first position where that class occurs. Assign one ranked class to each complete
40-step rhythmic pass: pitch = D root + ranked class. If there are more passes than
classes, cycle through the ranking. The phrase resets at the existing parity point.

Creative D = B intersect C has positions 2, 9, 21, 24, 26, 30, 32. Its counts are:

| Relative pitch class | Count |
|---|---:|
| 2 | 2 |
| 9 | 2 |
| 0 | 1 |
| 6 | 1 |
| 8 | 1 |

There are only two passes, so they use the first two ranked classes: MIDI 38 and 45.
This is a seven-semitone change between harmonic anchors. It results from the frequency
and tie-break rules; no fifth was inserted as an independent harmony rule. Less frequent
classes remain unused in this short version. In the other three rhythm presets, D's
A-intersect-C layer instead produces pass pitches 37, 47, 36.

These are repeated full-gate notes on D's existing onsets, not a newly sustained drone.
D may repeat pitches on adjacent attacks. Its purpose is slower harmonic emphasis,
whereas A/B/C carry gap-derived melodic movement. No claim of perceptual consonance
is inferred from frequency alone.

## Form, parity, accents, and register

All parent onsets, durations, velocities, channels, tempo and meter remain unchanged.
Creative keeps 108/52/81/14 notes: 255 notes over 40 quarter notes, or 20 seconds at
120 BPM. A/B use sixteenths, C eighth-note triplets, D eighths; passes remain 4/4/3/2.

A/B/C pitch fields are 40 local steps and close within their existing spans. D's anchor
field covers its full existing span and resets at parity; its final-to-first anchor
jump is an explicit harmonic cycle, not a signed-gap melody. No extra ending note is
inserted. If clips are looped, the next cycle begins the same plan.

The rhythm engine still rejects repeated complete accented passes BEFORE adding pitch.
Pitch does not excuse those repetitions. The combined sounding pattern is also checked
for complete-pass uniqueness and shorter periods. Accents remain independent of pitch:
velocity can still control timbre without automatically following melodic height.

Creative sounding ranges are A/C 48–64, B 49–60, D 38–45. They are narrower than the
initial 38-semitone collection because the signed contour closes rather than climbing
through all selected integers. Register is not compressed after generation. The actual
pitch field must fit MIDI 0–127 or rendering fails and asks for a root adjustment.

## Audition and reproducibility

New default MIDI is in mid/<preset>/. Initial comparison MIDI is in mid-initial/<preset>/
and uses filenames containing _initial. Both folders are ordinary directories. Start
with the creative arrangement and one pitched instrument per track, or use prime clips.
The ensemble file uses separate channels 1–4 for multitimbral routing. Sounds are not
embedded; these are pitched clips, not Drum Rack mappings.

The four rhythm/velocity presets keep their meanings; reference is a historical RHYTHM
and VELOCITY comparison with pitches added. To isolate pitch design, compare the same
preset in mid and mid-initial with the same instruments and levels.

Diagnostics and render.json record the gap sizes, preferred and resolved directions,
number of reversals, attack pitches, and D's counts and selected classes. No random seed
is needed. There are 25 tests: 18 retained initial-approach/regression tests and seven
new structural/MIDI tests, including independent optimality checks and an exhaustive
small example. The files are structurally verified, not auditioned with your patches.
Whether this is more compelling to listen to should be judged in that comparison.
