# Pitch revision — 2026-09-14

- Replaced the default interpolated ascending/descending mapping with cyclic signed
  gaps from each voice's own sieve. C membership determines preferred directions;
  minimum sign reversals ensure exact pitch closure, retaining every interval size.
- Preserved C's pitch canon and independent accent policy.
- Replaced D's slow ascent with one pitch per pass, ranked from its intersection's
  pitch-class counts. Creative uses MIDI 38 then 45.
- Preserved all parent onset/duration/velocity streams and 19200-tick first parity.
- Added derivation diagnostics, actual-range validation, bounded closure solver,
  seven structural/MIDI tests and --initial-pitch comparison exports.
- Preserved the complete initial design in INITIAL_APPROACH.md and original files
  in history/initial-pitch.zip. Current rationale and limitations: MUSICAL_DESIGN.md.
- Rerendered ordinary MIDI files in mid and mid-initial; no symlinks or instrument
  assignments. Previous series projects remain unchanged.

## Initial implementation notes

# Changes from dois_14(gpt)

- Preserve the rhythm planner as rhythm_engine.py and add a separate pitch layer.
- Derive a 27-note semitone-offset collection from the complete base sieve.
- Add ascending A, descending B, shifted pitch-canon C and slower/lower D fields.
- Advance pitch by grid position, including rests; never by a hidden attack counter.
- Validate pitch-field closure and the complete pitch/velocity/rhythm pattern without
  relaxing the earlier accented-pass constraints.
- Give voices separate channels 1–4 and replace the drumrack export with ensemble.
- Verify ensemble voices by channel rather than a fixed note number.
- Add pitch settings to configuration fingerprints and resolved fields to manifests
  and diagnostics. Keep ordinary MIDI folders and all four comparison presets.
- Add 18 pitch-focused integration/regression tests, including every preset's
  parent onset/duration/velocity fixture and independent pitch arithmetic.

No rhythmic event, gate or velocity is intentionally changed. Pitch is a new
compositional interpretation, not a source correction or a sound preset.
