
from agent.node import *
from agent.base_utils import *
import unittest
import sys
sys.path.append('../')


class GHOST_TestCase(unittest.TestCase):
    def setUp(self):
        self.no_of_nodes = 10
        self.genesis_block = Block('0', "genesis", 0)
        self.nodes = [Node(self.genesis_block, i)
                      for i in range(self.no_of_nodes)]

    def test_onelevel_heavyweight(self):
        # Just to check Heavy weight
        self.blockchain = set()
        block1 = Block('1B', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1A', self.nodes[1], 1, self.genesis_block)
        self.blockchain.update([block1])
        self.blockchain.update([block2])
        self.attestation = {1: {self.nodes[i]: block1 if i in range(
            int(0.6 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block})
        self.nodes[4].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

    def test_onelevel_tieweight(self):
        # Have to check the latest message driven, will have to talk to nicolo or benjamin or casper about this
        self.blockchain = set()
        block1 = Block('1B', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1A', self.nodes[1], 1, self.genesis_block)
        self.blockchain.update([block1])
        self.blockchain.update([block2])
        self.attestation = {1: {self.nodes[i]: block1 if i in range(
            int(0.5 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block})
        self.nodes[4].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block2})

    def test_twolevel_heavyweight(self):
        self.blockchain = set()
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 1, self.genesis_block)
        self.blockchain.update([block1])
        self.blockchain.update([block2])
        self.attestation = {1: {self.nodes[i]: block1 if i in range(
            int(0.5 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}
        # Retest the level one here
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block})
        self.nodes[4].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        # Logic to see if the consensus chain shifts the slot 1 also
        block3 = Block('2A', self.nodes[0], 2, block1)
        block4 = Block('2B', self.nodes[0], 2, block1)
        block5 = Block('2C', self.nodes[1], 2, block2)
        self.blockchain.update([block3, block4, block5])
        self.attestation.update({2: {
            self.nodes[i]: block4 if i in [0, 1, 2, ] else block5 if i in [3, 4, 5, 6] else block3 for i in range(self.no_of_nodes)}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block3})

    def test_threelevel_heavyweight(self):
        self.blockchain = set()
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 1, self.genesis_block)
        self.blockchain.update([block1])
        self.blockchain.update([block2])
        self.attestation = {1: {self.nodes[i]: block1 if i in range(
            int(0.5 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}
        # Retest the level one here
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block})
        self.nodes[4].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        # Logic to see if the consensus chain shifts justified block in the previous block and verify the subtree is heavier
        block3 = Block('2A', self.nodes[0], 2, block1)
        block4 = Block('2B', self.nodes[0], 2, block1)
        block5 = Block('2C', self.nodes[1], 2, block2)
        self.blockchain.update([block3, block4, block5])
        self.attestation.update({2: {
            self.nodes[i]: block4 if i in [0, 1] else block5 if i in [3, 4, 5, 6] else block3 for i in range(self.no_of_nodes)}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block3})

        # Logic to see if the consensus chain works for three levels and fights against longest chain
        block6 = Block('3A', self.nodes[0], 3, block3)
        block7 = Block('3B', self.nodes[0], 3, block3)
        block8 = Block('3C', self.nodes[1], 3, block5)
        block9 = Block('4A', self.nodes[1], 4, block8)
        self.blockchain.update([block6, block7, block8, block9])
        attestation2 = self.attestation.copy()
        attestation2.update({3: {
            self.nodes[i]: block6 if i in [0, 1, 2] else block7 if i in [3, 4, 5, 6] else block8 for i in range(self.no_of_nodes)}, 4: {self.nodes[6]: block9}})

        self.nodes[4].gasper.lmd_ghost(self.blockchain, attestation2)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block3, 3: block7, })

        self.attestation.update({3: {
            self.nodes[i]: block6 if i in [0] else block7 if i in [1] else block8 for i in range(self.no_of_nodes)}, 4: {self.nodes[6]: block9}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block2, 2: block5, 3: block8, 4: block9})

    def test_from_annotated_spec(self):
        self.blockchain = set()
        self.attestation = {}
        block1 = Block('1', self.nodes[0], 1, self.genesis_block)
        block2 = Block('2', self.nodes[1], 2, block1)
        block3 = Block('3', self.nodes[2], 3, block2)
        block4 = Block('4A', self.nodes[3], 4, block3)
        block5 = Block('5B', self.nodes[0], 5, block3)
        block6 = Block('6C', self.nodes[1], 6, block5)
        block7 = Block('7D', self.nodes[2], 7, block5)
        block8 = Block('8A', self.nodes[3], 8, block4)
        block9 = Block('9B', self.nodes[3], 9, block5)
        block10 = Block('10A', self.nodes[3], 10, block8)

        self.blockchain.update(
            [block1, block2, block3, block4, block5, block6, block7, block8, block9, block10])

        self.attestation.update({6: {self.nodes[4]: block6}, 7: {self.nodes[5]: block7}, 8: {
                                self.nodes[6]: block8}, 9: {self.nodes[7]: block9}, 10: {self.nodes[8]: block10}})

        self.nodes[9].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[9].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block2, 3: block3, 5: block5, 6: block6})

    def tearDown(self):
        del self.nodes, self.genesis_block
