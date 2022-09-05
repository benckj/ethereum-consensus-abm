import networkx as nx
import random as rnd
import numpy as np

class Gillespie:
    '''
    The Gillespie class combines all the different 
    classes to a single model. It combines processes, and structural properties into one single model.
    
    INPUT:
    - nodes         - A list of Node objects
    - blockchain    - A list of Block object, contain genesis block upon initiating
    - network       - A Network object (which stores the network on which miners interact) (Not necessarily needed)
    '''
    def __init__(self, nodes, blockchain, network, tau_block = 1, tau_attest = 0.1):
        
        self.time = 0
        self.blockchain = blockchain
        self.nodes = nodes 
        
        self.block_gossip_process = BlockGossipProcess(tau = tau_block, nodes = nodes)
        self.attestation_gossip_process = AttestationGossipProcess(tau = tau_attest, nodes = nodes)

        self.processes = [self.block_gossip_process, self.attestation_gossip_process]
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)
        
        self.network = network
        
        self.propose_time = 8
        self.attest_time = 4

    def update_lambdas(self):
        '''
        Lambdas are recauculated after each time increment
        '''
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)

    def increment_time(self):
        '''
        Function to increment time
        '''
        self.increment = (-np.log(np.random.random())/self.lambda_sum).astype('float64')
        #self.time += self.increment

    def trigger_event(self):
        '''
        Selects a process according to their weights and executes its event
        '''
        select_process = rnd.choices(population = self.processes, weights = self.lambdas, k = 1)[0]
        select_process.event()
        
    def proposal(self):
        pass

    def run(self, stoping_time):       
        '''
        Runs the model for a given stoping time
        '''
        self.last_propose = 0
        self.last_attest = 0
        self.attestation_window = True
        
        while self.time < stoping_time:

            #self.update_lambdas()
            self.increment_time()
            
            time_since_propose_event = ((self.time + self.increment) - self.last_propose)
            for i in range(int(time_since_propose_event//self.propose_time)):
                if i == 0:
                    for n in self.nodes:
                        n.is_attesing = True
                proposer = rnd.choice(self.nodes)
                proposer.mine_block()
                self.last_propose += self.propose_time
            
            time_since_attest_event = ((self.time + self.increment) - self.last_attest)
            for i in range(int(time_since_attest_event//self.attest_time)):
                self.attestation_window = not self.attestation_window
                for n in self.nodes:
                    if n.is_attesting:
                        n.attestations.attest()
                        
                    n.is_attesting = self.attestation_window
                    self.last_attest += self.attest_time
                
            self.trigger_event()
            self.time += self.increment
            print(self.time)
            
        return 

class Process:
    '''
    Parent class for processes
    '''
    def __init__(self, tau):
        self.__tau = tau
        self.__lam = 1/tau
    
    @property
    def tau(self):
        return self.__tau
    
    @tau.setter
    def tau(self, value):
        self.__tau = value
        self.__lam = 1/self.__tau
    
    @property
    def lam(self):
        return self.__lam

    def event(self):
        pass
    
class BlockGossipProcess(Process):
    
    def __init__(self, tau, nodes):
        super().__init__(tau)
        self.nodes = nodes
        
    def event(self):
        gossiping_node = rnd.choice(self.nodes)
        listening_node = rnd.choice(list(gossiping_node.neighbors))
        gossiping_node.gossip(listening_node)
        return
    
class AttestationGossipProcess(Process):

    def __init__(self, tau, nodes):
        super().__init__(tau)
        self.nodes = nodes
        
    def event(self):
        gossiping_node = rnd.choice(self.nodes)
        gossiping_node.attestations.send_attestation_message()
        return

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

#    @classmethod
#    def get_instances(cls):
#        return cls.instances

    def __init__(self, emitter = "genesis", parent = None):

        self.id = self.counter
        self.__update()

        self.children = set()
        self.parent = parent
        
        if not parent:
            self.parent = None
            self.height = 0
            self.emitter = "genesis"

        else:
            self.parent = parent
            self.height = self.parent.height + 1
            self.emitter = emitter
            parent.children.add(self)
            #self.nodes = {emitter}
            
    def __repr__(self):
        return '<Block {} (h={})>'.format(self.id, self.height)
   
class Node:
    '''
    Class for Miners
    
    INPUT:
    emitter          - List of miner objects
    parent           - Block object (parent of the block)
    transactions     - Number (integer) of transactions in the block
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
        #self.own_blocks = set() # Keeps track blocks mined by this node in order to evaluate strategy
        
        self.neighbors = set()
        self.non_gossiped_to = set()
        
        self.attestations = AttestationsData(self)
        self.is_attesting = True
        
    def mine_block(self):
        self.current_block = Block(self, self.current_block)
        print('Hurra! {} was proposed.'.format(self.current_block))
        
        self.local_blockchain.add(self.current_block)
        self.global_blockchain.append(self.current_block)
        
        #self.own_blocks.add(self.current_block)
        self.non_gossiped_to = self.neighbors.copy()
        
        self.attestations.attest() 
        return
        
    def is_gossiping(self):
        if self.non_gossiped_to:
            return True
        else:
            return False
    
    def update_local_blockchain(self, block):
        while block not in self.local_blockchain:
            self.local_blockchain.add(block)
            self.attestations.check_cache(block)
            block = block.parent           

    def gossip(self, listening_node):
        #self.non_gossiped_to.remove(listening_node)
        listening_node.listen(self)
        
    def listen(self, gossiping_node):
        block = gossiping_node.current_block 
        
        if block.height > self.current_block.height:           
                
            self.current_block = gossiping_node.current_block
            self.update_local_blockchain(self.current_block)
            #self.current_block.nodes.add(self)
            self.non_gossiped_to = self.neighbors.copy()
            self.non_gossiped_to.remove(gossiping_node)
            
            if self.is_attesting == True:
                self.attestations.attest()
   
    def __repr__(self):
        return '<Node {}>'.format(self.id)
                
class Network:
    
    import networkx as nx
    
    def __init__(self, G):
        self.network = G
        lcc_set = max(nx.connected_components(self.network), key=len)
        self.network = self.network.subgraph(lcc_set).copy()
        
    def __len__(self):
        return len(self.network)
            
    def set_neighborhood(self, nodes):
        nodes_dict = dict(zip(self.network.nodes(), nodes))
        nx.set_node_attributes(self.network, values = nodes_dict, name='node')

        for n in self.network.nodes():
            m = self.network.nodes[n]["node"]
            for k in self.network.neighbors(n):
                m.neighbors.add(self.network.nodes[k]["node"])    

class Model:
    '''
    Initiates the model and builds it around the parameters given
    model.gillespie.run to run the simulation.
    All objects are contained in the class
    '''
    def __init__(self,
                 graph = None,
                 tau_block = None,
                 tau_attest = None,
                ):
        
        self.tau_block = tau_block
        self.tau_attest = tau_attest
        
        self.blockchain = [Block()]
        self.network = Network(graph) 
        self.N = len(self.network)

        self.miners = [Node(blockchain = self.blockchain.copy()
                            )
                      for i in range(self.N)]

        self.network.set_neighborhood(self.nodes)

        self.gillespie = Gillespie(mempool = self.mempool,
                                   nodes = self.nodes,
                                   blockchain = self.blockchain,
                                   network = self.network,
                                   tau_block = self.tau_block,
                                   tau_attest = self.tau_attest,
                                  ) 
        
class Message():
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
    
    def __init__(self, node):
        self.node = node
        self.attestations = {}
        self.message_queue= set()
        self.attestations_cache = set()
         
    def attest(self):
        attestation = Attestation(self.node, self.node.current_block)
        
        self.update_attestations(attestation)
        self.add_to_message_queue(attestation)
        
    def update_attestations(self, attestation):
        '''
        Excepts an attestation object which is passed and then processed further
        '''
        if not attestation.block in self.node.local_blockchain:
            self.attestations_cache.add(attestation)
            print('where')
            return False
        
        elif attestation.attestor not in self.attestations.keys():
            self.attestations[attestation.attestor]=attestation.block
            return True
            
        elif attestation.attestor in self.attestations.keys():
            if attestation.block.id > self.attestations[attestation.attestor].id: 
                #precaution block id used instead of block slot since lmd
                self.attestations.update(attestation.as_dict())
                return True
        else:
            return False

    def add_to_message_queue(self, attestation):
        for n in self.node.neighbors:
            self.message_queue.add(Message(attestation, n))
            
    def select_attestation_message(self):
        s = rnd.choice(list(self.message_queue))
        return s
        
    def send_attestation_message(self):
        if len(self.message_queue)>0:
            message = self.select_attestation_message()
            self.message_queue.remove(message)
            print(str(self.node) + '  - sending ->  ' + str(message))
            
            message.recipient.attestations.receive_attestation(self, message)
             
    def receive_attestation(self, other, message):
        attestation = message.attestation
        
        print(str(self.node) + '   <- receiving -  ' + str(message))
        
        if self.update_attestations(attestation):
            self.add_to_message_queue(attestation)
            
    def check_cache(self, block):
        cached_blocks = set([a.block for a in self.attestations_cache])
        if block in cached_blocks:
            clear_cache = set()
            for a in self.attestations_cache:
                if a.block == block:
                    clear_cache.add(a)
                    self.attestations.update(a.as_dict())
            self.attestations_cache = self.attestations_cache - clear_cache
                    
                

     