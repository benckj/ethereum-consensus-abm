"""Module providing Function to change path"""
import numpy as np
import unittest
from agent.node import Node
from agent.base_utils import Block, ChainState
import sys
sys.path.append("../")

##################
# actual testing


class Entropy_TestCases(unittest.TestCase):
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

        mock_blockchain.update([genesis])

        block_1 = Block(
            '1',
            mock_node,
            1,
            genesis

        )
        mock_node.state.local_blockchain.update([block_1])
        mock_blockchain.update([block_1])

        block_2 = Block(
            '2',
            mock_node,
            2,
            block_1
        )
        mock_node.state.local_blockchain.update([block_2])
        mock_blockchain.update([block_2])

        block_3 = Block(
            '3',
            mock_node,
            3,
            block_2
        )
        mock_node.state.local_blockchain.update([block_3])
        mock_blockchain.update([block_3])

        block_4 = Block(
            '4',
            mock_node,
            4,
            block_3
        )
        mock_node.state.local_blockchain.update([block_4])
        mock_blockchain.update([block_4])

        ###################
        # mock attestations

        mock_node.state.attestations = {
            1: {mock_node: block_1, mock_node1: block_1, mock_node2: block_1},
            2: {mock_node: block_1, mock_node1: block_1, mock_node2: block_2},
            3: {mock_node: block_3, mock_node1: block_3, mock_node2: block_2},
            4: {mock_node: block_3, mock_node1: block_3, mock_node2: block_4, },
        }

        ###################
        # mock consensus
        chain_state = ChainState(50, 1, 5, 0, 0, genesis)
        mock_node.gasper.lmd_ghost(chain_state, mock_node.state)

        # testing
        self.assertEqual(mock_node.gasper.calculate_entropy(
           mock_blockchain), np.log(5)-(4/5)*np.log(4))
