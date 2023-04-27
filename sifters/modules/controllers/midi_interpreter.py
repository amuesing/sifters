import pretty_midi

class midiInterpreter:
    
    def parse_midi(filename):
        
        midi_data = pretty_midi.PrettyMIDI(f'data/midi/{filename}')
        
        for instrument in midi_data.instruments:
            
            for note in instrument.notes:
                
                print('MIDI:', note.pitch, 'Start:', note.start, 'End:', note.end)
                
if __name__ == '__main__':
    midiInterpreter.parse_midi('.interlude1.mid')