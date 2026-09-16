# Sifters code and musical-structure review

**Reviewed 10 September 2026. Current iteration: `dois_12`.**

The current composition is internally consistent and its saved MIDI agrees with the code. The main weakness is that the program's claims are broader than its guarantees: several valid-looking edits either fail, violate the first-convergence rule, or escape verification. Improving validation and verification will help you explore new material without accidentally changing the underlying musical rules.

I found reproducible correctness bugs, rather than just style issues. I did not change the repository, its MIDI, or `CONTEXT.md`. All experiments rendered into a separate audit workspace.

## Scope and evidence

I read all 60 Python files, both Markdown documents, scratch notes, the tuning definition, and the parked JavaScript file. Identical copies were compared by content hash; related iterations were read using full source and exact differences. I inspected the notation image, decoded all 772 MIDI files, read the six CSV datasets and SQLite tables, and inspected the four WAV files' format and sample data. The inventory covers 869 files outside `.git`, including incidental OS/cache files; those incidental files were inventoried rather than treated as application code.

The active version received the deepest behavioral testing. Historical generators were reviewed but not all executed: several overwrite files on import or clear output directories. The Max file received a source reading only; its development remains parked.

Validation used the existing environment at `/Users/amuesing/Documents/Development/.venv/bin/python`: Python 3.14.4, NumPy 2.4.6, music21 10.5.0, and installed mido. The default Homebrew Python lacks mido. No dependencies were installed.

Two independent approaches confirmed the baseline:

1. A fresh render, including the project's existing verification, followed by comparison against all six saved outputs.
2. A separate MIDI byte decoder, plus direct modular arithmetic and rational-number accent ranking, without using music21, mido, or the project's rendering/verification functions to calculate the expected notes.

All 60 Python sources parse successfully. All 772 MIDI files decode. Decoding successfully does not establish musical correctness for every historical output.

## What your goals imply

The latest principles in `CONTEXT.md` take precedence over superseded historical descriptions:

- Voices come from a common logical source and explicit transformations.
- A selected integer becomes an onset on the voice's own uniform time grid.
- The piece ends at the **first convergence of the raw rhythmic periods**.
- Accents justify the repetitions needed to reach that convergence. Each complete rhythm pass within a voice should differ, and the full rendered voice should have no shorter period.
- Weather is shared, with a specifically justified exception for the span accent.
- Velocity is a control signal for sound design; its meaning is not restricted to loudness.
- Full-step gates are intentional. Arrangement currently belongs in the DAW, and plugin work is parked.

These are useful, concrete design constraints. I would preserve the full velocity range, the present gate default, and the separation between generating material and arranging a track.

## Baseline: what works

| Voice | Raw layer | Unit, ticks | Passes | Notes | Full duration |
|---|---:|---:|---:|---:|---:|
| A | 40 steps | 120 | 4 | 60 | 19,200 ticks |
| B | 40 steps | 120 | 4 | 100 | 19,200 ticks |
| C | 40 steps | 120 | 4 | 60 | 19,200 ticks |
| D | 40 steps | 160 | 3 | 18 | 19,200 ticks |

The first convergence is `LCM(40 × 120, 40 × 160) = 19,200` ticks: 40 quarter notes, or 20 seconds at 120 BPM. The files declare 40/16, giving four bars; the same duration occupies ten bars in 4/4.

Confirmed from the saved files:

- A and B partition the rhythmic grid, and their full-step gates cover it continuously.
- C is A rotated by 13 steps, including the current dynamic contour.
- D's abstract binary is the intersection of A and C.
- Every voice has the expected minimal musical period; its complete 40-step passes are distinct.
- The ensemble contains 238 notes, with exact per-voice/arrangement/drum-rack correspondence.
- There are no hanging notes, orphan note-offs, same-pitch overlaps, or incorrect gate lengths in these current outputs.
- All six files use type 1 and 480 ticks per quarter note and end at 19,200 ticks.
- The current palette is eight velocities: 1, 19, 37, 55, 73, 91, 109, 127.

