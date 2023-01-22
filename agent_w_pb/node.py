from .base_utils import *
from .gasper_consensus import *
import numpy as np
import logging

class NodeState:
    def __init__(self, block, logging = logging) -> None:
        self.local_blockchain = set([block])
        self.attestations = {} # {slot: {node: block}}
        self.gossip_data = {}  # {slot: {"block": block, "attestations": []}}
        self.cached_attestations = set()  # {tuple(slot,node,block)}
        self.cached_blocks = set()
        self.proposer_weight = None
        self.logging = logging.getLogger('Node State')

    def get_block(self, block):
        replica = self.local_blockchain.copy()
        replica.remove(block)
        return (self.local_blockchain - replica).pop()

    def add_block(self, slot, chainstate: ChainState, received_block: Block):

        block = received_block.copy()
        block.update_receiving(chainstate)

        # as read in the gossiping rules, A Node should not accept a block where it does not
        # now its parent block of that listened block https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/p2p-interface.md#beacon_block

        if (block.parent not in self.local_blockchain):
            self.cached_blocks.add(block)
            return

        if block not in self.local_blockchain:
            self.local_blockchain.add(block)
            self.check_cached_blocks()
            self.check_cached_attestations()

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
                self.local_blockchain.add(block)

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

    def __init__(self, block, id, rng=np.random.default_rng(100), malicious=False, logging=logging):
        self.id = id
        # logging functionality
        self.logging = logging.getLogger('Node {}'.format(id))
           
        # Malicious Functionality
        self.malicious = malicious

        self.rng = rng
        self.gasper = Gasper(block)
        self.state = NodeState(block, logging)

        self.is_attesting = False
        self.neighbors = set()  # set of neighbours peers on the p2p network
     
        self.obstruct_gossiping = False


    def use_lmd_ghost(self, chainstate):
        self.gasper.lmd_ghost(chainstate, self.state)                              
        return self.gasper.get_head_block()

    def propose_block(self, chainstate: ChainState):
        head_slot, head_block = self.use_lmd_ghost(chainstate)
        if head_slot >= chainstate.slot:
            raise "Syncing Issue"

        # check if the slot is colliding
        new_block = Block('E{}_S{}'.format(
            chainstate.epoch, chainstate.slot), emitter=self, slot=chainstate.slot,
                          parent=head_block)
        self.logging.debug('Block proposed {} in slot {} by {}, with head as {}'.format(
            new_block, chainstate.slot, self, head_block))

        # add block to local blockchain
        self.state.add_block(chainstate.slot, chainstate, new_block)

        chainstate.update_gods_view(block=new_block)

    def gossip_block(self, chainstate: ChainState, listening_node):
        if self.obstruct_gossiping == True:
            return
        listening_node.listen_block(chainstate, self)

    def listen_block(self,  chainstate: ChainState, gossiping_node,):
        """Receive new block and update local information accordingly.
        """
        for listening_slot in gossiping_node.state.gossip_data.keys():
            if chainstate.slot > listening_slot > self.gasper.finalized_head_slot or ("block" not in gossiping_node.state.gossip_data[listening_slot].keys()):
                continue

            listening_block = gossiping_node.state.gossip_data[listening_slot]["block"]

            # As node can listen only one proposed block in a particular slot
            if listening_slot in self.state.gossip_data.keys() and "block" in self.state.gossip_data[listening_slot].keys():
                if self.state.gossip_data[listening_slot]["block"] != listening_block or self.state.gossip_data[listening_slot]["block"] != None:
                    continue
                
            if listening_block not in self.state.local_blockchain:
                # Add to local of the node
                self.state.add_block(listening_slot, chainstate, listening_block)

        # Attest if the node is in committee
        if self.is_attesting == True and chainstate.slot in self.state.gossip_data.keys() and "block" in self.state.gossip_data[chainstate.slot] and self.state.gossip_data[chainstate.slot]["block"]:
            if chainstate.slot in self.state.attestations.keys() and self in self.state.attestations[chainstate.slot].keys():
                return
            self.attest(chainstate)

    # Should take a new incoming block into consideration
    def attest(self, chainstate: ChainState):
        """Create the Attestation for the current head of the chain block.
        """
        # Fetch the Block2Attest, taking the listened blocks, LISTs in python behave LIFO
        attesting_slot, attesting_block = self.gasper.get_block2attest(chainstate,self.state)
            # self.state.local_blockchain.copy(), self.state.attestations)

        self.logging.debug('Block attested {} with weight {}'.format(
            attesting_block, attesting_block.booster_weight))

        # Create the attestation for this slot
        attestation = Attestation(self, attesting_block, attesting_slot)

        self.logging.debug('Block attested {} in slot {} by {}'.format(
            attesting_block, attesting_slot, self))

        self.state.add_attestation(attestation)

        chainstate.update_gods_view(attestation=attestation)
        # As a node must attest only once in a slot
        self.is_attesting = False

    def gossip_attestation(self, chainstate: ChainState, listening_node):
        if self.obstruct_gossiping == True:
            return
        listening_node.listen_attestation(chainstate, self)

    def listen_attestation(self, chainstate, gossiping_node):
        # as read in the gossiping attestation rules, A Node should not accept an attestation until ATTESTATION_PROPAGATION_SLOT_RANGE of slots
        # now its parent block of that listened block https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/p2p-interface.md#attestation-subnets
        for listening_slot in gossiping_node.state.gossip_data.keys():
            if listening_slot + ATTESTATION_PROPAGATION_SLOT_RANGE >= chainstate.slot >= listening_slot and chainstate.slot // SLOTS_PER_EPOCH == listening_slot // SLOTS_PER_EPOCH:

                if "attestations" not in gossiping_node.state.gossip_data[listening_slot].keys():
                    continue
                
                
                for attestation in gossiping_node.state.gossip_data[
                    listening_slot]["attestations"]:
                    self.state.add_attestation(attestation)

    def __repr__(self):
        return '<Node {}>'.format(self.id)
