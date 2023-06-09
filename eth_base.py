"""
    copyright 2022 uzh
    This file is part of ethereum-consensus-abm.

    ethereum-consensus-abm is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ethereum-consensus-abm is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with ethereum-consensus-abm.  If not, see <http://www.gnu.org/licenses/>.
"""
import random as rnd
import logging
import networkx as nx
import numpy as np
import math


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
        """Check if current FixedTimeEvent happens before next
        random event time next_event.
        If it does, activate the event trough method event().
        """
        while next_time >= self.next_event:
            self.counter += 1
            self.event()
            self.next_event += self.interval

            return True
        return False

    def event(self):
        """Activate FixedTimeEvent effects.
        Each FixedTimeEvent has a custom event method.
        """
        pass


class LateProposal(FixedTimeEvent):
    """Block Proposal event for delayer nodes.
    Creates bugs if latency is way larger than slot time.
    """
    def __init__(self, interval, delay, offset=np.inf, rng=None):
        super().__init__(interval, offset=offset, rng=rng)
        self.proposer = None
        self.delay = delay

    def set_proposer(self, proposer):
        self.proposer = proposer

    def set_next_time(self, time):
        self.next_event = time + self.delay

    def event(self):
        self.proposer.propose_block()


class SlotBoundary(FixedTimeEvent):
    """Event to start new slot.
    - Assign slot validators.
    - Assign epoch of the slot.
    - Enable attesters.
    - Select block proposer and release slot block.
    """
    def __init__(self, interval, validators, epoch_boundary, late_proposal, rng=None):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.epoch_boundary = epoch_boundary
        self.late_proposal = late_proposal

    def event(self):

        for v in self.epoch_boundary.committees[
                self.counter % self.epoch_boundary.slots_per_epoch]:
            v.is_attesting = True

        proposer = self.rng.choice(self.validators)
        if proposer.delayer:
            self.late_proposal.set_proposer(proposer)
            self.late_proposal.set_next_time(self.next_event)
        # TODO: remove propose block, pass proposer to model.

        else:
            # if proposer is not a delayer, just propose block here
            proposer.propose_block()

        # print('Block proposed')


class EpochBoundary(FixedTimeEvent):
    def __init__(self, slot_interval, validators, slots_per_epoch, rng=None):
        super().__init__(slot_interval*slots_per_epoch, rng=rng)
        self.validators = validators
        self.committees = []

        self.slots_per_epoch = slots_per_epoch
        self.v_n = len(self.validators)
        self.committee_size = int(self.v_n/self.slots_per_epoch)
        self.leftover = self.v_n - (self.committee_size * self.slots_per_epoch)

    def event(self):
        #print(self.validators)
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

        #print('New Epoch: Committees formed')


class AttestationBoundary(FixedTimeEvent):
    def __init__(self, interval, offset, validators, rng=None):
        super().__init__(interval, offset, rng=rng)
        self.validators = validators

    def event(self):
        for v in self.validators:
            if v.is_attesting is True:
                v.issue_attestation()


