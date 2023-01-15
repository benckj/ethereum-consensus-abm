from .base_utils import *
from .gasper_consensus import *
import numpy as np
import logging

class NodeState:
    def __init__(self, block) -> None:
        self.local_blockchain = [block]
        self.attestations = {} # {slot: {node: block}}
        self.gossip_data = {}  # {slot: {"block": block, "attestations": []}}
        self.cached_attestations = set()  # {tuple(slot,node,block)}
        self.cached_blocks = set()

    def add_block(self, slot, block):
        # as read in the gossiping rules, A Node should not accept a block where it does not
        # now its parent block of that listened block https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/p2p-interface.md#beacon_block
        if (block.parent not in self.local_blockchain):
            self.cached_blocks.add(block)
            return
        if block not in self.local_blockchain:
            self.local_blockchain.append(block)
            self.check_cached_attestations()
            self.check_cached_blocks()

        # add new_block to gossiping data
        if slot not in self.gossip_data.keys():
            self.gossip_data[slot] = {"block": block}
        else: 
            self.gossip_data[slot].update({"block": block})

    def add_attestation(self, attestation):
        if attestation.block not in self.local_blockchain:
            # Cache the attestation if the node does not know the block yet.
            self.cached_attestations.add(attestation)
        else:
            # add the attestations into the node's attestations
            if attestation.slot not in self.attestations.keys():
                self.attestations[attestation.slot] = {}
            self.attestations[attestation.slot][attestation.attestor] = attestation.block

        if attestation.slot not in self.gossip_data.keys():
            self.gossip_data[attestation.slot] = {"attestations": set()}

        if "attestations" not in self.gossip_data[attestation.slot].keys():
            self.gossip_data[attestation.slot].update({"attestations": set()})

        # Copy the attestation to gossip
        self.gossip_data[attestation.slot]["attestations"].add(attestation)  
    
    def check_cached_blocks(self):
        for block in self.cached_blocks.copy():
            if block.parent in self.local_blockchain:
                self.cached_blocks.remove(
                    block)
                self.local_blockchain.append(block)

    def check_cached_attestations(self):
        for attestation in self.cached_attestations.copy():
            if attestation.block in self.local_blockchain:
                if attestation.slot in self.attestations.keys():
                    if not (attestation.attestor in self.attestations[attestation.slot].keys() and self.attestations[attestation.slot][attestation.attestor] == attestation.block):
                        self.attestations[attestation.slot][attestation.attestor] = attestation.block
                        # if the attestor's attestation already reached the attestations then just delete the cached attestation
                else:
                    self.attestations[attestation.slot] = {}
                    self.attestations[attestation.slot][attestation.attestor] = attestation.block

                # delete from cache
                self.cached_attestations.remove(attestation)

class Node:
    '''Class for the validator.

    INPUT:
    - blockchain,   list of Block objects,
    '''

    def __init__(self, block, id, rng=np.random.default_rng(100), malicious=False, shared_state=None, logging=logging):
        self.id = id
        # logging functionality
        self.logging = logging.getLogger('Node {}'.format(id))
           
        # Malicious Functionality
        self.malicious = malicious

        if self.malicious and shared_state == None:
            self.logging.error('Provide shared state when using the malicious')

        self.rng = rng
        self.gasper = Gasper(block)
        self.state = NodeState(block) if not self.malicious else shared_state

        self.is_attesting = False
        self.neighbors = set()  # set of neighbours peers on the p2p network
     
        self.obstruct_gossiping = False


    def use_lmd_ghost(self, slot):
        self.gasper.lmd_ghost(self.state.local_blockchain.copy(),
                              self.gasper.prune_attestatations_byInclusionDelay(slot, self.state.attestations))

        return self.gasper.get_head_block()

    def propose_block(self, slot, value):
        head_slot, head_block = self.use_lmd_ghost(slot)
        if head_slot >= slot:
            raise "Syncing Issue"

        # check if the slot is colliding
        new_block = Block(value, emitter=self, slot=slot,
                          parent=head_block)
        self.logging.debug('Block proposed {} in slot {} by {}, with head as {}'.format(
            new_block, slot, self, head_block))

        # add block to local blockchain
        self.state.add_block(slot, new_block)

        # [TODO] How to add the 40% Attestation Proposer booster weight to consensus chain when node is proposing
        # also check this with

        return new_block

    def gossip_block(self, listening_node, slot):
        if self.obstruct_gossiping == True:
            return
        return listening_node.listen_block(self, slot)

    def listen_block(self, gossiping_node, slot):
        """Receive new block and update local information accordingly.
        """
        for listening_slot in gossiping_node.state.gossip_data.keys():
            if slot > listening_slot > self.gasper.finalized_head_slot or ("block" not in gossiping_node.state.gossip_data[listening_slot].keys()):
                continue

            listening_block = gossiping_node.state.gossip_data[listening_slot]["block"]

            # As node can listen only one proposed block in a particular slot
            if listening_slot in self.state.gossip_data.keys() and "block" in self.state.gossip_data[listening_slot].keys():
                if self.state.gossip_data[listening_slot]["block"] != listening_block or self.state.gossip_data[listening_slot]["block"] != None:
                    continue

            if listening_block not in self.state.local_blockchain:
                # Add to local of the node
                self.state.add_block(listening_slot, listening_block)

        # Attest if the node is in committee
        if self.is_attesting == True and slot in self.state.gossip_data.keys() and "block" in self.state.gossip_data[slot] and self.state.gossip_data[slot]["block"]:
            if slot in self.state.attestations.keys() and self in self.state.attestations[slot].keys():
                return
            return self.attest(slot)

    # Should take a new incoming block into consideration
    def attest(self, slot):
        """Create the Attestation for the current head of the chain block.
        """
        # Fetch the Block2Attest, taking the listened blocks, LISTs in python behave LIFO
        attesting_slot, attesting_block = slot, self.gasper.get_block2attest(
            self.state.local_blockchain.copy(), self.state.attestations)

        # Create the attestation for this slot
        attestation = Attestation(self, attesting_block, attesting_slot)

        self.logging.debug('Block attested {} in slot {} by {}'.format(
            attesting_block, attesting_slot, self))

        self.state.add_attestation(attestation)

        # As a node must attest only once in a slot
        self.is_attesting = False
        return attestation

    def gossip_attestation(self, listening_node, slot):
        if self.obstruct_gossiping == True:
            return
        listening_node.listen_attestation(self, slot)

    def listen_attestation(self, gossiping_node, slot):
        # as read in the gossiping attestation rules, A Node should not accept an attestation until ATTESTATION_PROPAGATION_SLOT_RANGE of slots
        # now its parent block of that listened block https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/p2p-interface.md#attestation-subnets
        for listening_slot in gossiping_node.state.gossip_data.keys():
            if listening_slot + ATTESTATION_PROPAGATION_SLOT_RANGE >= slot >= listening_slot and slot // SLOTS_PER_EPOCH == listening_slot // SLOTS_PER_EPOCH:

                if "attestations" not in gossiping_node.state.gossip_data[listening_slot].keys():
                    continue

                for attestation in gossiping_node.state.gossip_data[
                    listening_slot]["attestations"]:
                    self.state.add_attestation(attestation)



    def __repr__(self):
        return '<Node {}>'.format(self.id)
