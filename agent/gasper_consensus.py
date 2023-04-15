
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
    cummulative_weight_subTree = {}

    def __init__(self, genesis_block, logging=logging):
        self.consensus_chain = {self.finalized_head_slot: genesis_block}
        self.logging = logging.getLogger('ConsensusAlgo')

    def get_cummulative_weight_subTree(self, given_block: Block, node_state, chainstate: ChainState):
        """
        Function provides the weight of a block by cummulatively summing the attestation weight of the block and its descedant

        If a node's proposer boost block matches the block analyzed, then this functions also adds the proposer vote boost times slot committee weight

        Parameters
        ----------
        given_block: Block object: 
            This is the Block to be used to update the proposer boost.
        node_state: NodeState object:
            This is NodeState of the node for which the LMD GHOST uses the attestations
        chainstate: ChainState object: 
            This the network state object passed on globally to provide current status of the network.
        """
        # Memoizing the subtree weights
        if given_block in self.cummulative_weight_subTree.keys():
            return self.cummulative_weight_subTree[given_block]

        total_weights = 0

        for attestation in node_state.nodes_at.values():
            if given_block == attestation.block:
                total_weights += 1

        if len(given_block.children) != 0:
            for block in [block if block in node_state.local_blockchain else block for block in given_block.children]:
                total_weights += self.get_cummulative_weight_subTree(
                    block, node_state, chainstate)

        # using booster weight for the blocks which are in
        if node_state.proposer_booster == given_block and chainstate.slot == node_state.proposer_booster.slot:
            total_weights += chainstate.proposer_vote_boost * chainstate.slot_committee_weight

        self.cummulative_weight_subTree[given_block] = total_weights
        return total_weights

    def lmd_ghost(self, chainstate: ChainState, node_state):
        """
        Function executes the fork choice Hybrid version of the LMD GHOST.

        Parameters
        ----------
        node_state: NodeState object:
            This is NodeState of the node for which the LMD GHOST uses the attestations
        chainstate: ChainState object: 
            This the network state object passed on globally to provide current status of the network.
        """
        # check the cached attestations and update the nodes_at
        node_state.check_cached_attestations(chainstate)

        # reset the subtree weights
        self.cummulative_weight_subTree = {}
        previous_head = self.consensus_chain[self.finalized_head_slot]

        # clear the previously justified slots
        self.consensus_chain = {slot: block for slot, block in self.consensus_chain.items(
        ) if slot <= self.finalized_head_slot}

        while (previous_head):
            known_children = [
                block for block in previous_head.children if block in node_state.local_blockchain]

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

            previous_head = heavyBlock

        # # As there is no finality gadget, this was placed here. To try to emulate similar behavior.
        # Conditions: the finalized head slot block is updated every SLOTS_PER_EPOCH.
        if (chainstate.slot - 1) % SLOTS_PER_EPOCH == 0 and chainstate.slot > SLOTS_PER_EPOCH:
            self.finalized_head_slot = max(
                max(self.consensus_chain.keys()), self.finalized_head_slot)

    def get_head_block(self):
        return [(slot, block) for slot, block in self.consensus_chain.items() if slot == max(self.consensus_chain.keys())][0]

    def get_block2attest(self, chain_state: ChainState, node_state):
        self.lmd_ghost(chain_state, node_state)
        return self.get_head_block()

    # Benjamin Version of LMD GHOST
    #
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
        F : float
            The branching ratio
        """
        main_chain = set(
            [block for slot, block in self.consensus_chain.items()])
        orphan_blocks = all_known_blocks - main_chain

        counter = 0
        for block in main_chain:
            for orphan in orphan_blocks:
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
