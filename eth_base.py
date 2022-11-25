import networkx as nx
import random as rnd
import numpy as np
import logging


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

    def __init__(self, tau, edges, rng=np.random.default_rng()):
        self.edges = edges
        self.num_edges = len(edges)

        super().__init__((tau/self.num_edges))
        self.rng = rng

    def event(self):
        gossiping_node, listening_node = self.rng.choice(self.edges)
        gossiping_node.gossip(listening_node)
        return


class AttestationGossipProcess(BlockGossipProcess):
    def __init__(self, tau, edges, rng=np.random.default_rng()):
        super().__init__(tau, edges, rng)

    def event(self):
        gossiping_node, listening_node = self.rng.choice(self.edges)
        listening_node.receive_attestations(gossiping_node.attestations.copy())
        return


class FixedTimeEvent():
    def __init__(self, interval, time=0, offset=0, rng=None):
        if not interval >= 0:
            raise ValueError("Interval must be positive")
        self.rng = rng

        self.offset = offset
        self.interval = interval

        self.last_event = None
        self.next_event = time + self.offset

        self.counter = 0

    def trigger(self, next_time):
        while next_time > self.next_event:
            self.event()
            self.counter += 1
            self.next_event += self.interval

            return True
        return False

    def event(self):
        pass


class SlotBoundary(FixedTimeEvent):
    def __init__(self, interval, validators, epoch_boundary, rng=None):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.epoch_boundary = epoch_boundary

    def event(self):

        for v in self.epoch_boundary.committees[
                self.counter // self.epoch_boundary.slots_per_epoch]:
            v.is_attesting = True

        proposer = self.rng.choice(self.validators)
        proposer.propose_block()

        print('Block proposed')


class EpochBoundary(FixedTimeEvent):
    def __init__(self, interval, validators, rng=None):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.committees = []

        self.slots_per_epoch = 32
        self.v_n = len(self.validators)
        self.committee_size = int(self.v_n/self.slots_per_epoch)
        self.leftover = self.v_n - (self.committee_size * self.slots_per_epoch)

    def event(self):
        print(self.validators)
        self.rng.shuffle(self.validators)
        self.committees = [[self.validators[v+c*self.committee_size]
                            for v in range(self.committee_size)]
                           for c in range(self.slots_per_epoch)]
        j = list(range(self.slots_per_epoch))
        self.rng.shuffle(j)
        if self.leftover != 0:
            for i in range(1, self.leftover+1):
                self.committees[j[i-1]].append(self.validators[-i])

        for v in self.validators:
            v.is_attesting = False

        print('New Epoch: Committees formed')


class AttestationBoundary(FixedTimeEvent):
    def __init__(self, interval, offset, validators, rng=None):
        super().__init__(interval, offset, rng=rng)
        self.validators = validators

    def event(self):
        for v in self.validators:
            if v.is_attesting is True:
                v.issue_attestation()


class Block:
    '''
    Class for blocks.

    INPUT:
    emitter          - List of objects
    parent           - Block object (parent of the block)
    transactions     - Number (integer) of transactions in the block
    '''

    def __init__(self, emitter="genesis", parent=None, slot_no=-1):

        self.slot_no = slot_no

        self.children = set()
        self.parent = parent
        self.slot_no = slot_no

        if parent is None:
            self.parent = None
            self.height = 0
            self.emitter = "genesis"
            self.predecessors = {self}

        else:
            self.parent = parent
            self.height = self.parent.height + 1
            self.emitter = emitter
            parent.children.add(self)
            self.predecessors = parent.predecessors.copy()
            self.predecessors.add(self)

    def __repr__(self):
        return '<Block {} (h={})>'.format(self.slot_no, self.height)

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

    def __init__(self, blockchain, rng, id, model):
        self.id = id
        self.model = model

        self.rng = rng

        self.local_blockchain = {blockchain[0]}
        self.global_blockchain = blockchain

        self.neighbors = set()  # set of neighbours peers on the p2p network

        self.attestations = {}
        self.is_attesting = True

    def propose_block(self):
        head_of_chain = self.use_lmd_ghost()
        print('this is head', head_of_chain, ' by ', self)
        print('Block predecessors', head_of_chain.predecessors)

        new_block = Block(emitter=self, parent=head_of_chain,
                          slot_no=self.model.slot_boundary.counter)
        print('new_block pre', new_block.predecessors)

        self.local_blockchain.add(new_block)
        self.global_blockchain.append(new_block)
        return

    def issue_attestation(self):
        self.attestations[self] = (self.use_lmd_ghost(), self.model.slot_boundary.counter)

    def receive_attestations(self, attestations):
        attestations_old = self.attestations.copy()
        self.attestations.update(attestations)
        for k, v in attestations_old.items():
            if attestations_old[k][1] > self.attestations[k][1]:
                self.attestations[k] = attestations_old[k]

    def update_local_blockchain(self, block):
        """
        When self.Node receive a new block,
        update the local copy of the blockchain.
        """
        while block not in self.local_blockchain:
            self.local_blockchain.add(block)
            block = block.parent

    # TODO: gossip blocks, naming should be changed accordingly
    def gossip(self, listening_node):
        # self.non_gossiped_to.remove(listening_node)
        listening_node.listen(self)

    # TODO: listen blocks, naming should be changed accordingly
    def listen(self, gossiping_node):
        """Receive new block and update local information accordingly.
        """
        block = gossiping_node.use_lmd_ghost()
        self.update_local_blockchain(block)

        if self.is_attesting is True:
            self.issue_attestation()

    def use_lmd_ghost(self):
        return lmd_ghost(self.local_blockchain, self.attestations)

    def __repr__(self):
        return '<Node {}>'.format(self.id)


class Network:
    """
    Object to manage the peer-to-peer network.
    It is a wrapper of networkx.Graph right now.
    INPUT
    - G,    a networkx.Graph object
    """

    import networkx as nx

    def __init__(self, G):
        # G is a networkx Graph
        self.network = G

    def __len__(self):
        return len(self.network)

    # TODO: nodes -> peers
    def set_neighborhood(self, nodes):
        # dict map nodes in the nx.graph to nodes on p2p network
        nodes_dict = dict(zip(self.network.nodes(), nodes))
        # save peer node object as an attribute of nx node
        nx.set_node_attributes(self.network, values=nodes_dict, name='name')

        for n in self.network.nodes():
            m = self.network.nodes[n]['name']
            # save each neighbour in the nx.Graph inside the peer node object
            for k in self.network.neighbors(n):
                m.neighbors.add(self.network.nodes[k]['name'])


class Gillespie:
    '''
    The Gillespie class combines all the different classes to a single model.
    ONce it ran, you can parse the resulting objects which are:
    Gillespie.nodes, Gillespie.blockchain.
    INPUT:
    - nodes         - list of Node objects
    - blockchain    - list of Block objects, contains only genesis block upon
                      initiating
    - network       - Network object (which stores the network on which miners
                      interact) (Not necessarily needed)
    - tau_block     - float, block gossip latency
    - tau_attest    - float, attestation gossip latency
    '''

    def __init__(self,
                 processes,
                 rng=np.random.default_rng()):

        self.rng = rng

        self.processes = processes

        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)
        self.lambda_weighted = [process.lam/self.lambda_sum
                                for process in self.processes]

    def update_lambdas(self):
        '''Lambdas are recauculated after each time increment
        '''
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)
        self.lambda_weighted = [process.lam/self.lambda_sum
                                for process in self.processes]

    def calculate_time_increment(self):
        '''Function to generate the random time increment
            from an exponential random distribution.
        '''
        increment = (-np.log(self.rng.random())
                     / self.lambda_sum).astype('float64')
        return increment

    def select_event(self):
        '''Selects the next process according to its weight
        and it executes the related event.
        '''
        select_process = self.rng.choice(self.processes,
                                         p=self.lambda_weighted)
        return select_process