`required_modulus()` also passed comparison against brute-force smallest-modulus search for all 6,400 positive `(layer, target)` combinations with layer 1–40 and target 1–160. Its positive-integer arithmetic is sound; the larger problems are how its result is used and validated.

## Confirmed findings, in recommended repair order

Paths below are relative to the repository. Unless otherwise stated, `composition.py` means `sifters/dois_series/dois_12/composition.py`.

### 1. Failed rendering can erase the last good outputs

**Priority: high.** `composition.py:743–756, 868–891`.

`clear_our_outputs()` deletes all target files before their replacement tracks have been constructed, saved, or verified. Leaving unrelated filenames alone is an improvement over `dois_11`, but it does not make rendering safe on failure.

**Reproduction:** render the baseline, then set A's `root` to 128 and render again in the same audit directory. mido raises `data byte must be in range 0..127`. Before the failed run: six MIDI files. After: zero.

A failure later in rendering can instead leave a partial collection. Verification failures leave the newly written invalid collection in place. An edited file under an exact generated filename is also overwritten; the promise that edits survive applies only to other filenames.

**Fix:** validate the complete configuration and musical result before publication. Write and verify a staged collection, then publish it. Per-file atomic replacement protects individual files; publishing a versioned directory and switching a pointer/manifest gives stronger consistency for the six-file collection. Do not describe six separate replacements as an atomic batch.

### 2. Verification accepts missing music and repeated passages

**Priority: high.** `composition.py:523–537, 628–640, 675–700, 720–733`.

The rhythm reader sizes its grid from the last sounding note, not the declared clip end. The pass-distinctness check examines the in-memory velocity arrays, not the files. Ensemble comparison proves agreement among outputs, but cannot detect a shared error in all of them.

**Reproduction A:** delete A's final 40-step pass from its prime file, arrangement track, and drum-rack pad while keeping each end-of-track at 19,200. A now has **45 notes instead of 60**. `verify()` still returns `True` and prints “All checks passed.”

The shortened onset grid appears periodic, and the silent tail makes the velocity grid appear to have a long period. Neither proves that the full intended rhythm was rendered.

**Reproduction B:** keep all onsets, but replace A's fourth-pass velocities with its first-pass velocities in all three representations. Two complete passes are now identical. Verification still succeeds because the distinctness check uses the original in-memory arrays.

The same helper can reject valid data: a four-step clip containing `[1,0,0,0]` is read as the one-element layer `[1]` because its trailing rests disappear.

**Fix:** reconstruct the entire grid through the explicit end boundary, including silence. Compare every expected onset, pitch, gate, channel, and velocity to the rendered events. Perform pass-distinctness and minimal-period checks on that reconstructed data. Retain independent baseline expectations so the renderer and checker cannot agree on the same wrong implementation.

### 3. Verification misses channel errors and ensemble tempo changes

**Priority: high for note state; medium for metadata.** `composition.py:486–521, 706–733`.

`read_track()` keys active notes by pitch alone. MIDI channel is absent from both note matching and the comparison tuple. Ensemble calls discard the returned hanging-note and overlap diagnostics. Ensemble metadata checks inspect length and whole bars but do not compare tempo to the intended value.

**Reproduction A:** change every drum-rack note-off to channel 1 while leaving note-ons on channel 0. Verification succeeds. The note-offs no longer release the notes on their original channel.

**Reproduction B:** change the drum-rack tempo from 500,000 to 1,000,000 microseconds per quarter note. Verification succeeds despite the file now specifying half the intended tempo.

The checker also lacks an explicit expected file type/PPQ check and strict expected track/pad inventory. These are additional inspection findings, rather than separate tested corruptions.

**Fix:** match `(channel, pitch)`, report orphan releases and all open notes, and validate each complete ensemble. Check PPQ, expected metadata, track inventory, and the complete event multiset, not just projections onto known pads.

### 4. Equal periods are checked; the first convergence is not

**Priority: high for musical correctness.** `composition.py:789, 812, 832–833, 605–615`.

