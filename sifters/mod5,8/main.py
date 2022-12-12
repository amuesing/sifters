from music21 import *
from modules import *

def main():
    p_s = utilities.load_pickle('sifters/mod5,8/data/p_s.p')
    c = generate_score(p_s)
    c.show()
    
def generate_score(siev):
    score = stream.Score()
    part1 = stream.Part()
    part2 = stream.Part()
    binary = constructor.find_binary(siev)
    intervals = constructor.find_pitch_set(siev)
    note_length = 0.25
    id = 1
    num, den = utilities.largest_prime_factor(len(binary[0])), 2
    part1.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
    part1.insert(0, clef.PercussionClef())
    part1.append(instrument.UnpitchedPercussion())
    part1.append(tempo.MetronomeMark('fast', 144, note.Note(type='quarter')))
    part2.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
    part2.append(instrument.Piano())
    for bin in binary:
        part = generate_part1(bin, note_length, id)
        for n in part.notes:
            part1.insert(n.offset, n)
        id += 1
    for bin in binary:
        part = generate_part2(bin, intervals, note_length, id)
        for n in part.notes:
            part2.insert(n.offset, n)
        id +=1
    score.insert(0, part1)
    score.insert(0, part2)
    score.insert(0, metadata.Metadata())
    score.makeMeasures()
    score.makeRests()
    score.metadata.title = 'Sifters'
    score.metadata.composer = 'Aarib Moosey'
    return score

def generate_part1(bin, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    midi_key = [44, 60, 76, 80, 80, 80, 35, 35]
    period = len(bin)
    pattern = bin * period
    duration = note_length
    i = 0
    for bit in pattern:
        if bit == 1:
            part.insert(i * duration, note.Note(midi=midi_key[id - 1], quarterLength=duration))
        i += 1
    return part

def generate_part2(bin, intervals, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    period = len(bin)
    pattern = bin
    duration = note_length * period
    i = 0
    for bit in pattern:
        if bit == 1:
            part.insert(i * duration, note.Note(midi=60 + intervals[id-1], quarterLength=duration))
        i += 1
    return part

if __name__ == '__main__':
    main()
