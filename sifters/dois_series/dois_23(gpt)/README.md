# dois_23(gpt) — verify every occurrence of every accent state

GPT fork of Claude's dois_22. Musical configuration is unchanged: fixed pitch per
voice, stationary local-step accent fields and the shared velocity table. Pitch
experiments remain parked. Claude's folders and prior GPT versions are untouched.

## Fix

The old verifier stored only the last velocity seen for each (state,voice). A later
correct note could erase evidence of an earlier error. This verifier retains the
set of ALL velocities observed for each state and checks EVERY note against the
expected table. Errors include voice, onset, state, actual and expected velocity.
Diagnostics show the first five wrong events without limiting validation coverage.

The expected table is independently reconstructed from the configured accent fields:
weather rarity plus the maximum span rarity, ranking all states by summed rarity
and state-code tie break, with evenly spaced configured velocity bounds. Exact
rational counts avoid depending on the writer's ranking implementation. The inherited
writer is unchanged. The comparison test now also keeps every observed velocity.

## Principle VII and scope

Only config.py describes this composition. The fix contains no hardcoded sieve,
moduli, voice names/count, timing grid, pitch values or velocity table. Tests retain
Claude's alternate 7-and-5 sieve, measured period35, parity16800 and meter35/16. Invalid
accent configurations remain rejected. Weather and span residues remain explicit
composition choices; this fix neither invents them nor changes their meaning.

Parity remains the first convergence derived from raw rhythms. The accent span
justifies repeated rhythmic passes; all complete accented passes must differ. One
shared local-step weather and one shared state-to-velocity table apply. Velocity may
control timbre rather than volume. The gate and the current static-pitch workflow are
unchanged. Historical pitch studies are not revived by this version.

## Run

```bash
../../../../.venv/bin/python -B compose.py
../../../../.venv/bin/python -B -m unittest discover -s tests -v
```

Uses the existing Development/.venv environment (mido, music21, numpy). Six ordinary
MIDI files are in mid/. Their note events match dois_22; only titles/provenance differ.
Tests render into temporary folders and do not modify the supplied MIDI.

Eight tests: six inherited functional/generality cases, plus rejection of an early
wrong velocity despite later correct occurrences, and rejection of a consistently
wrong table. tests/fixtures/dois_21 is a frozen copy of Claude's prior comparison MIDI
so tests remain portable. VALIDATION.json records independent note-event comparisons.

The source fingerprint changes with this fix. Post-write checks still run AFTER
export; a failing render can already have replaced generated files. This patch closes
a verification gap, not a transactional-publication gap. No hardware audition is claimed.
