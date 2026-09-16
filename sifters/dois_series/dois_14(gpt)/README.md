# dois_14(gpt)

A successor to the GPT versions that incorporates Claude's review: ordinary MIDI
exports, strong musical/readback validation, and separately selectable reference,
policy and creative comparisons. Default: `creative`.

## Render and find the MIDI

From this directory, using the existing project environment:

```bash
../../../../.venv/bin/python -B composition.py
../../../../.venv/bin/python -B composition.py --all
../../../../.venv/bin/python -B composition.py --preset reference
../../../../.venv/bin/python -B composition.py --all --dry-run
../../../../.venv/bin/python -B composition.py --all --diagnostics
../../../../.venv/bin/python -B composition.py --all --verify-only
../../../../.venv/bin/python -B -m unittest discover -s tests -v
```

The interpreter is `/Users/amuesing/Documents/Development/.venv/bin/python`.
For a new environment, install requirements.txt; Python 3.14 is the tested version.

**Ableton: browse this project's ordinary `mid/` folder.** Each preset has a named
subfolder containing four voice files, an arrangement file, a Drum Rack file and
render.json. There are no symbolic links or duplicate browser exports.

The default clip is `mid/creative/dois_14(gpt)_creative_drumrack.mid`.
Use the matching `_arrangement.mid` for four tracks. MIDI pitches 36/37/38/39 are
pads A/B/C/D. `--output-dir PATH` selects another root; preset subfolders go inside it.
Preset names also appear in filenames, so copies remain distinguishable.

## Hear one decision at a time

| Preset | What changes from the preceding row | Notes A/B/C/D |
|---|---|---|
| reference | Reproduces Claude's dois_14 note data | 108/52/108/60 |
| fixed-weather | C's accents stay fixed instead of following its shift | 108/52/108/60 |
| shared-weather | D uses the same state-to-velocity table as A/B/C | 108/52/108/60 |
| creative (default) | C uses 160 ticks; D becomes B intersect C at 240 ticks | 108/52/81/14 |

All use the complete 27-attack source, first convergence of 19200 ticks, 120 BPM,
full gates and 40/16 metadata (four bars; ten bars of 4/4; 20 seconds). Every full
rhythm pass is distinct and each accented voice has the full minimal period.
The reference presets explicitly expose historical policy discrepancies for A/B
listening; they are not all claimed to satisfy the literal shared-weather policy.
Read MUSICAL_DESIGN.md for the exact reasoning and REVIEW_RESPONSE.md for how the
review was incorporated.

## Editing

config.py's top-level musical settings define the creative preset. Its settings()
function applies the small, documented comparison overrides for the other presets.
Edit the voice definitions, weather or range there; use --dry-run first. All voices
are derived from the first source, in dependency order. The one-base restriction
implements this iteration's brief, not a limitation of sieve theory.

Augmentation expands onset cells. To slow an unchanged pattern, change its duration
or step_ticks, as C and D do here. Intersections are in integer step coordinates
before clocks are assigned, not simultaneous-onset detection in absolute time.

## Export behavior

Rendering computes and validates the complete plan, writes temporary MIDI, and reads
it back against the planned notes before replacing outputs. Existing real folders
are accepted; unrelated files are untouched. Only the selected plan's filenames and
render.json are replaced. If you rename voices/titles, old filenames are retained;
remove obsolete exports yourself after checking them.

Each file replacement is atomic, but replacing all six files is not one transaction.
Use one renderer at a time. After an interruption, rerun the render and --verify-only.
There is no generation history, lock file, symlink, fsync machinery, or second export
copy. Temporary staging folders are cleaned up. Edited files under generated names
will be overwritten; save edits under different names.

The manifest records full configuration, source and MIDI hashes, dependency versions,
resolved voices and UTC timestamp. Verification compares against the current source
and runtime: after editing source or updating dependencies, rerender. This is not
an authenticity signature or a guarantee of every DAW's import behavior.

## Validation

43 tests cover musical structure, independent reference notes, preset isolation,
unknown settings, period bounds, channel-aware MIDI readback and straightforward
file publication. The reference fixture comes from an independent byte parser of
Claude's dois_14; the creative reference separately evaluates congruences and accent
states. Historical dois_12 cases remain explicit regression inputs, not defaults.
VALIDATION.json records the last validation. Run the tests for the current result.

Form and Max/plugin work remain parked. Previous project versions are untouched.
