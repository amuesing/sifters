from modules.textures.texture import *

class Homophonic(Texture):
    # Initialize ID value for first instance of Homophonic object.
    part_id = 1
    
    def __init__(self, sieves, grid=None, form=None):
        
        # Call superclass constructor.
        super().__init__(sieves, grid, form)
        
        # Set name of instrument.
        self.name = 'Homophonic'
        
        # Set ID value.
        self.part_id = Homophonic.part_id
        
        # Increment ID value.
        Homophonic.part_id += 1
        
        # Create a part for the instrument in the musical texture.
        self.set_notes_data()
        
        self.notes_data = self.group_by_start(self.notes_data)
        
        # Why get lowest midi? -- What if 'get_closest_midi' instead of 'get_lowest_midi' where the closest to the last MIDI value is given
        self.notes_data = self.get_lowest_midi(self.notes_data)
        
        self.notes_data = self.close_intervals(self.notes_data)
        
        self.notes_data = self.combine_consecutive_midi_values(self.notes_data)
        
        self.notes_data = self.convert_lists_to_scalars(self.notes_data)
        
        self.notes_data = self.parse_pitch_data(self.notes_data)
        
        # Should the number of voices be consistent with the number of moduli.
        # Homophonic texture should be based on a mapping of intervals onto a Monophonic texture
        # This is most likely preferable to generating multiple 'midi_notes' DataFrames
        # What are the rules for voiceleading? How to handle intervals?
        self.notes_data.to_csv(f'Homophonic Texture {self.part_id}')