# dois_15(gpt)

A direct fork of Claude's dois_15 lattice implementation. Default `lattice` reproduces
Claude's note events, including rhythms, velocities, pitch and channel routing.
`moduli` is a separately rendered pitch-clock experiment. Read FINDINGS.md before
interpreting its changed pitch relationships.

From this directory, using the project's existing environment:

```bash
../../../../.venv/bin/python -B composition.py
../../../../.venv/bin/python -B composition.py --pitch-mode moduli
../../../../.venv/bin/python -B -m unittest discover -s tests -v
```

Requires Python plus mido, music21, numpy. Both modes verify their rendered files.
`--output-dir PATH` overrides the output folder for the selected mode.

Outputs are ordinary files in `mid/lattice/` and `mid/moduli/`, six per mode:
four individual prime clips, a four-track arrangement, and a one-track ensemble
with channels 1–4. Use pitched instruments. The old `_drumrack` filename has been
renamed `_ensemble`; it no longer describes fixed drum pads. Arrangement/prime
tracks retain Claude's channel 1 routing; ensemble channels separate the voices.

Both modes have 108/52/108/60 notes (328 total), finish at 19200 ticks (40 quarter
notes, 20 seconds at 120 BPM), and use Claude's original accent policies. The GPT
creative 4:3:2 rhythm redesign and gap-contour solver are not part of this fork.

## Changes beyond the comparison

- Configuration fingerprints include pitch root, axis intervals, clock mode/counts,
  gate, velocity settings, meter settings and all voice definitions. Derived runtime
  accent dictionaries are excluded so a rerender has a stable fingerprint.
- The fixed 8-by-5 lattice explicitly requires a 40-step layer. Every voice's layer
  is checked before replacing output, and the full pitch collection must fit MIDI.
- File pitch verification uses the diagonal multiplier independently of the lattice
  function used to write notes.
- Eight tests cover the Claude event fixture, all 12 outputs, exact/modular canon
  distinction, lattice validity, parity, clock boundaries, accent nonrepetition and
  fingerprints. VALIDATION.json adds independent raw-byte validation and statistics.

The renderer retains Claude's simple publication scheme: it replaces its generated
filenames and preserves other files. It is not a transactional multi-file publisher.
A failed write can require rerendering. No DAW instrument audition is claimed.

The source snapshot is Claude's dois_15 as read on 2026-09-16. Its source files and
FOR_CHATGPT.md are left unchanged. A note addressed to Claude is in the repository
root FOR_CLAUDE.md and copied here for portability.
