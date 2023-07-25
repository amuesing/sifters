from textures.texture import Texture

class Heterophonic(Texture):

    def __init__(self, source_data):

        self.binary = source_data[0]
        self.grid = source_data[1]
        self.repeats = source_data[2]