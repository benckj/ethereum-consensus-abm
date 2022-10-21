from utils.attestation import AttestationsData
from utils.block import Block

class Proposer(object):
    def __init__(self):
        print('initialized proposer')
    def event(self):
        # self.current_block = Block(self, self.current_block)
        # # debug
        # # print('Huzza! {} was proposed.'.format(self.current_block))
        
        # self.local_blockchain.add(self.current_block)
        # self.global_blockchain.append(self.current_block)
        
        # tracks the neighbours self.Node didnt gossip
        # self.non_gossiped_to = self.neighbors.copy()
        #TODO: remove
        # self.attestations.attest() 
        print('proposed block')


class Validator(object):
    def __init__(self):
        print('initialized validator')
    def event(self):
        print('voted block')



class Node(Proposer, Validator):
    counter = 0

    @classmethod
    def __update(cls):
        cls.counter += 1

    def __init__(self, blockchain):
        Proposer.__init__(self)
        Validator.__init__(self)
        self.__update()
        self.id = self.counter
        self._slotRole = None

        self.local_blockchain = {blockchain[0]}
        self.global_blockchain = blockchain
        self.current_block = blockchain[0] # A Blockchain has to be initialized
        self.neighbors = set()  # set of neighbours peers on the p2p network

    @property
    def slotRole(self):
        """I'm the 'x' property."""
        return self._slotRole

    @slotRole.setter
    def slotRole(self, value):
        print("role setter called")
        self._slotRole = value

    def event(self):
        if self._slotRole == 'Proposer':
            Proposer.event(self)
        elif self._slotRole == 'Validator':
            Validator.event(self)
        else:
            pass

    def __repr__(self):
        return '<Node {}>'.format(self.id)

    #TODO: gossip blocks, naming should be changed accordingly
    def gossip(self, listening_node):
        #self.non_gossiped_to.remove(listening_node)
        listening_node.listen(self)

    #TODO: listen blocks, naming should be changed accordingly
    def listen(self, gossiping_node):
        """Receive new block and update local information accordingly.
        """
        block = gossiping_node.current_block 
        self.current_block = gossiping_node.current_block
        self.update_local_blockchain(self.current_block)
        #self.current_block.nodes.add(self)
        self.non_gossiped_to = self.neighbors.copy()
        self.non_gossiped_to.remove(gossiping_node)
               
        # [Teja] handles attestation here
        # if self.is_attesting == True:
        #     self.attestations.attest()

    def update_local_blockchain(self, block):
        """When self.Node receive a new block, update the local copy of the blockchain.
        """
        while block not in self.local_blockchain:
            self.local_blockchain.add(block)
            self.attestations.check_cache(block)
            block = block.parent 