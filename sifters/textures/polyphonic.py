from textures.texture import *

class Polyphonic(Texture):

    part_id = 1

    def __init__(self, source_data):
        super().__init__(source_data)

        self.name = 'Polyphonic'

        self.part_id = Polyphonic.part_id

        Polyphonic.part_id += 1

        # self.set_notes_data()

        # self.binary = source_data[0]
        # self.grid = source_data[1]
        # self.repeats = source_data[2]