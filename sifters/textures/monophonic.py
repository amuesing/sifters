from textures.texture import Texture

class Monophonic(Texture):
    # Initialize ID value for first instance of Monophonic object.
    part_id = 1
    
    def __init__(self, source_data):
        
        # Call superclass constructor.
        super().__init__(source_data)
        
        # Set name of instrument.
        self.name = 'Monophonic'
        
        # Set ID value.
        self.part_id = Monophonic.part_id
        
        # Increment ID value.
        Monophonic.part_id += 1
        
        # Group notes with the same start time into a single row.
        self.notes_data = self.group_by_start(self.notes_data)
        
        # Get the lowest MIDI note for each start time.
        self.notes_data = self.get_closest_note(self.notes_data)
        
        # Convert lists of pitch data into scalar pitch data.
        self.notes_data = self.convert_lists_to_scalars(self.notes_data)
        
        # Close the intervals by transposing all notes to the lowest octave containing the notes.
        self.notes_data = self.close_intervals(self.notes_data)
        
        # Combine consecutive MIDI values into a single note with a longer duration.
        self.notes_data = self.combine_consecutive_note_values(self.notes_data)
        
        self.notes_data = self.adjust_note_range(self.notes_data)
        
        self.notes_data.to_csv(f'data/csv/.monophonic{self.part_id}.csv')