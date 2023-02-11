"""Module providing Function to change path"""
import sys
sys.path.extend("../")

import unittest
from agent.base_utils import Block, ChainState, Attestation
from agent.node import Node


##################
# actual testing

class BranchRatio_TestCases(unittest.TestCase):
    def test(self):
        """Simple test
        """
        #################
        # mock blockchain
        mock_blockchain = set()

        genesis = Block('0', "genesis", 0)
        mock_node = Node(genesis, 0)
        mock_node1 = Node(genesis, 1)
        mock_node2 = Node(genesis, 2)
        analyze_node = Node(genesis,3)

        chain_state = ChainState(14, 1, 2, 0, 0, genesis)
        mock_blockchain.update([genesis])

        block_1 = Block(
            '1',
            mock_node,
            1,
            genesis

        )
        analyze_node.state.add_block(chain_state, block_1)
        mock_blockchain.update([block_1])

        block_2 = Block(
            '2',
            mock_node,
            2,
            block_1
        )
        chain_state.update_slot(3)
        analyze_node.state.add_block(chain_state, block_2)
        mock_blockchain.update([block_2])

        block_3 = Block(
            '3',
            mock_node,
            3,
            block_1
        )
        chain_state.update_slot(4)
        analyze_node.state.add_block(chain_state, block_3)
        mock_blockchain.update([block_3])

        block_4 = Block(
            '4',
            mock_node,
            4,
            block_2
        )
        chain_state.update_slot(5)
        analyze_node.state.add_block(chain_state, block_4)
        mock_blockchain.update([block_4])
        
        ###################
        # mock attestations

        attestations = {
            1: {mock_node: block_1, mock_node1: block_1, mock_node2: block_1},
            2: {mock_node: block_1, mock_node1: block_1, mock_node2: block_2},
            3: {mock_node: block_3, mock_node1: block_3, mock_node2: block_2},
            4: {mock_node: block_3, mock_node1: block_3, mock_node2: block_4},
        }

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                analyze_node.state.add_attestation(
                    Attestation(node, block, slot))

        ###################
        # mock consensus
        analyze_node.gasper.lmd_ghost(chain_state, analyze_node.state)

        # testing
        self.assertEqual(
            analyze_node.gasper.calculate_branch_ratio(mock_blockchain), 1/3)
