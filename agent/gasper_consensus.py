
from .constants import *
from .base_utils import *

import numpy as np
import logging
from timebudget import timebudget
timebudget.set_quiet()  # don't show measurements as they happen
timebudget.report_at_exit()  # Generate report when the program exits
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
    cummulative_weight_subTree = {}

    def __init__(self, genesis_block, logging=logging):
        self.consensus_chain = {self.finalized_head_slot: genesis_block}
        self.logging = logging.getLogger('ConsensusAlgo')

    @timebudget
    def get_cummulative_weight_subTree(self, given_block, node_state, chainstate):
        # Memoizing the subtree weights
        if given_block in self.cummulative_weight_subTree.keys():
            return self.cummulative_weight_subTree[given_block]

        total_weights = 0

        for attestation in node_state.nodes_at.values():
            if given_block == attestation.block:
                total_weights += 1

        if len(given_block.children) != 0:
            for block in [node_state.get_block(block) if block in node_state.local_blockchain else block for block in given_block.children if chainstate.slot > block.slot]:
                total_weights += self.get_cummulative_weight_subTree(
                    block, node_state, chainstate)

        # using booster weight for the blocks which are in
        if (chainstate.slot == given_block.slot or chainstate.slot == given_block.slot+1) and given_block in node_state.local_blockchain:
            total_weights += given_block.booster_weight * chainstate.slot_committee_weight

        self.cummulative_weight_subTree[given_block] = total_weights
        return total_weights

    @timebudget
    def lmd_ghost(self, chainstate, node_state):
        node_state.check_cached_attestations(chainstate)
        # reset the subtree weights
        self.cummulative_weight_subTree = {}

        previous_head = self.consensus_chain[self.finalized_head_slot]
        # clear the previously justified slots
        self.consensus_chain = {slot: block for slot, block in self.consensus_chain.items(
        ) if slot <= self.finalized_head_slot}

        while (previous_head):
            known_children = [node_state.get_block(
                block) for block in previous_head.children if block in node_state.local_blockchain and chainstate.slot > block.slot]

            if len(known_children) == 0:
                heavyBlock = None

            elif len(known_children) == 1:
                heavyBlock = known_children[0]

            else:
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

            if heavyBlock:
                self.consensus_chain[heavyBlock.slot] = heavyBlock

                # # As there is no finality gadget, this was placed here. To try to emulate similar behavior.
                if heavyBlock.slot % FFG_FINALIZE_SLOTS == 0:
                    self.finalized_head_slot = max(
                        heavyBlock.slot, self.finalized_head_slot)

            previous_head = heavyBlock
    
    ## Benjamin Version of LMD GHOST
    # @timebudget
    # def lmd_ghost(self, chainstate, node_state):
    #     node_state.check_cached_attestations(chainstate)
    #     self.consensus_chain = {slot: block for slot, block in self.consensus_chain.items(
    #     ) if slot <= self.finalized_head_slot}
    #     attest = {k: v.block for k, v in node_state.nodes_at.items()}
    #     # lowest_attested_block_height = min(b.height for b in attest.values())
    #     # blocks =
    #     # {b for b in blockchain if b.height >= lowest_attested_block_height}
    #     parent_blocks = {b.parent for b in node_state.local_blockchain}
    #     leaves = node_state.local_blockchain - parent_blocks

    #     chains = {b: b.predecessors for b in leaves}

    #     inverse_attestations = {}
    #     for n, b in attest.items():
    #         inverse_attestations[b] = inverse_attestations.get(b, []) + [n]

    #     heads_of_chains = {}
    #     for head_of_chain, chain in chains.items():
    #         val = 0
    #         for block in chain:
    #             if block in inverse_attestations.keys():
    #                 for node in inverse_attestations[block]:
    #                     val += 1
    #         heads_of_chains[head_of_chain] = val
    #     max_lmd_val = max(heads_of_chains.values())
    #     max_heads = [key for key, value
    #                  in heads_of_chains.items() if value == max_lmd_val]
    #     # introduce tiebreaker
    #     # sorted_max_heads = sorted(max_heads, key=lambda x: x.height, reverse=True)
    #     # TODO: use the rng
    #     np.random.shuffle(max_heads)
    #     sorted_max_heads = max_heads
    #     current_block_root = sorted_max_heads[0]
    #     while(current_block_root):
    #         if current_block_root.slot > self.finalized_head_slot:
    #             self.consensus_chain[current_block_root.slot] = current_block_root
    #             current_block_root = current_block_root.parent
    #         else:
    #             return

    def get_head_block(self):
        for slot, block in sorted(self.consensus_chain.items(), key=lambda item: item[0],  reverse=True):
            if block:
                return (slot, block)

    def get_block2attest(self, chain_state, node_state):
        self.lmd_ghost(chain_state, node_state)
        current_head_slot, current_head_block = self.get_head_block()
        latest_block = node_state.latest_block

        # Compare the block slot vs the head_slot
        # If the head_slot is greater and this block is propose in the already consensus achieved slots.
        # This block does not have enough attestations to reach consensus or this block was listened late in that particular slot.
        # So, we return the previous head as the current head block again.
        if current_head_slot >= latest_block.slot:
            return chain_state.slot, current_head_block

        # If the block produced is under the head of the canonical chain then return the block
        if latest_block.parent == current_head_block:
            return latest_block.slot, latest_block

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
        return len([block for slot, block in self.consensus_chain.items()]) / len(all_known_blocks)

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
            [block for slot, block in self.consensus_chain.items()])
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
