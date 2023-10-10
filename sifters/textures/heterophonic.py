from textures.texture import Texture

class Heterophonic(Texture):

    part_id = 1

    def __init__(self, mediator):
        
        # Call superclass constructor.
        super().__init__(mediator)

        self.part_id = Heterophonic.part_id

        Heterophonic.part_id += 1