The code computes the correct raw parity point, then independently derives a potentially longer accent span and recomputes an ensemble LCM. Verification requires equal voice periods but never requires those periods to equal the original parity point. Weather is documented as static, but that property is not enforced.

**Reproduction:** add `foreign='7@0|7@1'` to `WEATHER` without changing any rhythms or units. The raw first convergence remains **19,200** ticks. Every output becomes **134,400** ticks: seven times as long, or 140 seconds at the configured tempo. **All checks pass.** The provenance still records `parity=19200`.

This is exactly the extension beyond first convergence that Principle IV disallows. A different sparse mod-7 accent happened to trigger a duplicate-pass failure, but that incidental rejection does not enforce the missing rule.

**Fix:** require each weather period to divide each relevant note-layer period if static weather is the policy. Require `rendered_voice_ticks == raw_parity_ticks` for every voice and the ensemble. Reject incompatible accent fields before writing files; do not silently choose a longer piece.

### 5. Augmentation is exposed but cannot render correctly

**Priority: medium.** `composition.py:204–219, 240–260, 812–829`; `transformations.py:15–17`.

`build_binary()` correctly stretches the source to establish the augmented note layer. `voice_rhythm()` then tiles the source to the full requested output span and stretches that whole array again. Its returned array has `factor × span` elements, while the accent arrays have `span`.

**Reproduction:** change C's relationship to `augmentation` with factor 2. Rendering raises:

```
RuntimeError: accent 'sieve5' has 320 steps, voice has 640
```

A smaller direct example turns `[1,0,0]` into the correct six-step base `[1,1,0,0,0,0]`, but requesting a 12-step rendered span returns 24 elements.

**Fix:** establish the transformed minimal layer once, then tile that validated layer to the requested span. Independently verify the transformation at layer construction. This also avoids requiring an output span to be divisible by every original source period when a derived result has a shorter period.

**Musical qualification:** `np.repeat` produces repeated onset cells: `[1,0] → [1,1,0,0]`. It does not mean “one note with doubled duration.” That behavior predates this iteration and is documented in the implementation. Name it explicitly, or define a separate time-scaling operation, before treating it as conventional durational augmentation.

### 6. The provenance fingerprint does not identify the rendered configuration

**Priority: medium.** `composition.py:156–169, 860–864`.

The hash omits output-affecting inputs, including `GATE_RATIO`, velocity bounds, `derives_from`, secondary explicit sieve expressions, duration-mapping values, and meter policy settings.

**Reproduction:** baseline fingerprint `52ab7f83` is unchanged by each of:

- `GATE_RATIO = 0.5`;
- `MIN_VELOCITY = 24`;
- `MAX_VELOCITY = 100`;
- `MAX_METER_NUMERATOR = 39`;
- changing D's source list from `['A','C']` to `['A','B']`.

These are omissions from the hash input, not cryptographic collisions. Some changes produce different music; others should produce rejected configurations. Either way, the fingerprint cannot reliably distinguish them.

The provenance text includes accent names rather than their full definitions. A hash alone cannot reconstruct omitted definitions. `date.today()` also means byte-identical reproduction holds within a date, not across dates, even when the musical content is unchanged.

**Fix:** serialize the complete effective configuration canonically, with an engine/schema version and dependency versions in a manifest. Separate a musical-content identity from a render timestamp. Include a complete configuration sidecar or sufficiently complete embedded metadata.

### 7. The claimed shared velocity mapping is different for D

**Priority: medium; changing this changes music.** `composition.py:349–379, 819`.

The function claims that a given accent combination means the same velocity everywhere, but a new profile is calculated for each voice's accent set. D's denser `span3` changes the ordering of all states, including states where no span accent fires.

| Active weather; span inactive | A/B/C mapping | D mapping |
|---|---:|---:|
| `sieve8` only | 19 | 37 |
| `sieve5` only | 37 | 55 |
| both weather accents | 73 | 109 |

These are actual computed mappings. For example, A and D both encounter the `sieve8`-only state at their respective step 14, receiving 19 and 37.

The output is valid MIDI, but a shared structural state no longer carries a shared control value. That matters when velocity controls timbre or another synthesizer parameter.

