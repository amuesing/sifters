import mido
import numpy
import music21

def generate_midi_clip(sieve_string, filename):
    # Create a Sieve object
    s = music21.sieve.Sieve(sieve_string)

    # Calculate the period
    period = s.period()

    # Set Z-range
    s.setZRange(0, period - 1)

    # Get the binary segment
    binary = s.segment(segmentFormat='binary')

    # Create a MIDI file
    mid = mido.MidiFile()

    # Create a MIDI track
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Create a time signature message
    numerator = period
    denominator = 4  # You can adjust this as needed
    time_signature = mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0)
    track.append(time_signature)

    # Add note events
    for i, value in enumerate(binary):
        duration = 480
        if value == 0:
            track.append(mido.Message('note_on', note=64, velocity=0, time=0))
            track.append(mido.Message('note_off', note=64, velocity=0, time=duration))
        else:
            track.append(mido.Message('note_on', note=64, velocity=100, time=0))
            track.append(mido.Message('note_off', note=64, velocity=100, time=duration))

    # Save the MIDI file
    mid.save(f'data/mid/{filename}')


sieve_string = '(2@0|4@2)'
generate_midi_clip(sieve_string, f'{sieve_string}')
