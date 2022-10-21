import random as rnd

class Message():
    """It wraps attestation with respective recipient.
    INPUTS:
    - attestation,  Attestation object
    - reciptient,   Node object
    """
    __slots__=('attestation', 'recipient')

    def __init__(self, attestation, recipient):
        self.attestation = attestation
        self.recipient = recipient
        
    def return_attestation(self):
        return self.attestation
    
    def __eq__(self, other):
        return self.attestation == other.attestation and self.recipient == other.recipient

    def __hash__(self):
        return hash((self.attestation, self.recipient))

    def __repr__(self):
        return '<Message: {} for recipient {}>'.format(str(self.attestation).strip('<>'), self.recipient.id)
        

class Attestation():
    """It wraps a block to a node. In the context of attestation, 
    the block is the attested block and the node is the attestor.
    INPUTS:
    - attestor,  Node object
    - block,     Block object
    """
    __slots__=('attestor','block')
    
    def __init__(self, attestor, block):
        self.attestor = attestor
        self.block = block
        
    def as_dict(self):
        return {self.attestor:self.block}
    
    def __eq__(self, other):
        return self.attestor == other.attestor and self.block == other.block

    def __hash__(self):
        return hash((self.attestor, self.block))

    def __repr__(self):
        return '<Attestation: Block {} by node {}>'.format(self.block.id, self.attestor.id)

    
class AttestationsData():
    """It manages and saves attestations for a node.
    INPUTS:
    - node,     a Node object
    """
    
    def __init__(self, node):
        self.node = node
        self.attestations = {}  # Node:Block
        self.message_queue= set()  # Message
        self.attestations_cache = set()  # Attestation
         
    def attest(self):
        """Create the Attestation for the current head of the chain block.
        """
        attestation = Attestation(self.node, self.node.current_block)
        
        self.update_attestations(attestation)
        self.add_to_message_queue(attestation)  # init to send it out
        
    def update_attestations(self, attestation):
        '''Excepts an attestation object which is passed and then processed further.
        INPUTS:
        - attestation,  Attestation object
        OUTPUT:
        - Bool, wheter or not the update takes place or not
        '''
        # if node doesn't know the block the attestation is about, cache it
        if not attestation.block in self.node.local_blockchain:
            self.attestations_cache.add(attestation)
            # debug
            # print('where')
            return False
        # first time node receives attestation from specific attestor
        elif attestation.attestor not in self.attestations.keys():
            self.attestations[attestation.attestor]=attestation.block
            return True
        # node updates local latest attestation of the attestor  
        elif attestation.attestor in self.attestations.keys():
            if attestation.block.id > self.attestations[attestation.attestor].id: 
                #TODO: precaution block id used instead of block slot since lmd
                #TODO: epoch is the attestation timestamp-> use epoch
                self.attestations.update(attestation.as_dict())
                return True
        else:
            return False

    def add_to_message_queue(self, attestation):
        for n in self.node.neighbors:
            self.message_queue.add(Message(attestation, n))
            
    def select_attestation_message(self):
        #TODO: add rng
        s = rnd.choice(list(self.message_queue))
        return s
        
    def send_attestation_message(self):
        if len(self.message_queue)>0:
            message = self.select_attestation_message()
            self.message_queue.remove(message)
            # debug
            # print(str(self.node) + '  - sending ->  ' + str(message))
            
            message.recipient.attestations.receive_attestation(self, message)
             
    def receive_attestation(self, other, message):
        attestation = message.attestation
        # debug
        # print(str(self.node) + '   <- receiving -  ' + str(message))
        
        if self.update_attestations(attestation):
            self.add_to_message_queue(attestation)
            
    def check_cache(self, block):
        """Manage the cache after receiving a new block.
        If the block was cached, removes all attestations related to 
        the block from the cache and update local attestations.
        When the node receive a block he alreaqdy had attestations for
        the node needs to update the cache.
        """
        # create set of blocks in the cache
        cached_blocks = set([a.block for a in self.attestations_cache])
        if block in cached_blocks:
            clear_cache = set()
            for a in self.attestations_cache:
                if a.block == block:
                    clear_cache.add(a)
                    #TODO: use update_attestations()
                    self.attestations.update(a.as_dict())
            self.attestations_cache = self.attestations_cache - clear_cache
