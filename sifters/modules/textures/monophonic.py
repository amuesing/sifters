from modules.textures.texture import *

class Monophonic(Texture):
    # Initialize ID value for first instance of Monophonic object.
    part_id = 1
    
    def __init__(self, sieves, grid=None, form=None):
        
        # Call superclass constructor.
        super().__init__(sieves, grid, form)
        
        # Set name of instrument.
        self.name = 'Monophonic'
        
        # Set ID value.
        self.part_id = Monophonic.part_id
        
        # Increment ID value.
        Monophonic.part_id += 1
        
        # Create a part for the instrument in the musical texture.
        self.set_notes_data()
        
        # Group notes with the same start time into a single note with the highest MIDI value.
        self.notes_data = self.group_by_start(self.notes_data)
        
        # Get the lowest MIDI note for each start time.
        self.notes_data = self.get_lowest_midi(self.notes_data)
        
        # Close the intervals by transposing all notes to the lowest octave containing the notes.
        self.notes_data = self.close_intervals(self.notes_data)
        
        # Combine consecutive MIDI values with the same start time into a single note with a longer duration.
        self.notes_data = self.combine_consecutive_midi_values(self.notes_data)
        
        # Convert lists of pitch data into scalar pitch data.
        self.notes_data = self.convert_lists_to_scalars(self.notes_data)
        
        # Move parse_pitch_data method to score
        # # Add a Pitch column to the dataframe which seperates and tracks the decimal from the MIDI column values.
        # self.notes_data = self.parse_pitch_data(self.notes_data)