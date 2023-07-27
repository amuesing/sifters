from textures.texture import Texture

class Polyphonic(Texture):

    part_id = 1

    def __init__(self, source_data):
        super().__init__(source_data)

        self.name = 'Polyphonic'

        self.part_id = Polyphonic.part_id

        Polyphonic.part_id += 1

        self.notes_data = self.set_notes_data()