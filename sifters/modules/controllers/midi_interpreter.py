import pretty_midi
import pandas

from modules.composition import *

class midiInterpreter(Composition):
    
    @staticmethod
    def load_midi(filename):
        midi_file = pretty_midi.PrettyMIDI(f'data/midi/{filename}')
        return midi_file
        
    def parse_midi(self, midi_file):
        
        notes_data = []
        
        for instrument in midi_file.instruments:
            
            for note in instrument.notes:
                
                notes_data.append({
                        'Velocity': note.velocity,
                        'MIDI': note.pitch,
                        'Start': note.start, 
                        'End': note.end
                        })
                
        return self.group_by_start(pandas.DataFrame(notes_data))
                
if __name__ == '__main__':
    midi_file = midiInterpreter.load_midi('interludes2.mid')
    midi_data = midiInterpreter.parse_midi(midi_file)
    print(midi_data)