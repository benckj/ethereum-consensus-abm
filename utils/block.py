
class Block:
    '''
    Class for blocks.

    INPUT:
    parent           - Block object (parent of the block)
    transactions     - Number (integer) of transactions in the block
    '''
    counter = 0
    height = 0

    @classmethod
    def __update(cls):
        cls.counter += 1

    def __init__(self, value, parent=None):
        self.id = self.counter
        self.__update()
        if value == 'genesis':
            self._parent = None
            self._tx = value
            self.attestations = []
            return
        assert parent != None
        self._parent = parent
        self._tx = value
        self.attestations = []

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value
        self.height = self._parent.height + 1

    def attest(self, node):
        self.attestations.push(node)

    def attestation_weight(self):
        return len(self.attestations)

    def total_attestation_weight(self):
        if self._parent:
            return len(self.attestations) + self._parent.total_attestation_weight()
        return 0

    def __repr__(self):
        return '<Block {} (h={}), value={}>'.format(self.id, self.height, self._tx)

    def __next__(self):
        if self._parent:
            return self._parent
        raise StopIteration