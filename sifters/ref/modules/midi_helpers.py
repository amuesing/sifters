from music21 import *

def save(stream):
    return stream.write('midi', 'data/track/generated.midi')

def play(midi_file):
    stream = converter.parse(midi_file)
    stream.show('midi')