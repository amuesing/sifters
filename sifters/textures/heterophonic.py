from textures.texture import Texture

class Heterophonic(Texture):

    part_id = 1

    def __init__(self, database_connection, binary, period):
        
        # Call superclass constructor.
        super().__init__(database_connection, binary, period)

        self.part_id = Heterophonic.part_id

        Heterophonic.part_id += 1