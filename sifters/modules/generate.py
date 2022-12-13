from music21 import *

def part1(bin, note_length, id):
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
    
def part2(bin, intervals, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    period = len(bin)
    pattern = bin * 2
    duration = note_length * (period/2)
    i = 0
    x = 0
    for bit in pattern:
        if bit == 1:
            part.insert(i * duration, note.Note(midi=60+intervals[id - 1], quarterLength=duration))
            x += 1
        i += 1
    return part

def part3(bin, intervals, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    period = len(bin)
    pattern = bin * 4
    duration = note_length * (period/4)
    i = 0
    x = 0
    for bit in pattern:
        if bit == 1:
            part.insert(i * duration, note.Note(midi=60+intervals[id - 1], quarterLength=duration))
            x += 1
        i += 1
    return part
    
def part4(bin, intervals, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    period = len(bin)
    pattern = bin
    duration = note_length * period
    i = 0
    x = 0
    for bit in pattern:
        if bit == 1:
            mid = 60 + intervals[x]
            # what if there are more events than intervals, how to cycle?
            part.insert(i * duration, note.Note(midi=mid, quarterLength=duration))
            x += 1
        i += 1
    return part