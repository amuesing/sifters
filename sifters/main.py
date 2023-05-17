from modules.textures import *
from modules import *

def main():
    
    # data = dataset.load_midi('score.mid')
    # data = dataset.parse_midi(data)
    # data = dataset.extract_chords(data)
    # data = midi.midi_to_pitch_class(data)
    # data = midi.extract_single_occurrences(data)
    # data = midi.chords_to_sieves(data)
    # data = data.sort_values(by='Start')
    # sieves = data.iloc[6:7]['Sieves'].tolist()
    # data.to_csv('data/csv/dataframe.csv')
    sieves = ['((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)']
    
    mono1 = monophonic.Monophonic(sieves)
    np1 = nonpitched.NonPitched(sieves)
    textures = {
        # 'np1': nonpitched.NonPitched(sieves),
        # 'np2': nonpitched.NonPitched(sieves, '2/3')
        'mono1': monophonic.Monophonic(sieves, '4/3'),        
        # 'mono2': monophonic.Monophonic(sieves, '4/3'),
        # 'mono3': monophonic.Monophonic(sieves, '3/5')
        # 'homo1': homophonic.Homophonic(sieves),
    }
    
    df = mono1.notes_data
    
    # df = df.apply(lambda x: x.reset_index(drop=True))
    df.to_csv('duration.csv',)

    # print(mono1.notes_data)
    # output = score.Score(**textures)
    # # output.combine_parts('np1', 'np2')
    # output.write_score()
    
if __name__ == '__main__':
    main()
