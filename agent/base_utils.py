import networkx as nx
import numpy as np
import logging

from .constants import *


class Network:
    """Object to manage the peer-to-peer network. It is a wrapper of networkx.Graph right now.
    INPUT
    - G,    a networkx.Graph object
    """

    def __init__(self, graph):
        # graph is a networkx Graph
        self.graph = graph

    def __len__(self):
        return len(self.graph)

    def set_neighborhood(self, nodes):
        """
        Function is used to set neighbours property of the nodes based on the edges in the network graph
        """
        # dictionary mapping nodes in the nx.graph to their peers on p2p graph

        # Shuffle the nodes to
        peers_dict = dict(zip(self.graph.nodes(), nodes))

        # save peer node object as an attribute of nx node
        nx.set_node_attributes(
            self.graph, values=peers_dict, name='node_mapping')

        for n in self.graph.nodes():
            node_object = self.graph.nodes[n]["node_mapping"]
            # save each neighbour in the nx.Graph inside the peer node object
            for k in self.graph.neighbors(n):
                node_object.neighbors.add(self.graph.nodes[k]["node_mapping"])


class Block:
    '''
    Class for blocks.

    INPUT:
    value            - blocks values (this is arbitray value) used to differentiate the generation.
    emitter          - List of objects
    slot             - slot of the block
    parent           - Block object (parent of the block)
    transactions     - Number (integer) of transactions in the block
    '''

    def __init__(self, value, emitter, slot, parent=None, malicious=False):
        self.children = set()
        self.parent = parent
        self.value = value
        self.slot = slot
        self.malicious = malicious

        if parent == None:
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
        if not isinstance(self, Block):
            return None
        return '<Block {} (h={}) (s={})>'.format(self.value, self.height, self.slot)

    def __next__(self):
        if self.parent:
            return self.parent
        else:
            raise StopIteration

    def __eq__(self, other):
        if not isinstance(other, Block):
            return False
        return self.parent == other.parent and self.value == other.value and self.slot == other.slot and self.height == other.height and self.emitter == other.emitter

    def __hash__(self):
        if not isinstance(self, Block):
            return None
        return hash((self.parent, self.value, self.slot, self.height, self.emitter))

    def copy(self):
        obj = type(self).__new__(self.__class__)
        obj.__dict__.update(self.__dict__)
        return obj


class Attestation():
    """It wraps a block to a node. In the context of attestation, 
    the block is the attested block and the node is the attestor.
    INPUTS:
    - attestor,  Node object, (Member of the committee attestating)
    - block,     Block object, (The Block voted)
    - slot,      number, ()
    """

    def __init__(self, attestor, block, slot):
        self.attestor = attestor
        self.block = block
        self.slot = slot

    def as_dict(self):
        return {self.slot: {self.attestor: self.block}}

    def __eq__(self, other):
        return self.attestor == other.attestor and self.block == other.block and self.slot == other.slot

    def __hash__(self):
        return hash((self.attestor, self.slot, self.block))

    def __repr__(self):
        return '<Attestation: Block {} at slot {} by node {}>'.format(self.block.value, self.slot, self.attestor.id)


class ChainState():
    def __init__(self, time, epoch, slot, slot_committee_weight, proposer_vote_boost, genesis_block, logging=logging):
        self.time = time
        self.epoch = epoch
        self.slot = slot
        self.slot_committee_weight = slot_committee_weight
        self.proposer_vote_boost = proposer_vote_boost
        self.logging = logging.getLogger('ChainState')
        self.god_view_blocks = set([genesis_block])
        self.god_view_attestations = {}
        self.reorgs = []
        self.malicious_slot = True

    def reset_malicious_slot(self):
        self.malicious_slot = False

    def set_malicious_slot(self):
        self.reorgs.append(self.slot)
        self.malicious_slot = True

    def update_epoch(self, new_epoch):
        if new_epoch < self.epoch:
            self.logging.error(
                'New epoch should be greater than current epoch')
        self.epoch = new_epoch

    def update_slot(self, new_slot):
        if new_slot < self.slot:
            self.logging.error('New slot should be greater than current_slot')
        self.slot = new_slot

    def update_time(self, new_time):
        if new_time < self.time:
            self.logging.error('New time should be greater than current')
        self.time = new_time

    def update_gods_view(self, block: Block = None, attestation: Attestation = None):
        if block:
            self.god_view_blocks.add(block)
        if attestation:
            if attestation.slot not in self.god_view_attestations.keys():
                self.god_view_attestations[attestation.slot] = {}
            self.god_view_attestations[attestation.slot][attestation.attestor] = attestation.block

    def update_slot_committee_weight(self, weight):
        self.slot_committee_weight = weight

    def __eq__(self, other):
        return self.time == other.time and self.slot == other.slot and self.slot_committee_weight == other.slot_committee_weight

    def __hash__(self):
        return hash((self.time, self.slot, self.slot_committee_weight))

    def __repr__(self):
        return '<Slot: {} at epoch{} at time {} with committee weight {}>'.format(self.slot, self.epoch, self.time, self.slot_committee_weight)
