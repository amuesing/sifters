from modules.textures.texture import Texture

import pandas

class NonPitched(Texture):
    # Initialize ID for the first instance of NonPitched object.
    part_id = 1
    
    def __init__(self, sieves, grid=None, form=None):
        super().__init__(sieves, grid, form)
        
        # Set name of the instrument as "NonPitched".
        self.name = 'NonPitched'
        
        # Set unique ID value for the instrument.
        self.part_id = NonPitched.part_id
        
        # Increment ID value for next instance.
        NonPitched.part_id += 1
        
        # Create a part for the instrument in the musical texture.
        self.set_notes_data()
        
        unique_midi_values = self.notes_data['Note'].unique()
        unique_midi_values_sorted = pandas.Series(unique_midi_values).sort_values().to_list()
        # What if there are more than 127 unique midi values?
        int_dict = {val: i for i, val in enumerate(unique_midi_values_sorted)}
        self.notes_data['Note'] = self.notes_data['Note'].map(int_dict)
        
        self.notes_data.to_csv(f'data/csv/{self.part_id}.csv')