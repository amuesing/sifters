import mido
import numpy
from mido import MidiFile, MidiTrack, Message
import music21

# Define the sieve string
siv = '''
        (3@2|7@1)
        '''

# Create a Sieve object
s = music21.sieve.Sieve(siv)

# Calculate the period
period = s.period()

# Set Z-range
s.setZRange(0, period - 1)

# Get the binary segment
binary = s.segment(segmentFormat='binary')

# Create a MIDI file
mid = MidiFile()

# Create a MIDI track
track = MidiTrack()
mid.tracks.append(track)

for i, value in enumerate(binary):
        duration = 480
        if value == 0:
                track.append(Message('note_on', note=64, velocity=0, time=0))
                track.append(Message('note_off', note=64, velocity=0, time=duration))
        else:
                track.append(Message('note_on', note=64, velocity=100, time=0))
                track.append(Message('note_off', note=64, velocity=100, time=duration))

# # Function to calculate start recursively
# def calculate_start(binary, index):
#     start = 0
#     if index < len(binary) - 1 and binary[index + 1] == 0:
#         start += 1 + calculate_start(binary, index + 1)
#     return start

# # Function to calculate end recursively
# def calculate_end(binary, index):
#     end = 1
#     if index < len(binary) - 1 and binary[index + 1] == 1:
#         end += calculate_end(binary, index + 1)
#     return end

# for i, value in enumerate(binary):
#     print(binary)
#     if value == 1:
#         start_ticks = calculate_start(binary, i) * 480
#         print(start_ticks)
#         end_ticks = calculate_end(binary, i) * 480
#         track.append(Message('note_on', note=64, velocity=64, time=start_ticks))
#         track.append(Message('note_off', note=64, velocity=64, time=end_ticks))

# Save the MIDI file
mid.save('sieve.mid')