class Model:
    '''Initiates the model and builds it around the parameters given
    model.gillespie.run to run the simulation.
    All objects are contained in the class.
    '''

    def __init__(self,
                 graph=None,
                 tau_block=None,
                 tau_attest=None,
                 seed=None):

        self.rng = np.random.default_rng(seed)

        self.tau_block = tau_block
        self.tau_attest = tau_attest

        self.blockchain = [Block()]
        self.network = Network(graph)
        self.N = len(self.network)
        self.nodes = [Node(blockchain=self.blockchain,
                           rng=self.rng, id=i, model=self)
                      for i in range(self.N)]

        self.validators = self.nodes

        for n in self.nodes:
            n.attestations = {v: (self.blockchain[0],-1) for v in self.validators}


        self.network.set_neighborhood(self.nodes)
        self.edges = [(n, k) for n in self.nodes for k in n.neighbors]

        self.block_gossip_process = BlockGossipProcess(tau=self.tau_block,
                                                       edges=self.edges)
        self.attestation_gossip_process = AttestationGossipProcess(
            tau=self.tau_attest,
            edges=self.edges)

        self.epoch_boundary = EpochBoundary(32*12,
                                            self.validators,
                                            rng=self.rng)

        self.slot_boundary = SlotBoundary(12, self.validators,
                                          self.epoch_boundary,
                                          rng=self.rng)
        self.attestation_boundary = AttestationBoundary(12, offset=4,
                                        validators=self.validators,
                                        rng=self.rng)

        self.processes = [self.block_gossip_process,
                          self.attestation_gossip_process]
        self.fixed_events = [self.epoch_boundary, self.slot_boundary,
                             self.attestation_boundary]

        self.gillespie = Gillespie(self.processes, self.rng)
        self.time = 0

    def run(self, stoping_time):

        while self.time < stoping_time:
            # generate next random increment time and save it in self.increment
            increment = self.gillespie.calculate_time_increment()

            # loop over fixed and trigger if time passes fixed event time
            for fixed in self.fixed_events:
                fixed.trigger(self.time + increment)

            # select poisson process and trigger selected process
            next_process = self.gillespie.select_event()
            next_process.event()

            self.time += increment

    def results(self):
        d = {"test": 1}
        return d


