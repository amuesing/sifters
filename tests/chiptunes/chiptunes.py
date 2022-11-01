import pretty_midi, math, scipy, random, music21

from music21.note import Note
from fractions import Fraction
from collections import defaultdict
from nltk import ngrams
from pretty_midi import Instrument as Tone
from nesmdb.convert import midi_to_wav


def midi_to_string(midi_path):
  # parse the musical information stored in the midi file
  score = music21.converter.parse(
    midi_path,                     # set midi file path
    quantizePost=True,             # quantize note length
    quarterLengthDivisors=(4,3))   # set allowed note lengths
  # s will store the sequence of notes in string form
  s = ''
  # keep a record of the last time offset seen in the score
  last_offset = 0
  # iterate over each note in the score
  for n in score.flat.notes:
    # measure the time between this note and the previous
    delta = n.offset - last_offset
    # get the duration of this note
    duration = n.duration.components[0].type
    # store the time at which this note started
    last_offset = n.offset
    # if some time elapsed, add a "wait" token
    if delta: s += 'w_{} '.format(delta)
    # add tokens for each note (or each note in a chord)
    notes = [n] if isinstance(n, Note) else n.notes
    for i in notes:
      # add this keypress to the sequence
      s += 'n_{}_{} '.format(i.pitch.midi, duration)
  return s

def string_to_midi(s):
  # initialize the sequence into which we'll add notes
  stream = music21.stream.Stream()
  # keep track of the last observed time
  time = 1
  # iterate over each token in our string
  for i in s.split():
    # if the token starts with 'n' it's a note
    if i.startswith('n'):
      # identify the note and its duration
      note, duration = i.lstrip('n_').split('_')
      # create a new note object
      n = music21.note.Note(int(note))
      # specify the note's duration
      n.duration.type = duration
      # add the note to the stream
      stream.insert(time, n)
    # if the token starts with 'w' it's a wait
    elif i.startswith('w'):
      # add the wait duration to the current time
      time += float(Fraction(i.lstrip('w_')))
  # return the stream we created
  return stream

def markov(s, sequence_length=6, output_length=250):
  # train markov model
  d = defaultdict(list)
  # make a list of lists where sublists contain word sequences
  tokens = list(ngrams(s.split(), sequence_length))
  # store the map from a token to its following tokens
  for idx, i in enumerate(tokens[:-1]):
    d[i].append(tokens[idx+1])
  # sample from the markov model
  l = [random.choice(tokens)]
  while len(l) < output_length:
    l.append(random.choice(d.get(l[-1], tokens)))
  # format the result into a string
  return ' '.join([' '.join(i) for i in l])

# def midi_to_nintendo_wav(midi_path, length=None, scalar=0.3):
#   # create a list of tones and the time each is free
#   tones = [Tone(0, name=n) for n in ['p1', 'p2', 'tr', 'no']]
#   for t in tones: t.free = 0
#   # get the start and end times of each note in `midi_path`
#   score = music21.converter.parse(midi_path)
#   for n in score.flat.notes[:length]:
#     for i in [n] if isinstance(n, Note) else n.notes:
#       start = n.offset * scalar
#       end = start + (n.seconds * scalar)
#       # identify the index position of the first free tone
#       tone_index = None
#       for index, t in enumerate(tones[:3]):
#         if t.free <= start:
#           if tone_index is None: tone_index = index
#           t.free = 0
#       if tone_index is None: continue
#       tones[tone_index].free = end
#       # play the midi note using the selected tone
#       tones[tone_index].notes.append(pretty_midi.Note(
#         velocity=10,
#         pitch=i.pitch.midi,
#         start=start,
#         end=end))
#   # add drums: 1 = kick, 8 = snare, 16 = high hats
#   for i in range(math.ceil(end * 8)):
#     note = tones[3].notes.append(pretty_midi.Note(
#       velocity=10,
#       pitch=1 if (i%4) == 0 else 8 if (i%4) == 2 else 16,
#       start=(i/2 * scalar),
#       end=(i/2 * scalar) + 0.1))
#   midi = pretty_midi.PrettyMIDI(resolution=22050)
#   midi.instruments.extend(tones)
#   # store midi length, convert to binary, and then to wav
#   time_signature = pretty_midi.TimeSignature(1, 1, end)
#   midi.time_signature_changes.append(time_signature)
#   midi.write('tests/chiptunes/chiptune.midi')
#   return midi_to_wav(open('tests/chiptunes/chiptune.midi', 'rb').read())


s = midi_to_string('tests/chiptunes/interlude.midi')
# sample a new string from s then convert that string to midi
generated_midi = string_to_midi(markov(s))
# save the midi data in "generated.midi"
generated_midi.write('midi', 'tests/chiptunes/generated.midi')
# # convert our generated midi sequence to a numpy array
# wav = midi_to_nintendo_wav('tests\chiptunes\generated.midi')
# # save the numpy array as a wav file
# scipy.io.wavfile.write('tests\chiptunes\generated.wav', 44100, wav)
# generated_midi.show()

print(markov(s))