class Block:
    '''Class for blocks.

    PARAMETERS:
    ------
    emitter : list
        List of objects
    parent : Block object
        Parent of the block
    transactions : integer
        Number of transactions in the block
    '''

    def __init__(self, emitter="genesis", parent=None, slot_no=0):

        self.slot_no = slot_no

        self.children = set()
        self.parent = parent

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
        self.cached_attestations = {}
        self.is_attesting = True
        self.delayer = False

    def propose_block(self):
        head_of_chain = self.use_lmd_ghost()
        #print('this is head', head_of_chain, ' by ', self)
        #print('Block predecessors', head_of_chain.predecessors)

        new_block = Block(emitter=self, parent=head_of_chain,
                          slot_no=self.model.slot_boundary.counter)
        #print('new_block pre', new_block.predecessors)

        self.local_blockchain.add(new_block)
        self.global_blockchain.append(new_block)
        return

    def issue_attestation(self):
        self.attestations[self] = (self.use_lmd_ghost(),
                                   self.model.slot_boundary.counter)

    def receive_attestations(self, attestations):
        attestations_old = self.attestations.copy()
        attestations_with_known_blocks = {}

        for k, v in attestations.items():
            # check if block is known
            if v[0] not in self.local_blockchain:
                if k in self.cached_attestations.keys():
                    # check if slot is higher of the new attestation
                    if self.cached_attestations[k][1]<v[1]:
                        self.cached_attestations[k] = v
                else:
                    self.cached_attestations[k]=v
            else:
                attestations_with_known_blocks[k]=v

        self.attestations.update(attestations_with_known_blocks)
        
        # check for whether all the attestations belong to a newer slot
        for k, v in attestations_old.items():
            if attestations_old[k][1] > self.attestations[k][1]:
                self.attestations[k] = attestations_old[k]

    def check_cached_attestations(self):
        _cached_attestations = self.cached_attestations.copy()
        for k,v in _cached_attestations.items():
            if v[0] in self.local_blockchain:
                # delete from cache
                _ = self.cached_attestations.pop(k, 'None')
                #check if other attest from validator
                if k in self.attestations.keys():
                    # check issuing slot
                    if self.attestations[k][1]<v[1]:
                        self.attestations[k]=v
                else:
                    self.attestations[k]=v

    def update_local_blockchain(self, block):
        """
        When self.Node receive a new block,
        update the local copy of the blockchain.
        """
        self.local_blockchain = self.local_blockchain.union(block)
        self.check_cached_attestations()

    # TODO: gossip blocks, naming should be changed accordingly
    def gossip(self, listening_node):
        # self.non_gossiped_to.remove(listening_node)
        listening_node.listen(self)

    # TODO: listen blocks, naming should be changed accordingly
    def listen(self, gossiping_node):
        """Receive new block and update local information accordingly.
        """
        #block = gossiping_node.use_lmd_ghost()
        self.update_local_blockchain(gossiping_node.local_blockchain)

        if self.is_attesting is True:
            for b in self.local_blockchain:
                if b.slot_no == self.model.slot_boundary.counter:
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

    # pylint: disable=too-many-instance-attributes
    # the number of attributes is none of pylint business

    def __init__(self,
                 graph=None,
                 tau_block=None,
                 tau_attest=None,
                 delay_share=0,
                 delay_time=0,
                 seed=None):
        # set random seed
        self.rng = np.random.default_rng(seed)
        # set internal variables
        self.tau_block = tau_block
        self.tau_attest = tau_attest
        self.slots_per_epoch = 1
        self.delay_share = delay_share
        self.delay_time = delay_time
        # init the blocktree
        self.blockchain = [Block()]
        # set up peers
        self.network = Network(graph)
        self.N = len(self.network)
        self.nodes = [Node(blockchain=self.blockchain,
                           rng=self.rng, id=i, model=self)
                      for i in range(self.N)]
        # validators == peers
        self.validators = self.nodes
        # set up delayers nodes
        if self.delay_share > 0:
            self.delay_nodes = self.rng.choice(self.nodes, size=math.floor(self.N*self.delay_share))
            for node in self.delay_nodes:
                node.delayer = True
        # init attestations
        for node in self.nodes:
            node.attestations = {v: (self.blockchain[0], -1)
                                 for v in self.validators}
        # set up p2p network
        self.network.set_neighborhood(self.nodes)
        self.edges = [(n, k) for n in self.nodes for k in n.neighbors]

        # set up stochastic processes
        self.block_gossip_process = BlockGossipProcess(tau=self.tau_block,
                                                       edges=self.edges)
        self.attestation_gossip_process = AttestationGossipProcess(
            tau=self.tau_attest,
            edges=self.edges)

        self.epoch_boundary = EpochBoundary(slot_interval=12,
                                            validators=self.validators,
                                            slots_per_epoch=self.slots_per_epoch,
                                            rng=self.rng)
        self.late_proposal = LateProposal(np.inf,
                                            delay=self.delay_time,
                                            rng=self.rng)
        self.slot_boundary = SlotBoundary(12,
                                          self.validators,
                                          self.epoch_boundary,
                                          late_proposal=self.late_proposal,
                                          rng=self.rng)
        self.attestation_boundary = AttestationBoundary(12,
                                                        offset=4,
                                                        validators=self.validators,
                                                        rng=self.rng)

        self.processes = [self.block_gossip_process,
                          self.attestation_gossip_process]
        self.fixed_events = [self.epoch_boundary, self.slot_boundary,
                             self.attestation_boundary, self.late_proposal]
        # set up gillespie model
        self.gillespie = Gillespie(self.processes, self.rng)
        self.time = 0

    def run(self, stoping_time):
        """Method to run the model. Needs stopping time.
        """
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

            # to increase performance
            flag_blocks_are_the_same = True
            flag_attestations_are_the_same = True
            for n in self.nodes[1:]:
                if self.nodes[0].local_blockchain != n.local_blockchain:
                    flag_blocks_are_the_same = False
                    break
                if self.nodes[0].attestations != n.attestations:
                    flag_attestations_are_the_same = False
                    break

            if flag_blocks_are_the_same and flag_attestations_are_the_same:
                self.time = min([fixed.next_event for fixed in self.fixed_events])


    def results(self):
        """This functions returns a dictionary containing the
        experiments results, meaning the value functions computed
        on the final blocktree generated by the simulation.

        Returns:
        --------
        results : dictionary
        """
        # attestations from a god pov
        # for each node we have the latest attestations issued by the node
        god_view_attestations = {node: node.attestations[node] for node in self.validators}

        results_dict = {
            "mainchain_rate": calculate_mainchain_rate(self.blockchain, god_view_attestations),
            "branch_ratio": calculate_branch_ratio(self.blockchain, god_view_attestations),
            "blocktree_entropy": calculate_entropy(self.blockchain),
            "diameter": calculate_diameter(self.network),
            "average_shortest_path": calculate_average_shortest_path(self.network),
            "delayer_orphan_rate": calculate_delayer_orphan_rate(self.blockchain, god_view_attestations),
            }
        return results_dict


