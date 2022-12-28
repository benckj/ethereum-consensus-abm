
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

    def __init__(self, genesis_block):
        self.consensus_chain = {self.finalized_head_slot: genesis_block}

    def getLatestAttestationsBySlot(self, unneeded_slots, attestations):
        return {slot: node_attestations for slot,
                node_attestations in attestations.items() if slot > unneeded_slots}

    def prune_attestatations_byInclusionDelay(self, needed_slot, attestations):
        return {slot: node_attestations for slot,
                node_attestations in attestations.items() if slot <= needed_slot - MIN_ATTESTATION_DELAY}

    def get_cummulative_weight_subTree(self, slot, blockTree, fork_choice_attestations):
        # optimize this with dynamic programming approach
        total_weights = 0

        if len(blockTree) == 0 or slot not in fork_choice_attestations.keys():
            return 0

        slot_block_weights = {}
        for block in fork_choice_attestations[slot].values():
            if block in slot_block_weights.keys():
                slot_block_weights[block] += 1
            else:
                slot_block_weights[block] = 1

        for block in blockTree:
            if len(block.children) == 0 and block in slot_block_weights.keys():
                total_weights += slot_block_weights[block]
            elif block in slot_block_weights.keys():
                total_weights += slot_block_weights[block] + self.get_cummulative_weight_subTree(
                    slot+1, block.children, fork_choice_attestations)
            else:
                total_weights += self.get_cummulative_weight_subTree(
                    slot+1, [block], fork_choice_attestations)

        return total_weights

    def get_heaviest_block(self, slot, node_attestations, fork_choice_attestations, parent_block):
        inverse_node_attestations = {}

        if len(parent_block.children) == 0:
            return None

        for node, block in node_attestations.items():
            if block in parent_block.children:
                inverse_node_attestations[block] = inverse_node_attestations.get(
                    block, []) + [node]

        if len(inverse_node_attestations.keys()) == 0:
            return None

        # fetch the block's subtree weight
        block_w_weights = {block: self.get_cummulative_weight_subTree(
            slot+1, [block for block in block.children if block.slot == slot+1], fork_choice_attestations) for block in inverse_node_attestations.keys()}

        total_block_weights = {block: block_w_weights[block] + len(
            nodes) for block, nodes in inverse_node_attestations.items()}

        block_with_max_votes = [block for block, weight in total_block_weights.items(
        ) if weight == max(total_block_weights.values())]

        if len(block_with_max_votes) == 1:
            return block_with_max_votes[0]

        return [block for block, weights in block_w_weights.items() if weights == max(block_w_weights.values())][0]

    def last_consensus_block(self, slot):
        if slot in self.consensus_chain.keys() and self.consensus_chain[slot]:
            return self.consensus_chain[slot]
        else:
            return self.last_consensus_block(slot-1)

    def lmd_ghost(self, attestations):
        # prune the finalized slot votes of all the node
        fork_choice_attestations = self.getLatestAttestationsBySlot(
            self.finalized_head_slot, attestations)

        justified_slot = None
        for slot, node_attestations in fork_choice_attestations.items():
            last_block = self.last_consensus_block(
                justified_slot if justified_slot else self.finalized_head_slot)
            heavyBlock = self.get_heaviest_block(
                slot, node_attestations, fork_choice_attestations, last_block)
            justified_slot = slot

            # # Handling empty slots
            # if heavyBlock == None:
            #     continue
            self.consensus_chain[slot] = heavyBlock

            # As there is no finality gadget, this was placed here. To try to emulate similar behavior.
            if justified_slot % FFG_FINALIZE_SLOTS == 0:
                self.finalized_head_slot = max(
                    justified_slot-2, self.finalized_head_slot)

    def get_head_block(self):
        for slot, block in sorted(self.consensus_chain.items(), reverse=True):
            if block:
                return (slot,block) 

    def get_block2attest(self, block, attestations):
        self.lmd_ghost(attestations)
        current_head_slot, current_head_block = self.get_head_block()

        # Compare the block slot vs the head_slot
        # If the head_slot is greater and this block is propose in the already consensus achieved slots.
        # This block does not have enough attestations to reach consensus or this block was listened late in that particular slot.
        # So, we return the previous head as the current head block again.
        if current_head_slot >= block.slot:
            return current_head_block

        # If the block is proposed in the later slots and listened by this node, then this is great and this has to be attested.
        # [Techincally] If block.slot > current_head_slot:
        return block

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
        return len([block for slot, block in self.consensus_chain.items() if block])/ len(all_known_blocks)

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

        main_chain = set([block for slot, block in self.consensus_chain.items() if block])
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
