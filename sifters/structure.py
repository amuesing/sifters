class Structure:
    
    def __init__(self, mediator):
        
        self.changes = mediator.changes
        
        # Derive self-similar lists of integers based on the self.changes attribute.
        self.form = [[num] * len(self.changes) for num in self.changes]