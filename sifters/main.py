from modules.textures import *
from modules import *

def main():
    
    # data = dataset.Dataset('sentimental.mid')
    # print(data)
    # data = dataset.calculate_start_value(data)
    # data = dataset.extract_chords(data)
    # data = dataset.midi_to_pitch_class(data)
    # data = dataset.extract_single_occurrences(data)
    # data = dataset.chords_to_sieves(data)
    # data = dataset.sort_values(by='Start')
    # sieves = data.iloc[6:7]['Sieves'].tolist()
    # data.to_csv('data/csv/dataframe.csv')
    
    sieves = ['((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)']
    
    textures = {

        # 'np1': nonpitched.NonPitched(sieves),
        # 'np2': nonpitched.NonPitched(sieves, '2/3'),
        'mono1': monophonic.Monophonic(sieves),
        'mono2': monophonic.Monophonic(sieves, '2/3'),

    }   
    
    output = score.Score(**textures)
    
    print(output.normalized_parts_data)
    
    # Why is the Time slightly off when I combine two dataframes?
    output.combine_parts('mono1', 'mono2')
    
    output.write_midi()
    
if __name__ == '__main__':
    main()

