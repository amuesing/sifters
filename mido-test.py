import mido

# Create a MIDI file with a tempo change
mid = mido.MidiFile()
mid.ticks_per_beat = 480
track = mido.MidiTrack()
mid.tracks.append(track)

track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(69)))
track.append(mido.Message('note_off', velocity=64, time=480))
notes = [(60, 1), (62, 1), (64, 1), (65, 1)]
for note, duration in notes:
    ticks = int(duration * mid.ticks_per_beat)
    track.append(mido.Message('note_on', note=note, velocity=64, time=0))
    track.append(mido.Message('note_off', note=note, velocity=64, time=ticks))

# Change tempo to 140 BPM
track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(140), time=0))

# Add a melody at 140 BPM
notes = [(67, 1), (69, 1), (71, 1), (72, 1)]
for note, duration in notes:
    ticks = int(duration * mid.ticks_per_beat)
    track.append(mido.Message('note_on', note=note, velocity=64, time=0))
    track.append(mido.Message('note_off', note=note, velocity=64, time=ticks))

# Change tempo to 100 BPM
track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(100), time=0))

# Add a melody at 100 BPM
notes = [(55, 1), (57, 1), (59, 1), (60, 1)]
for note, duration in notes:
    ticks = int(duration * mid.ticks_per_beat)
    track.append(mido.Message('note_on', note=note, velocity=64, time=0))
    track.append(mido.Message('note_off', note=note, velocity=64, time=ticks))

print(mid)
# Save the MIDI file
mid.save('tempo_change.mid')