# FUNCTIONS
# LMD Ghost following functions handle LMD Ghost Evaluation of Blocks


def find_leaves_of_blockchain(blockchain):
    parent_blocks = {b.parent for b in blockchain}
    return blockchain - parent_blocks


def stake_attestation_evaluation(node):
    """Returns a peer stake.
    """
    return 1


def lmd_ghost(blockchain, attestations):
    """Returns the current head of the chain following LMD-GHOST algorithm
    from [0].

    [0]: Buterin, Vitalik, et al. "Combining GHOST and casper."arXiv preprint arXiv:2003.03052 (2020)."""

    # k:peer, v[0]: pointer to the attested block
    attest = {k: v[0] for k, v in attestations.items()}
    # blocks with at least one children
    parent_blocks = {b.parent for b in blockchain if b.parent is not None}
    # blocks with no children
    # leaves = blockchain - parent_blocks
    # for each leave, chain from the genesis to the leaf
    # chains = {b: b.predecessors for b in leaves}
    # key: block, item: list of nodes attesting to it
    inverse_attestations = {}
    for node, block in attest.items():
        inverse_attestations[block] = inverse_attestations.get(block, []) + [node]

    # define lambda function to return stake weight of a list of peers
    sum_stake = lambda node_list : sum([stake_attestation_evaluation(node) for node in node_list])
    # evaluate leaves weight
    leaves_weight = {block: sum_stake(item) for block, item in inverse_attestations.items()}
    # assign weight to all blocks in the local blocktree
    # all blocks have 0 by default
    blocks_weight = {block: 0 for block in blockchain}
    # attested leaves have anon-zero weight
    blocks_weight.update(leaves_weight)
    # diffuse the non-zero weight upward the blocktree branches
    for leaf, leaf_weight in leaves_weight.items():
        for block in leaf.predecessors:
            blocks_weight[block] += leaf_weight
    # find lmd ghost head chain
    # continue until leaf(from local peer pow)
    # head_chain = blockchain.genesis  # TODO: use a method of Blockchain class
    head_chain = [block for block in blockchain if block.parent is None].pop()
    while len([child for child in head_chain.children if child in blockchain]) > 0:
        local_children = [child for child in head_chain.children if child in blockchain]
        # pop a random item from children set
        list_head_chain = [local_children.pop()]
        current_max = blocks_weight[list_head_chain[0]]
        while len(local_children) > 0:
            block = local_children.pop()
            # compare children weights
            if blocks_weight[block] > current_max:
                list_head_chain = [block]
                current_max = blocks_weight[block]
            elif blocks_weight[block] == current_max:
                list_head_chain.append(block)
        # tie-breaks
        sorted(list_head_chain, key=hash)
        # update new head chain
        head_chain = list_head_chain[0]

    return head_chain


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


