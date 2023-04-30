from modules.generators import *
from modules.controllers import *

def main():
    
    midi = midi_interpreter.midiInterpreter()
    file = midi.load_midi('interludes2.mid')
    data = midi.parse_midi(file)
    data = midi.extract_chords(data)
    data = midi.midi_to_pitchclass(data)
    data = midi.extract_single_occurrences(data)
    data = midi.remove_repeated_pitchclass_values(data)
    data = midi.chords_to_sieves(data)
    data = data.sort_values(by='Start')
    data.to_csv('data/csv/dataframe.csv')
    print(data)
    # sieves = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    
    # textures = {
    #     'mono1': monophonic.Monophonic(sieves),
    #     # 'homo1': homophonic.Homophonic(sieves),
    # }
    
    # output = score.Score(**textures)
    # output.write_score()
    
if __name__ == '__main__':
    main()