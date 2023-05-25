from modules.textures import *
from modules import *

def main():
    
    data = dataset.load_midi('score.mid')
    data = dataset.parse_midi(data)
    # data = dataset.extract_chords(data)
    # data = dataset.midi_to_pitch_class(data)
    # data = dataset.extract_single_occurrences(data)
    # data = dataset.chords_to_sieves(data)
    # data = dataset.sort_values(by='Start')
    # sieves = data.iloc[6:7]['Sieves'].tolist()
    # data.to_csv('data/csv/dataframe.csv')
    
    # textures = {

    #     # 'np1': nonpitched.NonPitched(sieves),
    #     # 'np2': nonpitched.NonPitched(sieves, '2/3'),
    #     'mono1': monophonic.Monophonic(sieves),
    #     'mono2': monophonic.Monophonic(sieves, '2/3'),

    # }
    
    # output = score.Score(**textures)
    # output.combine_parts('mono1', 'mono2')
    # # output.combine_parts('np1', 'np2')
    # output.write_midi()
    
if __name__ == '__main__':
    main()

