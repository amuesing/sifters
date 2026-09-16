# dois_12(gpt)

A separate, hardened iteration of `dois_12`, created 11 September 2026. Default notes, velocities, gates, and timing match `dois_12` exactly: A/B/C/D have 60/100/60/18 notes, all ending at the first convergence of 19,200 ticks. The original iterations remain unchanged.

## Run

From this directory, using the existing project environment:

```bash
../../../../.venv/bin/python -B composition.py
../../../../.venv/bin/python -B composition.py --dry-run
../../../../.venv/bin/python -B composition.py --verify-only
../../../../.venv/bin/python -B -m unittest discover -s tests -v
```

The existing environment is four parents above this series directory. Alternatively:

```bash
/Users/amuesing/Documents/Development/.venv/bin/python -B composition.py
```

For a fresh environment, use Python 3.14 and install `requirements.txt`. That is the tested Python/dependency combination; no additional dependency is required for the unittest suite. The publication mechanism uses POSIX symlinks and file locking, suitable for this Mac and Linux.

`--output-dir /path/to/new-output` selects another publication path. It must be absent or already managed by this renderer. An existing real directory is rejected with its contents intact. `--dry-run` validates the musical plan without creating output files. `--verify-only` checks the existing files against the current configuration and their manifest; it does not regenerate them.

## Files

- `config.py`: voices, rhythmic units, weather, span residue policy, gate and velocity range, explicit accent policies, meter override, and resource limits.
- `composition.py`: command-line entry point. It loads this directory's modules without colliding with other iterations' `config.py` files.
- `engine.py`: configuration validation, transformations, measured periods, first-parity plan, and expected note data. No output writes.
- `transformations.py`: complement, canon shift, retrograde, union, intersection, and cell augmentation.
- `midi_io.py`: MIDI writing, channel-aware full-file verification, manifest, and publication.
- `REVIEW.md`: the original review of `dois_12`, retained as a historical audit. Its findings refer to the original code, not to this repaired variant.
- `CHANGES.md`: fixes, policy decisions, tests, and remaining limitations.
- `tests/fixtures/dois_12_notes.json`: frozen original note data decoded independently during the audit.
- `mid/`: current six MIDI files and `render.json`.

Use `mid/dois_12(gpt)_drumrack.mid` for one Drum Rack track, or `mid/dois_12(gpt)_arrangement.mid` for four tracks. The four `_prime.mid` files are exact per-voice references.

## Musical contract

All voices derive from one base sieve, in dependency order. Intersections combine integer-index patterns before each voice receives its time unit; D is not a detector of simultaneous attacks in the final timeline.

The raw rhythms determine the first parity. Shared weather must be static on each voice's minimal rhythm layer. The derived span accent must reach that parity exactly; it may not extend the piece. Every complete rhythm pass must differ dynamically, and the full rendered voice must have no smaller period. An incompatible configuration is rejected before publication.

`augmentation` expands onset cells: `[1,0]` becomes `[1,1,0,0]` at factor 2. Each resulting 1 is a fresh onset. It does not double the duration of one held note. It now transforms the minimal layer once and tiles the result correctly. Some source/residue combinations still cannot meet the musical contract; the renderer explains the failed constraint instead of changing it.

The two previously implicit accent choices are explicit:

- `ACCENT_PHASE_POLICY = 'follow_shift'` preserves the canon's shifted dynamics. A chain of canon shifts accumulates its source's shift offset. Other relationships begin their accent field at phase zero. `'fixed'` is available, but with the default sieve/residues it makes C's passes repeat and is therefore rejected.
- `VELOCITY_POLICY = 'per_grid_rarity'` preserves D's existing, different velocity table. All voices share weather **definitions**, not an identical state-to-velocity map or absolute-time field. A new common-map policy is not invented here.

Velocity remains a synth control value using 1–127. `GATE_RATIO = 1.0` retains full-step gates; choose a finite value in `(0,1]` for shorter notes. Gate lengths are quantized to at least one tick. `METER_OVERRIDE = (4,4)` explicitly selects 4/4 without changing notes; a meter that cannot contain the first parity in whole bars is rejected.

## Safe publication and provenance

`mid` is a symlink to a complete generation under `.mid-renders/`. The renderer writes a new generation, checks all six files and their manifest, and then atomically changes the symlink. A failed write, validation, or pointer replacement leaves the previous generation available. An OS lock prevents concurrent publishers targeting the same output.

Old generations are retained for recovery. Extra user files are copied into the new generation; files listed as generated in the prior manifest are replaced. An edit under an exact generated filename is replaced in the current generation, but remains in the previous generation. User edits made while a render is copying files are not synchronized; finish those edits before rendering.

Keep `.mid-renders/` with `mid` when copying this whole project, and preserve the symlink. To export MIDI to another machine or DAW, copy the actual files reached through `mid/`. Old generations are not automatically pruned.

The publication switch is atomic at the filesystem namespace level. This is not a guarantee against every hardware or power-loss failure. It also cannot make a separate application opening files across the switch observe a single snapshot; open `mid`'s resolved generation when that matters.

`render.json` contains complete configuration, ordered weather definitions, resolved accent expressions and tables, source and MIDI SHA-256 hashes, dependency versions, and a separate UTC render timestamp. MIDI metadata has no date, so identical settings and engine produce deterministic MIDI bytes across days. The full configuration fingerprint includes all configured musical inputs and the engine version; the manifest separately fingerprints actual source files.
