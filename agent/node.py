from .base_utils import *
from .gasper_consensus import *
import numpy as np


class Node:
    '''Class for the validator.

    INPUT:
    - blockchain,   list of Block objects,
    '''
    counter = 0

    @classmethod
    def __update(cls):
        cls.counter += 1

    def __init__(self, block, rng=np.random.default_rng(100), malicious=False):
        self.id = self.counter
        self.__update()

        self.rng = rng
        self.gasper = Gasper(block)
        self.attestations = {}  # {slot: {node:block}}
        self.cached_attestations = set()  # {tuple(slot,node,block)}

        self.local_blockchain = [block]
        self.global_blockchain = {0: block}

        self.is_attesting = False
        self.neighbors = set()  # set of neighbours peers on the p2p network

        self.gossip_data = {}  # {slot: {"block": block, "attestations": []}}

        # Malicious Functionality
        self.malicious = malicious
        # set of malicious_neighbors peers on the p2p network
        self.malicious_neighbors = set()
        self.obstruct_gossiping = False

    def update_local_blockchain(self, block):
        self.local_blockchain.append(block)
        self.check_cached_attestations()

    def use_lmd_ghost(self, slot):
        self.gasper.lmd_ghost(
            self.gasper.prune_attestatations_byInclusionDelay(slot, self.attestations))
        self.global_blockchain = self.gasper.consensus_chain
        return self.gasper.get_head_block()

    def propose_block(self, slot, value):
        head_slot, head_block = self.use_lmd_ghost(slot)
        if head_slot >= slot:
            raise "Syncing Issue"

        # check if the slot is colliding
        new_block = Block(value, emitter=self, slot=slot,
                          parent=head_block)
        print('Block proposed {} in slot {} by {}, with head as {}'.format(
            new_block, slot, self, head_block))

        # add block to local blockchain
        self.update_local_blockchain(new_block)

        # [TODO] How to add the block to consensus chain when node is proposing

        # add new_block to gossiping data
        self.gossip_data[slot] = {"block": new_block}

    def gossip_block(self, listening_node, slot):
        if self.obstruct_gossiping == True and listening_node not in self.malicious_neighbors:
            return
        listening_node.listen_block(self, slot)

    def listen_block(self, gossiping_node, slot):
        """Receive new block and update local information accordingly.
        """
        if (slot not in gossiping_node.gossip_data.keys()) or ("block" not in gossiping_node.gossip_data[slot].keys()):
            return

        listened_block = gossiping_node.gossip_data[slot]["block"]

        if listened_block not in self.local_blockchain:
            # Add to local of the node
            self.update_local_blockchain(listened_block)

            # Gossip the listened block,
            self.gossip_data[slot] = {"block": listened_block}

        # [ToDo] Fork choice execution upon listening to a block or how does the consensus gets updated
        # As this should either happen before they attest or propose a block

        # Attest if the node is in committee
        if self.is_attesting == True:
            if slot in self.attestations.keys() and self in self.attestations[slot].keys():
                return
            self.attest(slot)

    # Should take a new incoming block into consideration
    def attest(self, slot):
        """Create the Attestation for the current head of the chain block.
        """
        # [TODO] How to decide after listening a block and attest this block.
        # 1) Any listened block  get attested if the node did not attest on other block in the same slot.
        # 2) RQ1:

        # Fetch the Block2Attest, taking the listened blocks

        attesting_slot, attesting_block = slot, self.gasper.get_block2attest(
            self.local_blockchain.copy().pop(), self.attestations)

        # Create the attestation for this slot
        attestation = Attestation(self, attesting_block, attesting_slot)

        print('Block attested {} in slot {} by {}'.format(
            attesting_block, attesting_slot, self))

        # add the attestations into the node's attestations
        if attestation.slot not in self.attestations.keys():
            self.attestations[attestation.slot] = {}
        self.attestations[attestation.slot][self] = attestation.block

        # # perform a ghost with latest attestations
        # self.use_lmd_ghost(slot)

        if attestation.slot not in self.gossip_data.keys() or "attestations" not in self.gossip_data[attestation.slot].keys():
            self.gossip_data[attestation.slot] = {"attestations": set()}

        # Copy the attestation to gossip
        self.gossip_data[attestation.slot]["attestations"].add(
            tuple([attestation.slot, attestation.attestor, attestation.block]))

        # As a node must attest only once in a slot
        self.is_attesting = False

    def gossip_attestation(self, listening_node, slot):
        if self.obstruct_gossiping == True and listening_node not in self.malicious_neighbors:
            return
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
            if l_block in self.local_blockchain:
                self.attestations[l_slot][l_node] = l_block
                continue

            # As the block is not yet known by the node
            self.cached_attestations.add(tuple([l_slot, l_node, l_block]))

        # Copy the attestation to gossip
        if slot not in self.gossip_data.keys() or "attestations" not in self.gossip_data[slot].keys():
            self.gossip_data[slot] = {"attestations": set()}

        self.gossip_data[slot]["attestations"].update(
            listened_attestations)  # init to send it out

    def check_cached_attestations(self):
        for slot, node, block in self.cached_attestations.copy():
            if block in self.local_blockchain:
                if slot in self.attestations.keys():
                    if node in self.attestations[slot].keys() and self.attestations[slot][node] == block:
                        # if the node's attestation is for same block in this slot
                        # then just delete the cached attestation
                        self.cached_attestations.remove(
                            tuple([slot, node, block]))
                    else:
                        self.attestations[slot][node] = block
                        # delete from cache
                        self.cached_attestations.remove(
                            tuple([slot, node, block]))
                else:
                    self.attestations[slot] = {}
                    self.attestations[slot][node] = block
                    # delete from cache
                    self.cached_attestations.remove(tuple([slot, node, block]))

    def __repr__(self):
        return '<Node {}>'.format(self.id)