**Resolution:** either define one shared table over semantic roles such as `(sieve5, sieve8, span)` and explicitly choose the common ranking policy, or document per-grid rarity mapping as intentional. Preserving per-grid rarity and requiring identical cross-grid state values are different policies; neither should be presented as automatically delivering the other.

## Musical-policy ambiguities to resolve before changing sound

### C carries its weather with it

At `composition.py:815–817`, every accent mask is rotated for a shifted voice. Thus C is a canon of A's rhythm **and dynamics**, inherited from earlier iterations. Its weather is not phase-aligned with A and B on their shared time grid. The “one weather” check compares dictionary labels, not phase or effective masks.

The earlier canon description explicitly wanted dynamics to follow the shift. The later weather principle says every voice falls under the same field. Both readings have support in the history, so I would not silently change C. Make an explicit policy for whether a transformation acts on rhythm alone or on the entire accented phrase, and test the selected interpretation.

### D intersects step indices, not simultaneous onsets

D selects the six positions where the A and C binaries intersect, then plays those positions on the wider triplet grid. It is therefore a time-scaled expression of an abstract intersection. It is not a detector of simultaneous A/C attacks in the final timeline.

The independent baseline inspection found **zero D attacks coinciding with both A and C attacks** during the complete 19,200-tick cycle. For example, D's step 10 occurs at tick 1,600, whereas step 10 of A/C occurs at tick 1,200.

This agrees with the explicitly chosen polyrhythm. The improvement is to make the two coordinate systems clear in documentation and any future interface, rather than changing D to force temporal coincidences.

### “Derived” does not mean uniquely determined

The minimal modulus is mathematically derived; choosing that minimal solution is a policy. For example, both 32 and 160 satisfy `LCM(40,M)=160`; 32 is the smallest, not the only solution. The context's “only one” language should be corrected.

`WEATHER` and `SPAN_RESIDUE_SOURCE` are manually transcribed from the current base sieve. They are not automatically extracted when that sieve changes. Filtering the residue source to fit the derived modulus is a specific artistic derivation rule, not a general proof of independent accents, distinct passes, or feasibility.

Keep the rule if it serves the composition, but validate its consequences. A useful longer-term representation would name the source clauses once and derive both the base expression and accent definitions from those shared objects.

The context's impossibility argument for identical weather across differing units assumes the same field is evaluated in each voice's own step coordinates. It does not establish impossibility for a field defined in absolute ticks. Such a field would be a different musical model, not a drop-in correction to the current design.

## Code improvements that support exploration

**First introduce a small validated configuration model.** Enforce unique voice names, distinct pads for the current drum-rack contract, positive integer step sizes, valid velocity/pitch ranges, finite gate ratios in the supported range, and relationship arity. Currently a unary complement accepts `derives_from=['A','B']` and silently ignores B. Invalid gates are silently clamped: -1 and 0 become one tick, while 2 becomes a full step. These are poor responses to configuration mistakes in a system built around exact structure.

**Separate calculation, checking, and file publication.** A practical boundary is: configuration → resolved voice graph → minimal rhythmic layers → parity/accent plan → expected event data → validation → staged MIDI → independent readback → publication. Small immutable records would be enough. There is no need for a large framework or a rewrite in another language.

**Avoid mutating input configuration.** `main()` adds `accent_dict` into the imported configuration dictionaries, while helpers depend on module globals and wildcard imports. That makes isolated testing, repeated renders, and loading several iterations in one process harder. Bare `config` and `transformations` imports can also resolve to the wrong iteration in a shared Python session. Explicit package imports and passed configuration would make the engine reusable.

**Keep regression tests as project assets.** The current verifier is valuable, but it is not a replacement for tests that deliberately introduce failures. Start with the reproductions above, a frozen baseline event fixture, trailing-rest cases, and small exact transformation examples. Use independent expected events and readback so a common writer bug cannot pass by agreement across formats.

**Make running the current version unambiguous.** Add a dependency manifest, supported Python version, a documented environment command, and an entry point selecting `dois_12`. Add `--output-dir`, a check/dry-run mode, and a separate command that validates existing files without regenerating them. Those directly support your current DAW workflow.

