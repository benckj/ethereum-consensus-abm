
class Block:
    '''
    Class for blocks.
    
    INPUT:
    emitter          - List of objects
    parent           - Block object (parent of the block)
    transactions     - Number (integer) of transactions in the block
    '''
    counter = 0

    @classmethod
    def __update(cls):
        cls.counter += 1

    def __init__(self, emitter = "genesis", parent = None):

        self.id = self.counter
        self.__update()

        self.children = set()
        self.parent = parent
        
        if not parent:
            self.parent = None
            self.height = 0
            self.emitter = "genesis"
            self.predecessors = {self}

        else:
            self.parent = parent
            self.height = self.parent.height + 1
            self.emitter = emitter
            parent.children.add(self)
            self.predecessors = parent.predecessor.add(self)
        
        while block:
            self.predecessors.add(block)
            block = block.parent
            
    def __repr__(self):
        return '<Block {} (h={})>'.format(self.id, self.height)
    
    def __next__(self):
        if self.parent:
            return self.parent
        else:
            raise StopIteration
