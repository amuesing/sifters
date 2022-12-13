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
    part3 = stream.Part()
    part4 = stream.Part()
    binary = initialize.binary(siev)
    intervals = initialize.pitch_set(siev)
    note_length = 0.25
    id = 1
    num, den = utilities.largest_prime_factor(len(binary[0])), 2
    part1.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
    part1.insert(0, clef.PercussionClef())
    part1.append(instrument.UnpitchedPercussion())
    part1.append(tempo.MetronomeMark('fast', 144, note.Note(type='quarter')))
    part2.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
    part2.append(instrument.Piano())
    part3.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
    part3.append(instrument.Piano())
    part4.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
    part4.append(instrument.Piano())
    for bin in binary:
        p1 = generate.part1(bin, note_length, id)
        p2 = generate.part2(bin, intervals, note_length, id)
        p3 = generate.part3(bin, intervals, note_length, id)
        p4 = generate.part4(bin, intervals, note_length, id)
        for n in p1:
            part1.insert(n.offset, n)
        for n in p2:
            part2.insert(n.offset, n)
        for n in p3:
            part3.insert(n.offset, n)
        for n in p4:
            part4.insert(n.offset, n)
        id += 1
    score.insert(0, part1)
    score.insert(0, part2)
    score.insert(0, part3)
    score.insert(0, part4)
    score.insert(0, metadata.Metadata())
    score.metadata.title = 'Sifters'
    score.metadata.composer = 'Aarib Moosey'
    return score

if __name__ == '__main__':
    main()
