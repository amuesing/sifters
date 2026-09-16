# dois_13(gpt)

The complete 27-attack Psappha opening sieve, developed into four related voices on
three pulse rates. This update intentionally changes the previous music: 255 notes,
19200 ticks, 20 seconds at 120 BPM, with a fixed shared weather field and one shared
velocity table. Read MUSICAL_DESIGN.md for the source, choices and alternatives.

## Use

From this directory:

```bash
../../../../.venv/bin/python -B composition.py
../../../../.venv/bin/python -B composition.py --dry-run
../../../../.venv/bin/python -B composition.py --diagnostics
../../../../.venv/bin/python -B composition.py --verify-only
../../../../.venv/bin/python -B -m unittest discover -s tests -v
```

The project's existing interpreter is `/Users/amuesing/Documents/Development/.venv/bin/python`.
A fresh environment requires the versions in requirements.txt; Python 3.14 is tested.
Publication uses POSIX symlinks and locking (Mac/Linux).

Use `mid-files/dois_13(gpt)_drumrack.mid` for one Drum Rack track, or
`mid-files/dois_13(gpt)_arrangement.mid` for four separate tracks. The four prime files
contain identical per-voice data. Pads 36/37/38/39 correspond to A/B/C/D.

| Voice | Relationship | Unit | Passes | Notes |
|---|---|---|---|---|
| A | Complete base sieve | 120 ticks | 4 | 108 |
| B | Complement of A | 120 ticks | 4 | 52 |
| C | A shifted +13 | 160 ticks | 3 | 81 |
| D | B intersect C | 240 ticks | 2 | 14 |

All set operations are in step coordinates, before assigning clocks. The complete
statement ends at the first raw convergence; every full rhythm pass is distinct
through accents. Shared origin does not require every voice to attack at tick zero.
Weather is phase-aligned in local steps, not absolute time across unequal grids.

## Configuration and diagnostics

config.py contains the source sieve, derivations, units, weather, residue source,
velocity/phase policies, meter, tempo, gate and resource limits. Unknown settings
are rejected. GATE_RATIO=1.0 preserves full-step articulation and A/B's continuous
complementarity. MIDI velocity spans 1–127 as a sound-design control. METER_OVERRIDE
can select (4,4); default 40/16 also fits the full statement exactly.

The default shared_rarity table uses common weather rarities and the rarest derived
span as a single ensemble weight; see MUSICAL_DESIGN.md for its exact calculation.
Changing rhythm density alone cannot change it. The historical per_grid_rarity and
follow_shift options remain available for deliberate comparisons.

--diagnostics prints JSON without writing: units, raw periods, active steps, pass
counts, realized accent states, velocities and unused state codes. --dry-run validates
without writing. --verify-only checks existing MIDI and its manifest against the
current plan and runtime. --output-dir selects an absent or managed output path;
preexisting real directories are rejected with their contents intact.

## Verification and publication

The 44-test suite includes an independently evaluated complete source and expected
notes/velocities, readback of all six MIDI files, shared weather/table checks, exact
first convergence and nonrepetition, as well as the historical audit regressions.
The old 15-hit fixture tests explicitly load legacy settings; they no longer define
the default music. VALIDATION.json records the last completed validation, not a live
substitute for running the tests.

mid is a symlink into .mid-renders/. A new generation is written and verified before
the pointer switches. Identical verified generations are reused; damaged files are
replaced. Changed prior generations remain; unrelated extra files are carried forward.
Finish edits before rendering, since copying user files is not synchronized with edits.
There is no automatic history deletion. Copy actual files reached through mid/ when
exporting MIDI, or preserve both the symlink and .mid-renders/ for the whole project.

The manifest checks complete configuration, resolved voices, source and MIDI hashes,
dependency versions and timestamp format. Current-source/runtime changes require a
new render. These checks are not a historical authenticity signature. The publication
switch is atomic, but is not a promise against every power-loss or hardware failure.

## Project files and history

- engine.py: pure planning, periods, accent derivation and diagnostics.
- transformations.py: explicit step-pattern operations. Augmentation expands cells;
  a wider step_ticks is the way to slow a rhythm without adding attacks.
- midi_io.py: writing, full readback and generation publication.
- composition.py: CLI and isolated local imports.
- MUSICAL_DESIGN.md: current musical decisions and source citation.
- CHANGES.md: current changes followed by clearly marked historical entries.
- REVIEW.md: original audit of dois_12; historical, not a review of the current default.
- history/before-full-psappha.zip: source, tests and MIDI from immediately before
  this change. Extract elsewhere and use --verify-only for its exported real mid/
  directory; to render from that backup choose a new --output-dir.

Form and the parked Max patch remain outside this iteration.

## Ableton browser export (13 September 2026)

Every normal render now also writes six ordinary MIDI files to `mid-files/`.
Browse that folder in Ableton's existing sifters Place. It is not a symlink and is
not hidden. The CLI prints its exact path. A custom --output-dir X exports its
ordinary files to the sibling X-files folder. Dry-run/diagnostics/verify-only do
not export. Unrelated files are preserved. Each file replacement is atomic, but
the six-file copy is not a single transaction; `mid/` still holds the authoritative
verified generation. Retry a render if this final browser-copy step is interrupted.

This fixes confirmed browser invisibility. It does not establish that any reported
note/timing/playback problem is resolved; that requires an observed import example.
