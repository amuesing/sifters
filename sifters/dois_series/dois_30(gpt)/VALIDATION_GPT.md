# GPT validation — 2026-09-28

18 tests cover inherited musical contracts, alternative sieves, velocity tampering,
explicit settings, default-note equivalence and preservation of twelve real exports
after invalid weather or manual residues.

Independent raw MIDI decoding (no mido or project functions) compared all twelve
exports: all 1,968 note events match Claude30 in onset, duration, channel, pitch and
velocity. Meter, tempo, format, resolution and endpoints also match. No hanging notes,
orphan note-offs or same-pitch overlaps. Names and provenance intentionally differ.

No hardware audition. Direct writes remain vulnerable to interruption/disk failure.
