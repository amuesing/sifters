from textures.texture import Texture

class Heterophonic(Texture):

    part_id = 1

    def __init__(self, source_data, database_connection):
        
        # Call superclass constructor.
        super().__init__(source_data, database_connection)

        self.part_id = Heterophonic.part_id

        Heterophonic.part_id += 1