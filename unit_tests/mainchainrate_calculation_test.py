"""Module providing Function to change path"""
import sys
sys.path.append("../")
from agent.node import Node
from agent.base_utils import Block
import unittest


##################
# actual testing

class MainChainRate_TestCases(unittest.TestCase):
    def test(self):
        """Simple test
        """
        #################
        # mock blockchain
        mock_blockchain = set()

        genesis = Block('0', "genesis", 0)
        mock_node = Node(genesis)

        mock_blockchain.update([genesis])

        block_1 = Block(
            '1',
            mock_node,
            1,
            genesis

        )
        mock_blockchain.update([block_1])

        block_2 = Block(
            '2',
            mock_node,
            2,
            block_1
        )
        mock_blockchain.update([block_2])

        block_3 = Block(
            '3',
            mock_node,
            3,
            block_1
        )
        mock_blockchain.update([block_3])

        block_4 = Block(
            '4',
            mock_node,
            4,
            block_2
        )
        mock_blockchain.update([block_4])

        ###################
        # mock attestations

        mock_attestations = {
            1: {mock_node: block_1},
            2: {mock_node: block_1},
            3: {mock_node: block_3},
            4: {mock_node: block_4},
        }

        ###################
        # mock consensus
        mock_node.gasper.lmd_ghost(mock_attestations)

        # testing
        self.assertEqual(mock_node.gasper.calculate_mainchain_rate(mock_blockchain),0.6)