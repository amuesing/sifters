from textures.texture import Texture

import pandas

class NonPitched(Texture):

    part_id = 1
    
    def __init__(self, database_connection, binary, period):

        # Call superclass constructor.
        super().__init__(database_connection, binary, period)

        self.part_id = NonPitched.part_id

        NonPitched.part_id += 1
        
        # unique_midi_values = self.notes_data['Note'].unique()
        # unique_midi_values_sorted = pandas.Series(unique_midi_values).sort_values().to_list()
        # # What if there are more than 127 unique midi values?
        # int_dict = {val: i for i, val in enumerate(unique_midi_values_sorted)}
        # self.notes_data['Note'] = self.notes_data['Note'].map(int_dict)