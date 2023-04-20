from modules.generators.texture import *

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
        
        self.notes_data = self.get_lowest_midi(self.notes_data)
                
        self.notes_data.to_csv(f'Homophonic Texture {self.part_id}')