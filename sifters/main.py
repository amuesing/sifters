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
    
    textures = {

        # 'np1': nonpitched.NonPitched(sieves),
        'mono1': monophonic.Monophonic(sieves),

    }
    
    # Does it make sense to have a seperate class for this, why not just have as methods and call from main.py?
    output = render.Render(**textures)
    # output.combine_parts('np1', 'np2')
    output.render_midi()
    
if __name__ == '__main__':
    main()
