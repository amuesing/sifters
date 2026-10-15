# Verification

- All 10 tests passed, including both pitch modes, the alternative 7×5 sieve,
  invalid-mode protection, configuration immutability, and two deliberately wrong
  velocity cases rejected by the independent verifier.
- Independently decoded all 12 exported MIDI files without project code or mido.
- All 1968 note events match dois_25 exactly: onset, duration, pitch, velocity and channel.
- File format, resolution, tempo, meter and track endpoints match.
- No hanging notes, overlapping same-pitch notes, or orphan note-offs.
- Names and provenance text intentionally differ for the new version.
- DAW/instrument playback was not auditioned during this refactor.

Python source excluding tests: 1,381 lines, down from 1,677. Most of the
reduction moves historical explanation into DESIGN_HISTORY.md; the checks remain.
