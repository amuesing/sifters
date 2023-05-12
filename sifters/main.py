from modules.textures import *
from modules import *

def main():
    
    data = dataset.load_midi('interlude2.midi')
    data = dataset.parse_midi(data)
    data = dataset.extract_chords(data)
    # data = midi.midi_to_pitch_class(data)
    # data = midi.extract_single_occurrences(data)
    # data = midi.chords_to_sieves(data)
    # data = data.sort_values(by='Start')
    # sieves = data.iloc[6:7]['Sieves'].tolist()
    data.to_csv('data/csv/dataframe.csv')
    
    # textures = {
    #     'np1': nonpitched.NonPitched(sieves),
    #     'np2': nonpitched.NonPitched(sieves, '2/3')
    #     # 'mono1': monophonic.Monophonic(sieves),        
    #     # 'mono2': monophonic.Monophonic(sieves, '4/3'),
    #     # 'mono3': monophonic.Monophonic(sieves, '3/5')
    #     # 'homo1': homophonic.Homophonic(sieves),
    # }
    
    # output = score.Score(**textures)
    # output.combine_parts('np1', 'np2')
    # output.write_score()
    
if __name__ == '__main__':
    main()
