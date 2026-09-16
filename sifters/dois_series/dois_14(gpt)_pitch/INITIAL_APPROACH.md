> Historical design, retained for comparison. This is not the current default.

# Pitch design and musical reasoning

This version adds pitches to dois_14(gpt)'s existing rhythmic/velocity statements.
It does not change note onsets, gates, accents, tempo, or first convergence. The
creative default still has 108/52/81/14 notes and lasts 40 quarter notes (20 seconds
at 120 BPM). The complete sounding pattern includes rhythm, pitch, velocity and
note duration; its period and complete-pass distinctness are checked.

## One source, two interpretations

The complete Psappha opening sieve selects these integers within its 40-step period:

```text
0,1,3,4,6,8,10,11,12,13,14,16,17,19,20,22,23,25,27,28,29,31,33,35,36,37,38
```

For rhythm, selected step indices are attacks. For the pitch vocabulary, the same
selected integers become semitone offsets above a configurable MIDI root. There
is no major/minor scale filter, octave folding, random selection or unrelated
chord progression. Semitone interpretation and register are compositional choices,
not instructions from Xenakis. The result is a chromatic 27-pitch collection
spanning 38 semitones. That width is intentional; changing the root transposes
rather than compresses its intervals. MIDI note 60 is middle C.

The source is the opening sieve S in [Besada et al. (2021), PMC7849451](https://pmc.ncbi.nlm.nih.gov/articles/PMC7849451/).
This iteration is an original musical interpretation of that sieve, not a
historical reconstruction of Psappha's pitches.

## Pitch fields run on the grid, including rests

Let P be the ordered selected integers, N its size (27), and i the voice's step
index. An ascending field of length L chooses P[floor((i mod L)*N/L)]. This is a
monotone traversal of the collection on equal grid steps. L includes silent steps;
only the rhythmic sieve decides whether a pitch is actually sounded.

Consequences: some pitches repeat at adjacent steps, and some available pitches
are skipped at sounding onsets because their field positions fall on rests. There
is no promise that every voice plays all 27 pitches. No counter advances solely on
attacks, so rests never shift the later pitch assignments. The field wraps at its
boundary with an intentional register jump; it is not a smooth voice-leading rule.

| Voice | Pitch rule | Field length | MIDI root | Channel |
|---|---|---|---|---|
| A | Ascend through P | Base period, 40 steps | 48 | 1 |
| B | Descend through P using index N-1-floor(i*N/L) | 40 steps | 48 | 2 |
| C | Sample A's pitch field at i-13 | 40 steps | 48 | 3 |
| D | Ascend through P across its full statement | 80 steps in creative; 120 in other presets | 36 | 4 |

A exposes the ordered interval structure. B supplies contrary pitch direction
while its rhythmic complement still interlocks with A. C extends the existing
+13-step canon into pitch, independently of whether weather is fixed or shifted.
If C's root differs from A's, it is a transposed pitch canon; both default to 48.
D traverses the collection once across parity, one octave lower, giving the sparse
countervoice a slower register movement. Its register overlaps the other voices;
'lower' does not mean it is always below every note they play.

For the default creative preset, the actually sounded ranges are A/B/C: MIDI
48–85; D: MIDI 36–72. The entire available collection is 48–86 or 36–74.
Root and MIDI-range checks reject an out-of-range collection rather than folding
or clipping pitches silently.

## Pitch does not buy extra time

A/B/C's 40-step pitch fields divide their existing full spans. D's pitch field
uses the full already-established span, so it cannot ask for a later convergence.
Rhythms still run at sixteenths (A/B), eighth-note triplets (C), and eighths (D),
with 4/4/3/2 passes in the creative version. First parity stays 19200 ticks.

The rhythm engine validates accent nonrepetition BEFORE pitch is assigned. Pitch
is not allowed to conceal two identical accented rhythmic passes. The pitch layer
then checks its field closes at parity and that the combined sounding grid has no
shorter period or duplicate complete rhythmic pass. Repeated individual notes,
short phrases and the A/B/C pitch contours are allowed; their accented complete
passes remain distinct.

Velocity remains an independent synth-control dimension. A higher pitch does not
imply a stronger accent, and an active accent does not select a higher pitch.
No timing humanization, gate shortening or arrangement layer has been added.

## Comparisons and instrumentation

The four parent presets remain. `reference` now means the reference RHYTHM and
VELOCITY policy with this new pitch layer; it is not note-for-note identical to the
unpitched dois_14. Fixed-weather, shared-weather and creative retain their earlier
meanings. Their respective parent onset/duration/velocity streams are preserved
in an independent fixture and checked for every note.

Use the arrangement file with one pitched instrument per voice, or the individual
prime clips. The combined ensemble keeps MIDI channels 1–4 separate. This prevents
same-pitch note lifetimes from colliding in the MIDI file and supports multitimbral
routing; a host/instrument that merges all channels onto one sound may still treat
overlapping same-pitch notes differently. The separate-track arrangement is the
recommended starting point. Channel 10 is excluded from pitch configuration to
avoid its conventional percussion role.

These files do not choose sounds or set programs. They are deliberately not Drum
Rack exports: MIDI note now selects musical pitch rather than a different drum pad.
Octave names vary across software; MIDI numbers are the unambiguous reference.

The implementation has been verified structurally, not auditioned through the
user's instruments. Audition register and interval width first; keep the source
relationship explicit if you later choose octave mapping or scale-degree pitch.
