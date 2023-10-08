from textures.texture import Texture

class Polyphonic(Texture):

    part_id = 1

    def __init__(self, database_connection, binary, period):
        
        super().__init__(database_connection, binary, period)

        self.part_id = Polyphonic.part_id

        Polyphonic.part_id += 1