from music21 import *
from modules import *

def generate_part(pattern, midi_key, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    part.append(instrument.UnpitchedPercussion())
    period = len(pattern)
    numerator, denominator = utilities.largest_prime_factor(period), 4
    i = 0
    if id == 1:
            part.append(tempo.MetronomeMark('fast', 144, note.Note(type='quarter')))
    for point in pattern:
        if point == 1:
            part.insert(i * note_length, note.Note(midi=midi_key, quarterLength=note_length))
        i += 1
    part.insert(0, meter.TimeSignature('{n}/{d}'.format(n=numerator, d=denominator)))
    part.insert(0, clef.PercussionClef())
    part.makeMeasures(inPlace=True)
    part.makeRests(fillGaps=True, inPlace=True)
    return part

def generate_score(siev):
    s = stream.Score()
    id = 1
    sievs = constructor.initialize(siev)
    for siv in sievs:
        pattern, midi_key, note_length = siv[0], siv[1], siv[2]
        s.insert(0, generate_part(pattern, midi_key, note_length, id))
        id += 1
    s.insert(0, metadata.Metadata())
    s.metadata.title = 'Sifters'
    s.metadata.composer = 'Aarib Moosey'
    return s

if __name__ == '__main__':
    p_s = utilities.load_pickle('data/p_s.p')
    c = generate_score(p_s)
    c.show('midi')