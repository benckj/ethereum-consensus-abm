
from .constants import *
from .base_utils import *

import numpy as np
import logging
'''
FUNCTIONS
'''
'''
LMD Ghost following functions handle LMD Ghost Evaluation of Blocks
'''


class Gasper:
    finalized_head_slot = 0
    consensus_chain = {}
    headblock_weights = {}
    accounted_attestations = set()
    nodes_at = {}

    def __init__(self, genesis_block, logging=logging):
        self.consensus_chain = {self.finalized_head_slot: genesis_block}
        self.logging = logging.getLogger('ConsensusAlgo')

    def get_latest_attestations(self, attestations):
        if len(attestations) == 0:
            return self.nodes_at

        attestations_in_tuples = set()
        for slot, node_attestations in sorted(attestations.items()):
            if (max(attestations.keys()) >= slot >= (max(attestations.keys()) - 2 * FFG_FINALIZE_SLOTS)):
                for node, block in node_attestations.items():
                    attestations_in_tuples.update(
                        [Attestation(node, block, slot)])

        self.logging.debug(attestations_in_tuples)
        new_attestations = attestations_in_tuples - self.accounted_attestations
        self.accounted_attestations = attestations_in_tuples
        self.logging.debug(new_attestations)
        for attestation in new_attestations:
            self.nodes_at.update({attestation.attestor: (
                attestation.slot, attestation.block)})

        latest_attestation = {}
        for node, slot_attestations in self.nodes_at.items():
            if slot_attestations[0] not in latest_attestation.keys():
                latest_attestation.update({slot_attestations[0]: {
                    node: slot_attestations[1]}})
            else:
                latest_attestation[slot_attestations[0]].update(
                    {node: slot_attestations[1]})

        return latest_attestation

    def prune_attestatations_byInclusionDelay(self, needed_slot, attestations):
        return {slot: node_attestations for slot,
                node_attestations in attestations.items() if slot < needed_slot}

    def get_cummulative_weight_subTree(self, given_block, node_state, chainstate):
        total_weights = 0

        for slot in node_state.attestations.keys():
            for block in node_state.attestations[slot].values():
                if given_block == block:
                    total_weights += 1

        if len(given_block.children) != 0:
            for block in [node_state.get_block(block) if block in node_state.local_blockchain else block for block in given_block.children]:
                total_weights += self.get_cummulative_weight_subTree(
                    block, node_state, chainstate)

        # using booster weight for the blocks which are in
        return total_weights + given_block.booster_weight * chainstate.slot_committee_weight if chainstate.slot == given_block.slot and given_block in node_state.local_blockchain else 0

    def lmd_ghost(self, chainstate, node_state):
        # get the latest attestations out of all know attestations
        fork_choice_attestations = self.get_latest_attestations(
            self.prune_attestatations_byInclusionDelay(chainstate.slot, node_state.attestations))

        if len(fork_choice_attestations.keys()) == 0:
            return

        previous_head = self.consensus_chain[self.finalized_head_slot]

        # clear the previous justified slots
        self.consensus_chain = {slot: block for slot, block in self.consensus_chain.items(
        ) if slot <= self.finalized_head_slot}

        while (previous_head):
            known_children = [node_state.get_block(
                block) for block in previous_head.children if block in node_state.local_blockchain]

            if len(known_children) == 0:
                return

            block_weights = {block: self.get_cummulative_weight_subTree(
                block, node_state, chainstate) for block in known_children}

            block_with_max_votes = [block for block, weight in block_weights.items(
            ) if weight == max(block_weights.values())]
            # As seen in the ethereum about ties handling using the max funcrtion which selects the first options if it is equal
            # https://github.com/ethereum/annotated-spec/blob/master/phase0/fork-choice.md#get_latest_attesting_balance
            if len(block_with_max_votes) > 1:
                block_with_max_votes = [block for block in block_with_max_votes if block.slot == min(
                    [block.slot for block in block_with_max_votes])]

            heavyBlock = min(block_with_max_votes,
                             key=lambda block: block.value)

            self.consensus_chain[heavyBlock.slot] = heavyBlock

            # # As there is no finality gadget, this was placed here. To try to emulate similar behavior.
            if heavyBlock.slot % FFG_FINALIZE_SLOTS == 0:
                self.finalized_head_slot = max(
                    heavyBlock.slot, self.finalized_head_slot)

            previous_head = heavyBlock

    def get_head_block(self):
        for slot, block in sorted(self.consensus_chain.items(), key=lambda item: item[0],  reverse=True):
            if block:
                return (slot, block)

    def get_block2attest(self, chain_state, node_state):
        self.lmd_ghost(chain_state, node_state)
        current_head_slot, current_head_block = self.get_head_block()
        latest_block = node_state.local_blockchain.copy().pop()

        # Compare the block slot vs the head_slot
        # If the head_slot is greater and this block is propose in the already consensus achieved slots.
        # This block does not have enough attestations to reach consensus or this block was listened late in that particular slot.
        # So, we return the previous head as the current head block again.
        if current_head_slot >= latest_block.slot:
            return chain_state.slot, current_head_block

        # If the block produced is under the head of the canonical chain then return the block
        if latest_block.parent == current_head_block:
            return chain_state.slot, latest_block

        # If the block is proposed in the later slots and does not have the latest computed
        return chain_state.slot, current_head_block

    def calculate_mainchain_rate(self, all_known_blocks):
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
        return len([block for slot, block in self.consensus_chain.items() if block]) / len(all_known_blocks)

    def calculate_branch_ratio(self, all_known_blocks):
        """Compute the branch Ratio, which measures how often forks happen

        Parameters:
        -----------
        blockchain : A list of Block objects
        Returns:
        --------
        F : float
            The branching ratio
        """

        main_chain = set(
            [block for slot, block in self.consensus_chain.items() if block])
        orphan_chain = all_known_blocks - main_chain

        counter = 0
        for block in main_chain:
            for orphan in orphan_chain:
                if block.parent == orphan.parent:
                    counter += 1

        return counter/len(main_chain)

    def calculate_entropy(self, all_known_blocks):
        """Compute the entropy of the in-degree distribution of the blocktree
        """
        # compute the degree frequency
        degrees = np.array([len(block.children) for block in all_known_blocks])
        degrees_unique, degrees_counts = np.unique(degrees, return_counts=True)
        degrees_frequencies = degrees_counts/degrees_counts.sum()
        tmp = 0
        for prob in degrees_frequencies:
            tmp -= prob*np.log(prob)
        return tmp
