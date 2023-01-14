from .base_utils import *
from .gasper_consensus import *
import numpy as np


class Node:
    '''Class for the validator.

    INPUT:
    - blockchain,   list of Block objects,
    '''

    def __init__(self, block, id, rng=np.random.default_rng(100), malicious=False):
        self.id = id

        self.rng = rng
        self.gasper = Gasper(block)
        self.attestations = {}  # {slot: {node:block}}
        self.cached_attestations = set()  # {tuple(slot,node,block)}
        self.cached_blocks = set()

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
        # as read in the gossiping rules, A Node should not accept a block where it does not
        # now its parent block of that listened block https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/p2p-interface.md#beacon_block
        if (block.parent not in self.local_blockchain):
            self.cached_blocks.add(block)
            return
        if block not in self.local_blockchain:
            self.local_blockchain.append(block)
            self.check_cached_attestations()
            self.check_cached_blocks()

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

        # [TODO] How to add the 40% Attestation Proposer booster weight to consensus chain when node is proposing
        # also check this with

        # add new_block to gossiping data
        self.gossip_data[slot] = {"block": new_block}

        return new_block

    def gossip_block(self, listening_node, slot):
        if self.obstruct_gossiping == True and listening_node not in self.malicious_neighbors:
            return
        return listening_node.listen_block(self, slot)

    def listen_block(self, gossiping_node, slot):
        """Receive new block and update local information accordingly.
        """
        for listening_slot in gossiping_node.gossip_data.keys():
            if slot > listening_slot > self.gasper.finalized_head_slot or ("block" not in gossiping_node.gossip_data[listening_slot].keys()):
                continue

            listening_block = gossiping_node.gossip_data[listening_slot]["block"]

            # As node can listen only one proposed block in a particular slot
            if listening_slot in self.gossip_data.keys() and "block" in self.gossip_data[listening_slot].keys():
                if self.gossip_data[listening_slot]["block"] != listening_block or self.gossip_data[listening_slot]["block"] != None:
                    continue

            if listening_block not in self.local_blockchain:
                # Add to local of the node
                self.update_local_blockchain(listening_block)

                # Gossip the listened block if the slot does not exist on the gossip data
                if listening_slot not in self.gossip_data.keys():
                    self.gossip_data[listening_slot] = {"block": listening_block}

                # Gossip the listened block if the gossip data does have slot but not the block key.
                if "block" not in self.gossip_data[listening_slot].keys():
                    self.gossip_data[listening_slot].update({"block": listening_block})

        # Attest if the node is in committee
        if self.is_attesting == True and slot in self.gossip_data.keys() and "block" in self.gossip_data[slot]:
            if slot in self.attestations.keys() and self in self.attestations[slot].keys():
                return
            return self.attest(slot)

    # Should take a new incoming block into consideration
    def attest(self, slot):
        """Create the Attestation for the current head of the chain block.
        """
        # Fetch the Block2Attest, taking the listened blocks, LISTs in python behave LIFO
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

        if attestation.slot not in self.gossip_data.keys():
            self.gossip_data[attestation.slot] = {"attestations": set()}

        if "attestations" not in self.gossip_data[attestation.slot].keys():
            self.gossip_data[attestation.slot].update({"attestations": set()})

        # Copy the attestation to gossip
        self.gossip_data[attestation.slot]["attestations"].add(
            tuple([attestation.slot, attestation.attestor, attestation.block]))

        # As a node must attest only once in a slot
        self.is_attesting = False
        return attestation

    def gossip_attestation(self, listening_node, slot):
        if self.obstruct_gossiping == True and listening_node not in self.malicious_neighbors:
            return
        listening_node.listen_attestation(self, slot)

    def listen_attestation(self, gossiping_node, slot):
        # as read in the gossiping attestation rules, A Node should not accept an attestation until ATTESTATION_PROPAGATION_SLOT_RANGE of slots
        # now its parent block of that listened block https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/p2p-interface.md#attestation-subnets
        for listening_slot in gossiping_node.gossip_data.keys():
            if listening_slot + ATTESTATION_PROPAGATION_SLOT_RANGE >= slot >= listening_slot and slot // SLOTS_PER_EPOCH == listening_slot // SLOTS_PER_EPOCH:

                if "attestations" not in gossiping_node.gossip_data[listening_slot].keys():
                    continue

                listened_attestations = gossiping_node.gossip_data[
                    listening_slot]["attestations"]

                for l_slot, l_node, l_block in listened_attestations:

                    if l_slot not in self.attestations.keys():
                        self.attestations[l_slot] = {}

                    if l_block not in self.local_blockchain:
                        # Below execute if the block does not exist in the  the block is not yet known by the node
                        self.cached_attestations.add(
                            tuple([l_slot, l_node, l_block]))
                        continue

                    self.attestations[l_slot][l_node] = l_block

         
                if slot not in self.gossip_data.keys():
                    self.gossip_data[slot] = {"attestations": set()}
                if "attestations" not in self.gossip_data[slot].keys():
                    self.gossip_data[slot].update({"attestations": set()})

                # Copy the attestation to gossip
                self.gossip_data[slot]["attestations"].update(
                    listened_attestations)  # init to send it out

    def check_cached_blocks(self):
        for block in self.cached_blocks.copy():
            if block.parent in self.local_blockchain:
                self.cached_blocks.remove(
                    block)
                self.local_blockchain.append(block)

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
