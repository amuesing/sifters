import mido

# Create a new MIDI track
track = mido.MidiTrack()

# Add a note-on message for middle C (note number 60) with velocity 64 and time 0
track.append(mido.Message('note_on', note=60, velocity=64, time=0))

# Add a note-off message for middle C with velocity 64 and time 480 (corresponding to a quarter note)
track.append(mido.Message('note_off', note=60, velocity=64, time=480))

# Add a note-on message for middle C (note number 60) with velocity 64 and time 0
track.append(mido.Message('note_on', note=60, velocity=64, time=0))

# Add a note-off message for middle C with velocity 64 and time 480 (corresponding to a quarter note)
track.append(mido.Message('note_off', note=60, velocity=64, time=480))

# Add a note-on message for middle C (note number 60) with velocity 64 and time 0
track.append(mido.Message('note_on', note=60, velocity=64, time=0))

# Add a note-off message for middle C with velocity 64 and time 480 (corresponding to a quarter note)
track.append(mido.Message('note_off', note=60, velocity=64, time=480))

# Add a note-on message for a rest (note number 0) with velocity 0 and time 0 (immediately after the note-off)
track.append(mido.Message('note_on', note=0, velocity=0, time=960))

# Add end of track meta-message
track.append(mido.MetaMessage('end_of_track'))

# Create a new MIDI file
mid = mido.MidiFile()

# Add the track to the MIDI file
mid.tracks.append(track)

# Save the MIDI file
mid.save('output.mid')
