import pretty_midi

# Load MIDI file
midi_data = pretty_midi.PrettyMIDI('example.mid')

# Set an initial tempo for the MIDI file
initial_tempo = 120  # BPM
midi_data.estimate_tempo()

# Get the first track in the MIDI data
track = midi_data.instruments[0]

# Set the new tempo for the MIDI file
new_tempo = 140  # BPM
tempo_microseconds = pretty_midi.bpm2tempo(new_tempo)  # Convert BPM to microseconds per quarter note

# Create a ControlChange object to change the tempo
control_change = pretty_midi.ControlChange(0, 0x51, int(tempo_microseconds))

# Add the ControlChange event to the track
track.control_changes.append(control_change)

# Write the modified MIDI data to a new file
midi_data.write('example_with_tempo_change.mid')
