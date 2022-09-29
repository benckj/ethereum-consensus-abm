import networkx as nx
import random as rnd
import numpy as np

class Gillespie:
    '''
    The Gillespie class combines all the different classes to a single model.
    ONce it ran, you can parse the resulting objects which are: Gillespie.nodes, Gillespie.blockchain.
    INPUT:
    - nodes         - list of Node objects
    - blockchain    - list of Block objects, contains only genesis block upon initiating
    - network       - Network object (which stores the network on which miners interact) (Not necessarily needed)
    - tau_block     - float, block gossip latency
    - tau_attest    - float, attestation gossip latency
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
        #TODO: change to 12
        self.propose_time = 8
        self.attest_time = 4

    def update_lambdas(self):
        '''Lambdas are recauculated after each time increment
        '''
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)

    def increment_time(self):
        '''Function to generate the random time increment from an exponential random distribution.
        '''
        #TODO: add a rng in the init and pass it to all random functions.
        self.increment = (-np.log(np.random.random())/self.lambda_sum).astype('float64')
        #self.time += self.increment

    def trigger_event(self):
        '''Selects the next process according to its weight and it executes the related event.
        '''
        #TODO: add RNG
        select_process = rnd.choices(population = self.processes, weights = self.lambdas, k = 1)[0]
        select_process.event()
        
    def proposal(self):
        #TODO: implement w/ commitee, slots, epochs
        pass

    def run(self, stopping_time):       
        '''Runs the model for a given stopping time.
        '''
        self.last_propose = 0
        self.last_attest = 0
        self.attestation_window = True
        
        while self.time < stopping_time:

            # self.update_lambdas()
            # generate next random increment time and save it in self.increment
            #TODO: naming is misleading. Change increment)_time() name.
            self.increment_time()
            
            # compute and execute number of proposal events vefore next random event.
            time_since_propose_event = ((self.time + self.increment) - self.last_propose)
            # execute all propose events before next random event
            for i in range(int(time_since_propose_event//self.propose_time)):
                # tell the nodes the new slot started and they have to attest
                if i == 0:
                    for n in self.nodes:
                        n.is_attesting = True
                proposer = rnd.choice(self.nodes)
                #TODO: mine->propose
                proposer.mine_block()
                self.last_propose += self.propose_time
                
            # compute and execute number of proposal events before next random event.            
            time_since_attest_event = ((self.time + self.increment) - self.last_attest)
            for i in range(int(time_since_attest_event//self.attest_time)):
                self.attestation_window = not self.attestation_window
                for n in self.nodes:
                    if n.is_attesting:
                        n.attestations.attest()
                        
                    n.is_attesting = self.attestation_window
                    self.last_attest += self.attest_time
                    
            # trigger the random event
            self.trigger_event()
            # update time
            self.time += self.increment
            print(self.time)
            
        return 


class Process:
    '''Parent class for processes. 
    INPUT:
    - tau,  float, the latency
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
    """The process to manage block gossiping
    INPUT:
    - nodes,    list of Nodes obejct
    - tau,      float, process latency
    """
    
    def __init__(self, tau, nodes):
        super().__init__(tau)
        self.nodes = nodes
        
    def event(self):
        #TODO: from nodes sampling to edges sampling
        gossiping_node = rnd.choice(self.nodes)
        listening_node = rnd.choice(list(gossiping_node.neighbors))
        gossiping_node.gossip(listening_node)
        return
    
class AttestationGossipProcess(Process):
    """The process to manage attestation gossiping
    INPUT:
    - nodes,    list of Nodes obejct
    - tau,      float, process latency
    """
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
                
class Network:
    """Object to manage the peer-to-peer network. It is a wrapper of networkx.Graph right now.
    INPUT
    - G,    a networkx.Graph object
    """
    
    import networkx as nx
    
    def __init__(self, G):
        # G is a networkx Graph
        self.network = G
        #TODO: remove lcc..
        lcc_set = max(nx.connected_components(self.network), key=len)
        self.network = self.network.subgraph(lcc_set).copy()
        
    def __len__(self):
        return len(self.network)
            
    #TODO: nodes -> peers
    def set_neighborhood(self, nodes):
        # dict map nodes in the nx.graph to nodes on p2p network
        nodes_dict = dict(zip(self.network.nodes(), nodes))
        # save peer node object as an attribute of nx node
        nx.set_node_attributes(self.network, values = nodes_dict, name='node')

        for n in self.network.nodes():
            m = self.network.nodes[n]["node"]
            # save each neighbour in the nx.Graph inside the peer node object
            for k in self.network.neighbors(n):
                m.neighbors.add(self.network.nodes[k]["node"])    

class Model:
    '''Initiates the model and builds it around the parameters given
    model.gillespie.run to run the simulation.
    All objects are contained in the class.
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
        self.nodes = [Node(blockchain = self.blockchain.copy()
                            )
                      for i in range(self.N)]

        self.network.set_neighborhood(self.nodes)

        self.gillespie = Gillespie(
                                   nodes = self.nodes,
                                   blockchain = self.blockchain,
                                   network = self.network,
                                   tau_block = self.tau_block,
                                   tau_attest = self.tau_attest,
                                  ) 

    def results(self):
        d = {"test": 1}
        return d

#TODO:         
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

'''
FUNCTIONS
'''
'''
LMD Ghost following functions handle LMD Ghost Evaluation of Blocks
'''

def find_leaves_of_blockchain(blockchain):
    parent_blocks = {b.parent for b in blockchain}
    return blockchain - parent_blocks

def lmd_ghost(blockchain, attestations, eval = simple_attestation_evaluation):
    #identify leaf blocks
    leaves = find_leaves_of_blockchain(blockchain)
    if len(leaves)==1:
        return leaves.pop()
    #invert attestations: from node:block to block:[nodes]
    inverse_attestations= {}
    for n, b in attestations.items():
        inverse_attestations[b] = inverse_attestations.get(b, []) + [n]

    attested_blocks = set(inverse_attestations.keys())

    lowest_attestation = next(iter(attested_blocks))
    for b in attested_blocks:
        if b.height < lowest_attestation.height:
            lowest_attestation = b

    cut_trees_per_leave = {b:b.predecessors - lowest_attestation.predecessors for b in leaves}
    attested_blocks = set(inverse_attestations.keys())
    attested_blocks_per_leave = {b: cut_trees_per_leave[b] & attested_blocks for b in leaves}
    attestations_per_leave = {b:[inverse_attestations[x] for x in attested_blocks_per_leave[b]] for b in leaves}

    sum_attestations_per_leave = {b:sum([eval(n) for n in attestations_per_leave[b]])}
    return max(sum_attestations_per_leave, key=attestations_per_leave.get)


def simple_attestation_evaluation(n):
    return 1

def stake_attestation_evaluation(n):
    pass

def blockchain_to_digraph(blockchain):
    leaves = find_leaves_of_blockchain(blockchain)

    d = {}
    for l in leaves:
        b=l
        while b:
            d[b]={b.parent}
            b = b.parent
            if b in d.keys():
                break

    return nx.from_dict_of_dicts(d, create_using=nx.DiGraph)

def blockchain_layout(blockchain_digraph):
    #get max height
    #get start block
    #add to left for each height 
    for b in blockchain_digraph.nodes()

    


    
                    
                

     