'''
FUNCTIONS
'''
'''
LMD Ghost following functions handle LMD Ghost Evaluation of Blocks
'''


def find_leaves_of_blockchain(blockchain):
    parent_blocks = {b.parent for b in blockchain}
    return blockchain - parent_blocks


def simple_attestation_evaluation(n):
    return 1


def stake_attestation_evaluation(n):
    pass

def lmd_ghost(blockchain, attestations):

    attest = {k: v[0] for k, v in attestations.items()}
    #lowest_attested_block_height = min(b.height for b in attest.values())
    #blocks = {b for b in blockchain if b.height >= lowest_attested_block_height}
    parent_blocks = {b.parent for b in blockchain}
    leaves = blockchain - parent_blocks

    chains = {b: b.predecessors for b in leaves}

    inverse_attestations = {}
    for n, b in attest.items():
        inverse_attestations[b] = inverse_attestations.get(b, []) + [n]

    heads_of_chains = {}
    for head_of_chain, chain in chains.items():
        val = 0
        for block in chain:
            if block in inverse_attestations.keys():
                for node in inverse_attestations[block]:
                    val += 1
        heads_of_chains[head_of_chain]=val
    max_lmd_val = max(heads_of_chains.values())
    max_heads = [key for key, value in heads_of_chains.items() if value == max_lmd_val]
    #introduce tiebreaker
    sorted_max_heads = sorted(max_heads, key=lambda x: x.height, reverse=True)
    return sorted_max_heads[0]

def lmd_ghost_needs_debug_not_used(blockchain, attestations, stake=simple_attestation_evaluation):
    attestations = {k: v[0] for k, v in attestations.items()}
    leaves = find_leaves_of_blockchain(blockchain)
    if len(leaves) == 1:
        return leaves.pop()

    inverse_attestations = {}
    for n, b in attestations.items():
        inverse_attestations[b] = inverse_attestations.get(b, []) + [n]

    attested_blocks = set(inverse_attestations.keys())
    if len(attested_blocks) == 0:
        return next(iter(blockchain))

    lowest_attestation = next(iter(attested_blocks))
    for b in attested_blocks:
        if b.height < lowest_attestation.height:
            lowest_attestation = b

    if lowest_attestation.height == 0:
        cut_trees_per_leave = {b: b.predecessors.copy() for b in leaves}
    else:
        cut_trees_per_leave = {b: b.predecessors -
                               lowest_attestation.parent.predecessors
                               for b in leaves}

    attested_blocks_per_leaf = {b: cut_trees_per_leave[b] & attested_blocks
                                for b in leaves}
    attested_blocks_per_leaf = {b: n for b, n in
                                attested_blocks_per_leaf.items() if n}
    if attested_blocks_per_leaf.keys() == 1:
        return next(iter(attested_blocks_per_leaf.keys()))

    leaves_with_attestations = set(attested_blocks_per_leaf.keys())

    attestations_per_leaf = {b: [inverse_attestations[x]
                                 for x in attested_blocks_per_leaf[b]]
                             for b in leaves_with_attestations}
    attestations_per_leaf = {b: [node for nodes in n for node in nodes]
                             for b, n in attestations_per_leaf.items()}

    sum_attestations_per_leaf = {b: sum([simple_attestation_evaluation(n)
                                         for n in attestations_per_leaf[b]])
                                 for b in leaves_with_attestations}
    return max(sum_attestations_per_leaf, key=sum_attestations_per_leaf.get)


def blockchain_to_digraph(blockchain):
    leaves = find_leaves_of_blockchain(blockchain)

    d = {}
    for leaf in leaves:
        b = leaf
        while b:
            d[b] = {b.parent}
            b = b.parent
            if b in d.keys():
                break

    return nx.from_dict_of_dicts(d, create_using=nx.DiGraph)


def get_longest_chain(blockchain):
    if isinstance(blockchain, set):
        bc = list(blockchain)
    else:
        bc = blockchain.copy()
    bc.sort(key=lambda x: x.height, reverse=True)
    return bc[0]


def calculate_orphan_rate(blockchain):
    M = get_longest_chain(blockchain).predecessors
    B = blockchain
    return len(M)/len(B)


def calculate_branch_ratio(blockchain):
    if isinstance(blockchain, set):
        bc = list(blockchain)
    else:
        bc = blockchain.copy()
    M = get_longest_chain(blockchain).predecessors
    B = set(blockchain)
    Theta = B - M

    s = 0
    for b in M:
        for c in Theta:
            if b.parent == c.parent:
                s += 1

    return s/len(M)
