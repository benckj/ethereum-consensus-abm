import networkx as nx

from consensus_utils import *
from visualizations import *


class Network:
    """Object to manage the peer-to-peer network. It is a wrapper of networkx.Graph right now.
    INPUT
    - G,    a networkx.Graph object
    """

    import networkx as nx

    def __init__(self, network_graph):
        # G is a networkx Graph
        self.network = network_graph

    def __len__(self):
        return len(self.network)

    def set_neighborhood(self, peers):
        # dictionary mapping nodes in the nx.graph to their peers on p2p network
        peers_dict = dict(zip(self.network.nodes(), peers))

        # save peer node object as an attribute of nx node
        nx.set_node_attributes(
            self.network, values=peers_dict, name='neighbors')

        for n in self.network.nodes():
            m = self.network.nodes[n]["neighbors"]
            # save each neighbour in the nx.Graph inside the peer node object
            for k in self.network.neighbors(n):
                m.neighbors.add(self.network.nodes[k]["neighbors"])


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
    counter = 0

    @classmethod
    def __update(cls):
        cls.counter += 1

    def __init__(self, value, emitter, slot, parent=None):

        self.id = self.counter
        self.__update()
        self.children = set()
        self.parent = parent
        self.value = value

        if parent == None:
            self.parent = None
            self.height = 0
            self.emitter = "genesis"
            self.slot = slot
            self.predecessors = {self}

        else:
            self.parent = parent
            self.height = self.parent.height + 1
            self.emitter = emitter
            parent.children.add(self)
            self.predecessors = parent.predecessors.copy()
            self.predecessors.add(self)
            self.slot = slot

    def __repr__(self):
        return '<Block {} (h={}) (v={})>'.format(self.id, self.slot, self.value)

    def __next__(self):
        if self.parent:
            return self.parent
        else:
            raise StopIteration


class Attestation():
    """It wraps a block to a node. In the context of attestation, 
    the block is the attested block and the node is the attestor.
    INPUTS:
    - attestor,  Node object
    - block,     Block object
    """

    def __init__(self, attestor, block, slot):
        self.attestor = attestor
        self.block = block
        self.slot = slot

    def as_dict(self):
        return {self.slot: {self.attestor: self.block}}

    def __eq__(self, other):
        return self.attestor == other.attestor and self.block == other.block and self.slot == self.slot

    def __hash__(self):
        return hash((self.attestor, self.slot, self.block))

    def __repr__(self):
        return '<Attestation: Block {} by node {}>'.format(self.block.id, self.slot, self.attestor.id)


class Node:
    '''Class for the validator.

    INPUT:
    - blockchain,   list of Block objects,
    '''
    counter = 0

    @classmethod
    def __update(cls):
        cls.counter += 1

    def __init__(self, block, rng):
        self.id = self.counter
        self.__update()

        self.rng = rng
        self.gasper = Gasper(block[0])
        self.attestations = {}  # {slot: {node:block}}

        self.local_blockchain = [block[0]]
        self.global_blockchain = {-1: block[0]}

        self.is_attesting = False
        self.neighbors = set()  # set of neighbours peers on the p2p network
        self.gossip_data = {}  # {slot: {"block": block, "attestations": []}}

    def use_lmd_ghost(self):
        self.gasper.lmd_ghost(self.attestations)
        self.global_blockchain = self.gasper.consensus_chain
        return self.gasper.get_head_block()

    def propose_block(self, slot, value):
        head_slot, head_block = self.use_lmd_ghost()
        if head_slot >= slot:
            raise "Syncing Issue"

        # check if the slot is colliding
        new_block = Block(value, emitter=self, slot=slot,
                          parent=head_block)
        print('Block proposed {} in slot {} by {}'.format(new_block, slot, self))
        self.local_blockchain.append(new_block)

        self.gossip_data[slot] = {"block": new_block}

    def gossip_block(self, listening_node, slot):
        listening_node.listen_block(self, slot)

    def listen_block(self, gossiping_node, slot):
        """Receive new block and update local information accordingly.
        """

        if (slot not in gossiping_node.gossip_data.keys()) or ("block" not in gossiping_node.gossip_data[slot].keys()):
            return

        listened_block = gossiping_node.gossip_data[slot]["block"]

        if listened_block not in self.local_blockchain:
            # Add to local of the node
            self.local_blockchain.append(listened_block)

            # Gossip the listened block,
            self.gossip_data[slot] = {"block": listened_block}

        # Attest if the node is in committee
        if self.is_attesting == True:
            if slot in self.attestations.keys() and self in self.attestations[slot].keys():
                return
            self.attest(slot)

    # Should take a new incoming block into consideration
    def attest(self, slot):
        """Create the Attestation for the current head of the chain block.
        """
        # Call Consensus
        # Fetch the Block and then Attest
        attesting_slot, attesting_block = slot, self.gasper.get_block2attest(
            self.local_blockchain.copy().pop(), self.attestations)
        print('Block attested {} in slot {} by {}'.format(
            attesting_block, attesting_slot, self))
        attestation = Attestation(self, attesting_block, attesting_slot)

        if attestation.slot not in self.attestations.keys():
            self.attestations[attestation.slot] = {}
        self.attestations[attestation.slot][attestation.attestor] = attestation.block

        # Create the attestation for this slot
        if attestation.slot not in self.gossip_data.keys() or "attestations" not in self.gossip_data[attestation.slot].keys():
            self.gossip_data[attestation.slot] = {"attestations": set()}

        # Copy the attestation to gossip
        self.gossip_data[attestation.slot]["attestations"].add(
            tuple([attestation.slot, attestation.attestor, attestation.block]))
        self.is_attesting = False  # As a node has to attest only once in a slot

    def gossip_attestation(self, listening_node, slot):
        listening_node.listen_attestation(self, slot)

    def listen_attestation(self, gossiping_node, slot):
        # if head block is the parent of the new block then vote for it or else check attestations of that block as the node knows.
        if slot not in gossiping_node.gossip_data.keys() or "attestations" not in gossiping_node.gossip_data[slot].keys():
            return
        listened_attestations = gossiping_node.gossip_data[
            slot]["attestations"]

        for l_slot, l_node, l_block in listened_attestations:
            if l_slot not in self.attestations.keys():
                self.attestations[l_slot] = {}
            self.attestations[l_slot][l_node] = l_block

        # Copy the attestation to gossip
        if slot not in self.gossip_data.keys() or "attestations" not in self.gossip_data[slot].keys():
            self.gossip_data[slot] = {"attestations": set()}
        self.gossip_data[slot]["attestations"].update(
            listened_attestations)  # init to send it out

    def __repr__(self):
        return '<Node {}>'.format(self.id)