**Put limits on proposed renders before allocating arrays.** LCM growth can make a small configuration edit produce enormous spans; ranking all accent states also grows as `2^accent_count`. Report proposed duration, steps, and event count early. Benchmark before optimizing: this composition is small, so caching repeated sieve evaluation is a more proportionate first step than rewriting everything for speed.

**Keep the historical iterations intact as historical material.** Several encode different musical decisions. Do not route all old compositions through a new engine without proving their event output remains unchanged. The active engine can become modular while old versions remain stable references.

## Historical and documentation findings

These do not invalidate the current `dois_12` output and should not displace repairs to the active version.

- **Earlier clips lose trailing rests.** The saved A prime files in `dois_03` and `dois_09` end at 4,680 ticks instead of their 4,800-tick rhythmic period. Their writers stop after the last note-off. Several historical arrangement tracks likewise end at their last event rather than their intended overall boundary. This is useful evidence for preserving explicit end markers and full-span tests.
- **Earlier meter logic has known incorrect fallbacks.** Several versions treat an unknown grid as sixteenths; some halve a 32nd-note numerator while also using denominator 32. These defects are substantially addressed in the current meter helpers.
- **`dois_08`'s configured eight-step density window covers nine interior cells.** Its inclusive symmetric range uses `half=4` and slices from `i-4` through `i+4`. If revived, define whether the parameter means width or radius and test the boundaries.
- **Historical scripts have side effects and path assumptions.** Amen and Starbird render at import time; some standalone configurations still use working-directory-relative output paths; several clear broad filename patterns. `CONTEXT.md`'s claim that all configurations use absolute paths is false.
- **The archived wavetable envelope fails for zero release.** `envelope[-0:]` selects the whole array, while the assigned release array has length zero. This reproduced a broadcasting error. Normalization also divides by the peak without a zero-signal guard. These are archived-only issues.
- **The archived white-noise generator does not apply its `volume=0.5` setting to white noise**, although other branches use that parameter. The saved white-noise peak is approximately 1.0. Treat this as historical behavior, not an active MIDI concern.
- **The archived composition/database paths point at `archive/data/...`**, while the present datasets live under `archive/sifters_orig/data/...`. That pipeline also retains approximate decimal timing and complicated SQL event construction. Reviving it would require a separate audit; it is not imported by `dois_12`.
- **The parked Max source is stale by design.** Its old arrays and incomplete note lifecycle should remain outside the active correctness contract until that work resumes.

The documentation needs a focused cleanup. The README calls `dois_10` current, while `CONTEXT.md` mixes snapshots from multiple iterations and gives incompatible descriptions of length, accents, and allowed repetition. Its top date is September 3 despite later entries. Some historical statements are marked superseded; others still read as current facts.

A particularly actionable example: the context says switching to 4/4 costs “one line in config.py,” but `TIME_SIGNATURE` is only a fallback. Setting it to 3/4 during an experiment left the output at 40/16 and verification passed. A deliberate meter override requires a real option in the selection logic.

Keep one short current specification, a separate chronology of decisions, and commands that generate factual render summaries. Preserve the reasoning and the user's original statements; stop duplicating current numerical tables throughout a historical log.

## Suggested next implementation sequence

1. Preserve the current event output as a baseline fixture.
2. Add the failing corruption, first-parity, augmentation, and output-preservation cases as regression tests.
3. Repair staged publication and full-file verification, including channel-aware note matching.
4. Enforce the first convergence and static-weather conditions before rendering.
5. Repair augmentation's output length and complete the configuration fingerprint.
6. Resolve the shared velocity-table and canon/weather policies explicitly before altering those sounds.
7. Extract a small reusable engine, add dependency/entry-point documentation, and clean up the current-state reference.

The highest-value improvement is confidence that a new sieve, relationship, or time grid either produces exactly the structure you asked for or fails clearly while preserving the last good render. More arrangement machinery or a plugin port can wait until that foundation is reliable.
