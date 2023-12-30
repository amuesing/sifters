from generators.matrix import Matrix

class Polyphonic(Matrix):

    part_id = 1

    def __init__(self, mediator):
        
        super().__init__(mediator)

        self.part_id = Polyphonic.part_id

        Polyphonic.part_id += 1