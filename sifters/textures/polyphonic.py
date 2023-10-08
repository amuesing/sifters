from textures.texture import Texture

class Polyphonic(Texture):

    part_id = 1

    def __init__(self, source_data, database_connection):
        
        super().__init__(source_data, database_connection)

        self.part_id = Polyphonic.part_id

        Polyphonic.part_id += 1