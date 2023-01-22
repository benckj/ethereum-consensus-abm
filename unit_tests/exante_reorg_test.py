import unittest
import sys
sys.path.append('../')

from agent.node import *
from agent.base_utils import *

class ExAnteReOrg_TestCase(unittest.TestCase):
    def setUp(self):
        self.no_of_nodes = 10
        self.genesis_block = Block('0', "genesis", 0)
        self.nodes = [Node(self.genesis_block,i)
                      for i in range(self.no_of_nodes)]

    def produce_emptyslot(self):
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 1, self.genesis_block)

        self.blockchain = set()
        self.blockchain.update([block1])
        self.attestation = {1: {self.nodes[i]: block1 if i in range(
            int(0.5 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}
        # Retest the level one here
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block})
        self.nodes[4].gasper.lmd_ghost( self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        # Logic to see produce an empty slot
        self.blockchain.update([block2])
        self.attestation.update(
            {2: {self.nodes[i]: block1 for i in range(int(0.6 * self.no_of_nodes))}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain, self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1,})

    def produce_emptySlot_and_blockinlater(self):
        self.blockchain = set()
        block1 = Block('n', self.nodes[0], 1, self.genesis_block)
        self.attestation = {
            1: {self.nodes[i]: block1 for i in range(self.no_of_nodes)}}

        # Retest the level one here
        self.blockchain.update([block1])
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block})
        self.nodes[4].gasper.lmd_ghost(self.blockchain,self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        # Logic to see produce an empty slot
        self.attestation.update(
            {2: {self.nodes[i]: block1 for i in range(int(0.6 * self.no_of_nodes))}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain,self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, })

        block2 = Block('n+2', self.nodes[0], 3, block1)
        self.blockchain.update([block2])
        self.attestation.update(
            {3: {self.nodes[i]: block2 for i in range(int(0.6 * self.no_of_nodes))}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain,self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 3: block2})

    def reorg(self):
        self.blockchain = set()        
        block1 = Block('n', self.nodes[0], 1, self.genesis_block)
        self.attestation = {
            1: {self.nodes[i]: block1 for i in range(self.no_of_nodes)}}

        # Retest the level one here
        self.blockchain.update([block1])
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block})
        self.nodes[4].gasper.lmd_ghost(self.blockchain,self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        # Logic to see produce an empty slot
        self.attestation.update(
            {2: {self.nodes[i]: block1 for i in range(int(0.4 * self.no_of_nodes))}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain,self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        block2 = Block('n+2', self.nodes[0], 3, block1)
        self.blockchain.update([block2])
        self.attestation.update(
            {3: {self.nodes[i]: block2 for i in range(int(0.6 * self.no_of_nodes))}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain,self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 3: block2})

        block3 = Block('n+1', self.nodes[0], 2, block1)
        block4 = Block('n+3', self.nodes[0], 4, block3)
        self.blockchain.update([block3, block4])
        self.attestation[2].update({self.nodes[i]: block3 for i in [
                                6, 7, 8, 9]})
        self.attestation[3].update({self.nodes[i]: block3 for i in [6, 7, 8, 9]})
        self.attestation.update({4: {self.nodes[i]: block4 for i in [4, 5, 6, 7, 8, 9]}})
        self.nodes[4].gasper.lmd_ghost(self.blockchain,self.attestation)
        self.assertEqual(self.nodes[4].gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block3, 4: block4})

    def tearDown(self):
        del self.nodes, self.genesis_block
