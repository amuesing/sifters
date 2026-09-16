# Fixture provenance

dois_14_notes.json: parsed directly from Claude's dois_14/mid/*_prime.mid using the
independent raw Standard MIDI File decoder from the earlier audit, not mido or the
project engine. Contains onset, duration, channel, pitch and velocity per note.

dois_12_notes.json and dois_12_settings.json: inherited explicit historical 15-hit
regression data. They do not specify the new default source or music.

The published 27-position source list and an independent modular-arithmetic and
velocity reference are in test_full_psappha.py.
