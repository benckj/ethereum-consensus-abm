from attestation import AttestationsData

class Node:
    '''Class for the validator.
    
    INPUT:
    - blockchain,   list of Block objects,
    '''
    counter = 0

    @classmethod
    def __update(cls):
        cls.counter += 1

    def __init__(self, blockchain):
        self.__update()
        self.id = self.counter
        
        self.local_blockchain = {blockchain[0]}
        self.global_blockchain = blockchain
        self.current_block = blockchain[0] # A Blockchain has to be initialized
        self.neighbors = set()  # set of neighbours peers on the p2p network
        self.non_gossiped_to = set()  # set of neighbour peers self.Node didn't gossip to
        
        self.attestations = AttestationsData(self)
        self.is_attesting = True
        
    #TODO: mine->propose
    def mine_block(self):
        self.current_block = Block(self, self.current_block)
        # debug
        # print('Huzza! {} was proposed.'.format(self.current_block))
        
        self.local_blockchain.add(self.current_block)
        self.global_blockchain.append(self.current_block)
        
        # tracks the neighbours self.Node didnt gossip
        self.non_gossiped_to = self.neighbors.copy()
        #TODO: remove
        self.attestations.attest() 
        return
        
    def is_gossiping(self):
        """If the set of nodes self.Node hasnt gossiped to it's empty,
        self.Node doesn't need to gossip anymore then self.is_gossiping it's False.
        """
        if self.non_gossiped_to:
            return True
        else:
            return False
    
    def update_local_blockchain(self, block):
        """When self.Node receive a new block, update the local copy of the blockchain.
        """
        while block not in self.local_blockchain:
            self.local_blockchain.add(block)
            self.attestations.check_cache(block)
            block = block.parent 
            
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

        if self.is_attesting == True:
            self.attestations.attest()

   
    def __repr__(self):
        return '<Node {}>'.format(self.id)
 