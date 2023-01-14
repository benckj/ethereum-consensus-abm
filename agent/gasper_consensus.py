
from .constants import *
import numpy as np
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

    def __init__(self, genesis_block):
        self.consensus_chain = {self.finalized_head_slot: genesis_block}

    def get_latest_attestations(self, attestations):
        chunked_attestation = {slot: node_attestations for slot,
                               node_attestations in attestations.items() if slot > self.finalized_head_slot}
        inv_latest_attestaion = {}
        latest_attestation = {}

        for slot, node_attestation in chunked_attestation.items():
            for node, block in node_attestation.items():
                inv_latest_attestaion.update({node: (slot, block)})

        for node, slot_attestations in inv_latest_attestaion.items():
            if slot_attestations[0] not in latest_attestation.keys():
                latest_attestation.update({slot_attestations[0]: {
                    node: slot_attestations[1]}})
            else:
                latest_attestation[slot_attestations[0]].update( 
                    {node: slot_attestations[1]})

        return latest_attestation

    def prune_attestatations_byInclusionDelay(self, needed_slot, attestations):
        return {slot: node_attestations for slot,
                node_attestations in attestations.items() if slot <= needed_slot - MIN_ATTESTATION_DELAY}

    def get_cummulative_weight_subTree(self, given_block, attestations):
        total_weights = 0

        for slot in attestations.keys():
            for block in attestations[slot].values():
                if given_block == block:
                    total_weights += 1

        if len(given_block.children) != 0:
            for block in given_block.children:
                total_weights += self.get_cummulative_weight_subTree(block, attestations)

        return total_weights

    def get_heaviest_block(self, slot, attestations, local_blockchain):
        # fetch the block's subtree weight
        block_weights = {block: self.get_cummulative_weight_subTree(
            block, attestations) for block in local_blockchain if block.slot == slot}


        block_with_max_votes = [block for block, weight in block_weights.items(
        ) if weight == max(block_weights.values())]

        if len(block_with_max_votes) == 0:
            return None

        ## As seen in the ethereum about ties handling using the max funcrtion which selects the first options if it is equal
        # https://github.com/ethereum/annotated-spec/blob/master/phase0/fork-choice.md#get_latest_attesting_balance
        return block_with_max_votes[0]

    def lmd_ghost(self, local_blockchain, attestations):
        # get the latest attestations out of all know attestations
        fork_choice_attestations = self.get_latest_attestations(attestations)

        if len(fork_choice_attestations.keys())==0:
            return

        # justified_slot = None
        for slot in range(1, max(fork_choice_attestations.keys()) + 1):
            heavyBlock = self.get_heaviest_block(
                slot, fork_choice_attestations, local_blockchain)
            # justified_slot = slot

            self.consensus_chain[slot] = heavyBlock

            # # As there is no finality gadget, this was placed here. To try to emulate similar behavior.
            # if justified_slot % FFG_FINALIZE_SLOTS == 0:
            #     self.finalized_head_slot = max(
            #         justified_slot, self.finalized_head_slot)

    def get_head_block(self):
        for slot, block in sorted(self.consensus_chain.items(), key=lambda item: item[0],  reverse=True):
            if block:
                return (slot, block)

    def get_block2attest(self, local_blockchain, attestations):
        self.lmd_ghost(local_blockchain, attestations)
        current_head_slot, current_head_block = self.get_head_block()
        latest_block = local_blockchain.pop()

        # Compare the block slot vs the head_slot
        # If the head_slot is greater and this block is propose in the already consensus achieved slots.
        # This block does not have enough attestations to reach consensus or this block was listened late in that particular slot.
        # So, we return the previous head as the current head block again.
        if current_head_slot >= latest_block.slot:
            return current_head_block

        # If the block produced is under the head of the canonical chain then return the block
        if latest_block.parent == current_head_block:
            return latest_block

        # If the block is proposed in the later slots and does not have the latest computed
        return current_head_block

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
