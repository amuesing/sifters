from textures.texture import Texture

import pandas

class NonPitched(Texture):
    
    def __init__(self, source_data):
        
        # Call superclass constructor.
        super().__init__(source_data)
        
        # unique_midi_values = self.notes_data['Note'].unique()
        # unique_midi_values_sorted = pandas.Series(unique_midi_values).sort_values().to_list()
        # # What if there are more than 127 unique midi values?
        # int_dict = {val: i for i, val in enumerate(unique_midi_values_sorted)}
        # self.notes_data['Note'] = self.notes_data['Note'].map(int_dict)