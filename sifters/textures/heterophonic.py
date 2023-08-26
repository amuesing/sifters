from textures.texture import Texture

class Heterophonic(Texture):

    part_id = 1

    name = f'hetero'

    def __init__(self, source_data):
        
        # Call superclass constructor.
        super().__init__(source_data)

        self.name = Heterophonic.name

        self.part_id = Heterophonic.part_id

        Heterophonic.part_id += 1