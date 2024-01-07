import mido
from mido import MidiFile, MidiTrack, Message

def create_midi_file(output_file):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Add notes and rests one by one
    notes = [(60, 500), (62, 500), (64, 500), ('rest', 500),
             (65, 500), (67, 500), (69, 500), (71, 500)]

    for note, duration in notes:
        if note == 'rest':
            track.append(Message('note_off', note=60, velocity=0, time=duration))
            print(f"Rest for {duration} ms")
        else:
            track.append(Message('note_on', note=note, velocity=64, time=0))
            track.append(Message('note_off', note=note, velocity=64, time=duration))
            print(f"Note {note} for {duration} ms")

    mid.save(output_file)

if __name__ == "__main__":
    create_midi_file('output.mid')
