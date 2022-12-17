
from constants import *
import numpy as np
'''
FUNCTIONS
'''
'''
LMD Ghost following functions handle LMD Ghost Evaluation of Blocks
'''

class Gasper:
    finalized_head_slot = -1
    consensus_chain = {}

    def __init__(self, genesis_block):
        self.consensus_chain = {self.finalized_head_slot: genesis_block}

    def prune_attestationsBySlot(self, unneeded_slots, attestations):
        return {slot: node_attestations for slot,
                node_attestations in attestations.items() if slot > unneeded_slots}

    def get_cummulative_weight_subTree(self, slot, blockTree, fork_choice_attestations):
        # optimize this with dynamic programming approach
        total_weights = 0
        # Will be used in future for votes counting
        subtree_attestations_by_slot = self.prune_attestationsBySlot(
            slot, fork_choice_attestations)
        for block in blockTree:
            if len(block.children) == 0:
                total_weights += 1  # replace the 1 with actual number of votes
            else:
                total_weights += self.get_cummulative_weight_subTree(
                    slot+1, block.children, fork_choice_attestations) + 1  # replace the 1 with actual number of votes
        return total_weights

    def get_heaviest_block(self, slot, node_attestations, fork_choice_attestations, parent_block):
        inverse_node_attestations = {}
        if len(parent_block.children) == 0:
            return None
        for node, block in node_attestations.items():
            if block in parent_block.children:
                inverse_node_attestations[block] = inverse_node_attestations.get(
                    block, []) + [node]

        # fetch the block's subtree weight
        block_w_weights = {block: self.get_cummulative_weight_subTree(
            slot+1, block.children, fork_choice_attestations) for block in inverse_node_attestations.keys()}

        total_block_weights = {block: block_w_weights[block] + len(
            nodes) for block, nodes in inverse_node_attestations.items()}

        block_with_max_votes = [block for block, weight in total_block_weights.items(
        ) if weight == max(total_block_weights.values())]

        if len(block_with_max_votes) == 1:
            return block_with_max_votes[0]

        return [block for block, weights in block_w_weights.items() if weights == max(block_w_weights.values())][0]

    def last_consensus_slot(self, slot):
        if slot in self.consensus_chain.keys():
            return slot
        else:
            self.last_consensus_slot(slot-1)

    def lmd_ghost(self, attestations):
        # prune the finalized slot votes of all the node
        # [TODO] handle empty slots.
        fork_choice_attestations = self.prune_attestationsBySlot(
            self.finalized_head_slot, attestations)

        last_iterated_slot = 0
        for slot, node_attestations in fork_choice_attestations.items():
            last_slot = self.last_consensus_slot(slot)
            heavyBlock = self.get_heaviest_block(
                slot, node_attestations, fork_choice_attestations, self.consensus_chain[last_slot])
            last_iterated_slot = slot
            # Handling empty slots
            if heavyBlock == None:
                continue
            self.consensus_chain[slot] = heavyBlock

        # As there is no finality gadget, this was placed here. To try to emulate similar behavior.
        if last_iterated_slot % SLOTS_PER_EPOCH == 0:
            self.finalized_head_slot = max(
                last_iterated_slot-2, self.finalized_head_slot)

    def get_head_block(self):
        return {slot: block for slot, block in self.consensus_chain.items() if slot == max(self.consensus_chain.keys())}.copy().popitem()

    def get_block2attest(self, block, attestations):
        self.lmd_ghost(attestations)
        current_head_slot, current_head_block = self.get_head_block()

        # If there is an attestation already for this block, The block has a chance to be in consensus_chain.
        # So we will check if the consensus_chain contains this block and return based on it
        if len([v for k, v in self.consensus_chain.items() if v == block]):
            return block

        # If the block produced is under the head of the canonical chain then return the block
        if block.parent == current_head_block:
            return block

        # If there is no attestation for this block and the block's parent is not current head
        # Check if the block head is in the Consensus_chain
        block_parent_slot, _ = [(k, v) for k,
                                v in self.consensus_chain.items() if v == block.parent][0]

        # If consensus_chain contains the block head.
        if block_parent_slot:
            # Compare the block slot vs the head_slot
            # If the head_slot is greater and this block is propose in the already consensus achieved slots, This block does not have enough attestations to reach consensus
            if current_head_slot >= block.slot:
                return current_head_block
            # If the block slot is higher than the current head slot and the head of this block is in our consensus chain, this means, we have fork again in the block slot.
            # As there is no Proposer boost, We weigh the previous head block but not the block don't have any attestations for it. So we see that the next
            if block.slot > current_head_slot:
                return current_head_block

        # Don't see a possible to see a possiblity where the block parent is not accounted but block could get included as proposer boost is not involved.
        # Later I have to added this into the codebase.
        # if len(head_block) == 0:
        #     block_head_height_difference = block.parent.height - current_head.height
        #     block_head_slot_difference = block.parent.slot - current_head.slot
        #     if block_height_difference == 1:
        #         if block.parent == current_head or current_head.slot < block.parent.slot:
        #             return block
        #     # The head of the block does not match, need to check if the head of the block exists with me
        #         if current_head.slot >= block.parent.slot or block_head_height_difference < 0:
        #             # what would I do if the block.parent is not equal to current head
        #             # As proposer boost is not there in the implementation, now compare just weights of both forks from the common block.
        #             return current_head

        return current_head_block

    def calculate_mainchain_rate(self, local_blockchain):
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

        head_block = self.get_head_block()
        main_chain = head_block.predecessors
        return len(main_chain)/len(local_blockchain)

    def calculate_branch_ratio(self, local_blockchain):
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

        head_block = self.get_head_block()
        main_chain = head_block.predecessors
        orphan_chain = local_blockchain - main_chain

        counter = 0
        for block in main_chain:
            for orphan in orphan_chain:
                if block.parent == orphan.parent:
                    counter += 1

        return counter/len(main_chain)

    def calculate_entropy(local_blockchain):
        """Compute the entropy of the in-degree distribution of the blocktree
        """
        # compute the degree frequency
        degrees = np.array([len(block.children) for block in local_blockchain])
        degrees_unique, degrees_counts = np.unique(degrees, return_counts=True)
        degrees_frequencies = degrees_counts/degrees_counts.sum()
        tmp = 0
        for prob in degrees_frequencies:
            tmp -= prob*np.log(prob)
        return tmp
