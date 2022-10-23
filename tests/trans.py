import numpy as np

from music21.chord import Chord
from music21.stream import Part
from music21.midi.translate import streamToMidiFile


CHORD_TRANSITIONS = np.matrix([
  #              Transition Matrix: (FROM)
  # ---------------------------------------------
  #  I     ii     iii    IV      V     vi    viio   
  # ---------------------------------------------
    [0.07,  0.00,  0.00,  0.00,  0.65,  0.14,  0.86],  # | I    | 
    [0.15,  0.17,  0.00,  0.05,  0.07,  0.30,  0.00],  # | ii   | 
    [0.00,  0.00,  0.00,  0.00,  0.00,  0.37,  0.00],  # | iii  | 
    [0.19,  0.00,  0.39,  0.16,  0.14,  0.00,  0.00],  # | IV   | (TO)
    [0.52,  0.83,  0.29,  0.43,  0.00,  0.19,  0.00],  # | V    | 
    [0.07,  0.00,  0.32,  0.36,  0.14,  0.00,  0.14],  # | vi   |  
    [0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00]]) # | viio |  

CHORD_TRANSITIONS = CHORD_TRANSITIONS.T  # swap axes for simpler lookup based on current chord

TRIADS = [
  (0, 4, 7),  # I
  (2, 5, 9),  # ii
  (4, 7, 11),  # iii
  (-7, -3, 0),  # IV
  (-5, -1, 2),  # V
  (-3, 0, 4),  # vi
  (-1, 2, 5),  # viio
] 

PC_TO_NAME = ('C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B')

def midi_to_pc(midi_note):
  return midi_note % 12

def midi_to_name(midi_note):
  return PC_TO_NAME[midi_to_pc(midi_note)]

def chord_to_midi(chord_index, root_midi=60):  # chord_index is from 0 to 6
  return [root_midi + x for x in TRIADS[chord_index]]

def chord_to_names(chord_index, root_midi=60):  # chord_index is from 0 to 6
  return [midi_to_name(note) for note in chord_to_midi(chord_index, root_midi)]

num_chords = len(CHORD_TRANSITIONS)

def generate(start_chord=0, length=8):
  cur = start_chord
  chords = [cur]
  for _ in range(length - 1):
    probs = CHORD_TRANSITIONS[cur,:].tolist()[0]
    chord = np.random.choice(num_chords, p=probs)
    chords.append(chord)
    cur = chord
  return chords

chords = generate()

print(f'Generated chords: {chords}')

print(f'Note names:')
for chord in chords:
  print(chord_to_names(chord))

print(f'MIDI notes:')
for chord in chords:
  print(chord_to_midi(chord))

print('Converting to MIDI')
part = Part()
for chord in chords:
  midis = chord_to_midi(chord)

  # Repeat each chord 4 times.
  for i in range(4):  
    part.append(Chord(midis, quarterLength=1))

mf = streamToMidiFile(part)

mf.open('chords.mid', 'wb')
mf.write()
mf.close()

# https://stackoverflow.com/questions/60074713/how-do-i-use-a-markov-chain-matrix-to-generate-music