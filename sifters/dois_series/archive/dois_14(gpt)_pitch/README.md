# dois_14(gpt)_pitch

Sieve-derived pitches added to dois_14(gpt), preserving its rhythms, velocities,
gates and first parity. Default preset: creative. Read MUSICAL_DESIGN.md for the
exact mappings and reasoning.

## Run

From this directory:

```bash
../../../../.venv/bin/python -B composition.py
../../../../.venv/bin/python -B composition.py --all
../../../../.venv/bin/python -B composition.py --preset shared-weather
../../../../.venv/bin/python -B composition.py --all --dry-run
../../../../.venv/bin/python -B composition.py --all --diagnostics
../../../../.venv/bin/python -B composition.py --all --verify-only
../../../../.venv/bin/python -B -m unittest discover -s tests -v
```

Existing interpreter: /Users/amuesing/Documents/Development/.venv/bin/python.
Python 3.14 and requirements.txt dependencies are the tested environment.
--output-dir supplies a different root for the preset subfolders.

## Load into Ableton

Browse the ordinary `mid/creative/` folder. Start with
`dois_14(gpt)_pitch_creative_arrangement.mid` and use one pitched instrument per
voice. The four `_prime.mid` files are individual parts. `_ensemble.mid` contains
all voices on separate MIDI channels 1–4 for multitimbral routing.

**Do not use these as Drum Rack clips:** pitch now controls musical notes.
No sounds or program changes are embedded. Separate tracks avoid relying on a
single instrument's handling of overlapping same-pitch notes across channels.

There are six ordinary MIDI files plus render.json per preset, with no symlinks,
lock files, generation directories or duplicate browser copy. All 24 current files and 24 initial-approach comparison
files are supplied. The 'reference' folder preserves the reference rhythm and
velocity policy, but adds pitches; it is not the original unpitched MIDI.

## Pitch configuration

The new default uses signed sieve gaps for A/B, A's shifted pitch canon for C,
and pitch-class frequency anchors from D's own intersection. Direction prefers
upward motion on C-membership and downward elsewhere; the minimum necessary
reversals make each gap melody close exactly. Edit root, motion and channel in
PITCH_CONFIG. Read MUSICAL_DESIGN.md for formulas, examples and the creative reasoning.

The complete initial approach is preserved in INITIAL_APPROACH.md. Compare it with:

```bash
../../../../.venv/bin/python -B composition.py --all --initial-pitch
../../../../.venv/bin/python -B composition.py --all --initial-pitch --verify-only
```

These use mid-initial/<preset>/ and filenames containing _initial. Normal runs use
mid/<preset>/. Both sets are supplied. --output-dir overrides the root for either
mapping, so choose separate roots when making custom comparisons.

Creative still has 255 notes over 40 quarter notes: 20 seconds at 120 BPM. Existing
40/16 metadata displays four bars, equivalent to ten bars of 4/4. Pitch adds no time.
A/C now sound MIDI 48–64, B 49–60, and D 38–45.

## Implementation and verification

rhythm_engine.py is the previous pure rhythm/velocity planner, retained intact.
engine.py adds deterministic pitch fields and combined-pattern validation. Keeping
this boundary makes pitch changes independent of the established accent contract.
config.py contains musical inputs; midi_io.py handles exact event readback and
ordinary file exports; composition.py provides the CLI.

25 tests cover all parent onset/duration/velocity streams, both pitch designs, signed gap closure and optimality, independent pitch
arithmetic for the initial presets, all 24 MIDI files, pitch/channel corruption, pitch range,
canon phase, full-span closure, combined nonrepetition, manifests and ordinary exports.
The parent fixture was read directly from raw MIDI bytes. VALIDATION.json records
the last completed checks; rerun tests after edits.

Outputs are fully staged and verified before individual file replacement. Other
filenames are preserved; files under generated names are replaced. An interrupted
multi-file update may leave a mixed set: rerender and verify. Source or dependency
changes also require rerendering for current-runtime manifest verification.
The manifest is a consistency record, not an authenticity signature.

Previous projects remain untouched. Form and the Max/plugin work remain parked.
