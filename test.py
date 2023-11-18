import mido
from mido import MidiFile, MidiTrack, Message

def create_chord_with_pitch_wheel_midi(file_path):
    # Create a MIDI file
    midi_file = MidiFile()

    # Create a track
    track = MidiTrack()
    midi_file.tracks.append(track)

    # Add note-on messages for the first chord (C major chord)
    track.append(Message('note_on', note=60, velocity=64, time=0))  # C
    track.append(Message('note_on', note=64, velocity=64, time=0))  # E
    track.append(Message('note_on', note=67, velocity=64, time=0))  # G

    # Add pitch wheel messages for pitch bend
    # Adjust the pitch values as needed (-8192 to 8191, 0 is center)
    track.append(Message('pitchwheel', pitch=500, time=0))  # Pitch wheel for the same duration as the chord

    # Add note-off messages to release the notes after some time
    track.append(Message('note_off', note=60, velocity=64, time=500))
    track.append(Message('note_off', note=64, velocity=64, time=0))
    track.append(Message('note_off', note=67, velocity=64, time=0))

    # Add note-on messages for the second chord (D minor chord)
    track.append(Message('note_on', note=62, velocity=64, time=0))  # D
    track.append(Message('note_on', note=65, velocity=64, time=0))  # F
    track.append(Message('note_on', note=69, velocity=64, time=0))  # A

    # Add pitch wheel messages for pitch bend
    track.append(Message('pitchwheel', pitch=-500, time=0))  # Pitch wheel for the same duration as the chord

    # Add note-off messages to release the notes after some time
    track.append(Message('note_off', note=62, velocity=64, time=500))
    track.append(Message('note_off', note=65, velocity=64, time=0))
    track.append(Message('note_off', note=69, velocity=64, time=0))

    # Save the MIDI file
    midi_file.save(file_path)

if __name__ == "__main__":
    # Specify the file path where you want to save the MIDI file
    midi_file_path = "chords_with_pitch_wheel.mid"

    # Create the chord MIDI file with pitch wheel messages
    create_chord_with_pitch_wheel_midi(midi_file_path)

    print(f"MIDI file '{midi_file_path}' created successfully.")