def calculate_mainchain_rate(blockchain, attestations):
    """Compute the ratio of blocks in the mainchain over the total
    number of blocks produced in the simulation.

    Parameters:
    -----------
    blockchain : A list of Block objects

    Returns:
    --------
    xi : float
        Mainchain blocks ratio
    """

    if isinstance(blockchain, list):
        blockchain = set(blockchain)
    head_block = lmd_ghost(blockchain, attestations)
    main_chain = head_block.predecessors
    return len(main_chain)/len(blockchain)


def calculate_branch_ratio(blockchain, attestations):
    """Compute the branch Ratio, which measures how often forks hap-
    pen

    Parameters:
    -----------
    blockchain : A list of Block objects

    Returns:
    --------
    F : float
        The branching ratio
    """

    # check blockchain is actually a list or a set
    # TODO: do we really need it?
    # if isinstance(blockchain, set):
    #    blockchain_list = list(blockchain)
    #else:
    #    blockchain_list = blockchain.copy()
    if isinstance(blockchain, list):
        blockchain = set(blockchain)
    main_chain = lmd_ghost(blockchain, attestations).predecessors
    orphan_chain = blockchain - main_chain

    counter = 0
    for block in main_chain:
        for orphan in orphan_chain:
            if block.parent == orphan.parent:
                counter += 1

    return counter/len(main_chain)


def calculate_entropy(blockchain):
    """Compute the entropy of the in-degree distribution of the blocktree
    """
    # compute the degree frequency
    degrees = np.array([len(block.children) for block in blockchain])
    degrees_unique, degrees_counts = np.unique(degrees, return_counts=True)
    degrees_frequencies = degrees_counts/degrees_counts.sum()
    tmp = 0
    for prob in degrees_frequencies:
        tmp -= prob*np.log(prob)
    return tmp


def calculate_diameter(net):
    """Compute diameter of the p2p network
    """
    return nx.diameter(net.network)


def calculate_average_shortest_path(net):
    """Compute diameter of the p2p network
    """
    return nx.average_shortest_path_length(net.network)


def calculate_delayer_orphan_rate(blockchain, attestations):
    """Compute the orphan rate for blocks produced by
    delayer nodes.
    The orphan rate is defined as the number of blocks produced by delayers
    that are orphaned over the total number of blocks produced by delayers.
    """
    if isinstance(blockchain, list):
        blockchain = set(blockchain)
    head_block = lmd_ghost(blockchain, attestations)
    main_chain = head_block.predecessors

    orphan_counter = 0
    block_counter = 0
    for block in blockchain:
        if block.emitter != 'genesis':
            if block.emitter.delayer:
                block_counter += 1
                if block not in main_chain:
                    orphan_counter += 1

    return orphan_counter/block_counter
