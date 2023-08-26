from textures.texture import Texture

class Polyphonic(Texture):

    part_id = 1

    name = 'poly'

    def __init__(self, source_data):
        
        super().__init__(source_data)

        self.name = Polyphonic.name

        self.part_id = Polyphonic.part_id

        Polyphonic.part_id += 1