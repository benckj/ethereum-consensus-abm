from .base_utils import *
from .gasper_consensus import *
import numpy as np
import logging


class NodeState:
    def __init__(self, block, logging=logging) -> None:
        self.local_blockchain = set([block])
        self.attestations = {}  # {slot: {node: block}}
        self.gossip_data = {}  # {slot: {"block": block, "attestations": []}}
        self.cached_attestations = set()  # set of Attestation Object(slot,node,block)
        self.cached_blocks = set()
        self.logging = logging.getLogger('Node State')
        self.nodes_at = {}      # {node: Attestation}
        self.proposer_booster = None

    def update_receiving(self, chainstate: ChainState, block: Block):
        """
        Function is used to update node's proposer_booster block with eligibility criterias:
            - Block has to be received in the current slot of the Network
            - Block has to be received before 1st interval of the `SECONDS_PER_SLOT`
         This is used in the `add_block` in the `NodeState` class. 

        Parameters
        ----------
        chainstate: ChainState object: 
            This the network state object passed on globally.
        block: Block object: 
            This is the Block to be used to update the proposer boost.
        """
        if chainstate.slot == block.slot and (chainstate.time % SECONDS_PER_SLOT) < (SECONDS_PER_SLOT // INTERVALS_PER_SLOT):
            self.proposer_booster = block

    def add_block(self, chainstate: ChainState, block: Block):
        """
        Function adds a Block into Node States and Gossiping Data. 
        Criteria for updating node state:
            - Block should not already known by the Node. 
        Function also updates the cached attestations upon receiving the new block


        Parameters
        ----------
        chainstate: ChainState object: 
            This the network state object passed on globally.
        block: Block object: 
            block used to update the node's state..
        """

        if block in self.local_blockchain:
            return

        self.update_receiving(chainstate, block)
        self.local_blockchain.add(block)
        self.check_cached_attestations(chainstate)

        # add new_block to gossiping data
        if block.slot not in self.gossip_data.keys():
            self.gossip_data[block.slot] = {"block": block}
            return

        if "block" not in self.gossip_data[block.slot].keys():
            self.gossip_data[block.slot].update({"block": block})
            return

    def add_attestation(self, chainstate: ChainState,  attestation: Attestation):
        """
        Function adds an Attestation into Node State and Gossiping Data. 
        Function also queues the attestation, If:
         - The block is not known 
         (OR)
         - The attestation is of current slot.


        Parameters
        ----------
        chainstate: ChainState object: 
            This the network state object passed on globally.
        Attestation: Attestation object: 
            attestation used to update the node's state.
        """

        if (attestation.slot in self.attestations.keys()
            and attestation.attestor in self.attestations[attestation.slot].keys()
                and self.attestations[attestation.slot][attestation.attestor] == attestation.block):
            return

        # add attestation into gossiping data
        if attestation.slot not in self.gossip_data.keys():
            self.gossip_data[attestation.slot] = {"attestations": set()}

        if "attestations" not in self.gossip_data[attestation.slot].keys():
            self.gossip_data[attestation.slot].update({"attestations": set()})

        self.gossip_data[attestation.slot]["attestations"].add(attestation)

        # Cache the attestation.
        if attestation.block not in self.local_blockchain or attestation.slot == chainstate.slot:
            self.cached_attestations.add(attestation)
            return

        # Add the attestation to node state.
        if attestation.slot not in self.attestations.keys():
            self.attestations[attestation.slot] = {}

        self.attestations[attestation.slot][attestation.attestor] = attestation.block
        self.update_nodesAt_byLatestAttestation(attestation)

    def update_nodesAt_byLatestAttestation(self, latest_attestation: Attestation):
        """
        Function updates node state with the latest attestation.

        Parameters
        ----------
        Attestation: Attestation object: 
            attestation used to update the node's state.
        """
        if latest_attestation.attestor in self.nodes_at.keys():
            current_block_at = self.nodes_at[latest_attestation.attestor]

            if latest_attestation.slot > current_block_at.slot:
                self.nodes_at.update(
                    {latest_attestation.attestor: latest_attestation})
            return
        self.nodes_at[latest_attestation.attestor] = latest_attestation

    def check_cached_attestations(self, chainstate: ChainState):
        """
        Function includes node state cached attestations into attestations if criteria passes:
         - Block is known by the node
         - Attestation slot is atleast one slot older than current slot of the network

        Parameters
        ----------
        chainstate: ChainState object: 
            This the network state object passed on globally.
        """
        for attestation in self.cached_attestations.copy():
            if attestation.block in self.local_blockchain and chainstate.slot > attestation.slot:

                if attestation.slot not in self.attestations.keys():
                    self.attestations[attestation.slot] = {}

                if attestation.attestor not in self.attestations[attestation.slot].keys():
                    self.attestations[attestation.slot][attestation.attestor] = attestation.block
                    self.update_nodesAt_byLatestAttestation(attestation)

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
            raise "Setup Issue"

        # check if the slot is colliding
        new_block = Block(value='E{}_S{}'.format(
            chainstate.epoch, chainstate.slot), emitter=self, slot=chainstate.slot,
            parent=head_block, malicious=self.malicious)

        self.logging.debug('Block proposed {} in slot {} by {}, with head as {}'.format(
            new_block, chainstate.slot, self, head_block))

        # add block to local blockchain
        self.state.add_block(chainstate, new_block)

        chainstate.update_gods_view(block=new_block)

        return new_block

    def gossip_block(self, chainstate: ChainState, listening_node):
        if self.obstruct_gossiping == True:
            return
        listening_node.listen_block(chainstate, self)

    def listen_block(self,  chainstate: ChainState, gossiping_node,):
        """
        Listening node tries to read all the blocks from the gossiping node and update local state.
        Below are the conditions it follows:
        - listening block's slot should not be lesser than node finalized head slot
        - listening node should have the first block listened in a particular slot.
        """
        # as read in the gossiping rules, A Node should not accept a block where it does not
        # now its parent block of that listened block https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/p2p-interface.md#beacon_bloc

        for listening_slot in gossiping_node.state.gossip_data.keys():
            if listening_slot < self.gasper.finalized_head_slot or ("block" not in gossiping_node.state.gossip_data[listening_slot].keys()):
                continue

            listening_block = gossiping_node.state.gossip_data[listening_slot]["block"]

            # Not neccessary
            # # As node can listen only one proposed block in a particular slot
            # if listening_slot in self.state.gossip_data.keys() and "block" in self.state.gossip_data[listening_slot].keys():
            #     if self.state.gossip_data[listening_slot]["block"] != listening_block or self.state.gossip_data[listening_slot]["block"] != None:
            #         continue

            if listening_block not in self.state.local_blockchain:
                # Add to local of the node
                self.state.add_block(chainstate, listening_block)

        # Attest if the node is in committee and received a block for this slot
        if (self.is_attesting == True and chainstate.slot in self.state.gossip_data.keys()
            and "block" in self.state.gossip_data[chainstate.slot].keys()
                and self.state.gossip_data[chainstate.slot]["block"]):

            # Not neccesary as this should not happen twice as is_attesting is set to false if node already attests
            # if chainstate.slot in self.state.attestations.keys() and self in self.state.attestations[chainstate.slot].keys():
            #     return
            attestation = self.attest(chainstate)
            self.logging.debug('{} Attestor Node {}: Consensus View {} Consensus Attestations: {}'.format(attestation,
                                                                                                          self, self.gasper.consensus_chain, self.state.attestations))

    def attest(self, chainstate: ChainState):
        """Create the Attestation for the current head of the chain block.
        """
        _, attesting_block = self.gasper.get_block2attest(
            chainstate, self.state)

        # Create the attestation for this slot
        attestation = Attestation(self, attesting_block, chainstate.slot)

        self.logging.debug('Block attested {} in slot {} by {}'.format(
            attesting_block, chainstate.slot, self))

        self.state.add_attestation(chainstate, attestation)

        chainstate.update_gods_view(attestation=attestation)
        # As a node must attest only once in a slot
        self.is_attesting = False

        return attestation

    def gossip_attestation(self, chainstate: ChainState, listening_node):
        if self.obstruct_gossiping == True:
            return
        listening_node.listen_attestation(chainstate, self)

    def listen_attestation(self, chainstate, gossiping_node):
        """
        Listening node tries to read all the attestations from the gossiping node and update local state.
        Below are the conditions it follows:
        - listening node should accept an attestation only if the attestation slot within ATTESTATION_PROPAGATION_SLOT_RANGE
        - listening node should accept an attestation of the same epoch only.
        - Further adding into the state has further validation check in the `NodeState` class `add_attestation` function.
        """
        # as read in the gossiping attestation rules, A Node should not accept an attestation until ATTESTATION_PROPAGATION_SLOT_RANGE of slots
        # now its parent block of that listened block https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/p2p-interface.md#beacon_aggregate_and_proof
        for listening_slot in gossiping_node.state.gossip_data.keys():
            if (listening_slot + ATTESTATION_PROPAGATION_SLOT_RANGE >= chainstate.slot >= listening_slot
                    and chainstate.slot // SLOTS_PER_EPOCH == listening_slot // SLOTS_PER_EPOCH):
                if "attestations" not in gossiping_node.state.gossip_data[listening_slot].keys():
                    continue

                for attestation in gossiping_node.state.gossip_data[
                        listening_slot]["attestations"]:
                    self.state.add_attestation(chainstate, attestation)

    def __repr__(self):
        return '<Node {}>'.format(self.id)
