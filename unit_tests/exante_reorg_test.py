import unittest
import sys
sys.path.append('../')

from agent.node import *
from agent.base_utils import *

class ExAnteReOrg_TestCase(unittest.TestCase):
    def setUp(self):
        self.no_of_nodes = 12
        self.genesis_block = Block('0', "genesis", 0)
        self.nodes = [Node(self.genesis_block,i)
                      for i in range(self.no_of_nodes)]
        self.analyze_node = Node(self.genesis_block,self.no_of_nodes)

    def produce_emptyslot(self):
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 1, self.genesis_block)

        chain_state = ChainState(14, 1, 2, 0, 0, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)
        attestations = {1: {self.nodes[i]: block1 if i in range(
            int(0.5 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,Attestation(node,block,slot))

        # Retest the level one here
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block})
        self.analyze_node.gasper.lmd_ghost(chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        
        chain_state.update_slot(3)
        # Logic to see produce an empty slot
        self.analyze_node.state.add_block(chain_state, block2)
        attestations = {2: {self.nodes[i]: block1 for i in range(int(0.6 * self.no_of_nodes))}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,Attestation(node,block,slot))

        self.analyze_node.gasper.lmd_ghost(chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

    def produce_emptySlot_and_blockinlater(self):
        block1 = Block('n', self.nodes[0], 1, self.genesis_block)

        # Retest the level one here
        chain_state = ChainState(14, 1, 2, 0, 0, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)

        attestations = {
            1: {self.nodes[i]: block1 for i in range(self.no_of_nodes)}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state, Attestation(node,block,slot))

        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block})
        self.analyze_node.gasper.lmd_ghost(chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})
        
        # Logic to see produce an empty slot
        attestations = {2: {self.nodes[i]: block1 for i in range(int(0.6 * self.no_of_nodes))}}
        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state, Attestation(node,block,slot))

   
        chain_state.update_slot(3)  
        self.analyze_node.gasper.lmd_ghost(chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, })

        
        chain_state.update_slot(4)

        block2 = Block('n+2', self.nodes[0], 3, block1)
        self.analyze_node.state.add_block(chain_state, block2)
        attestations = {3: {self.nodes[i]: block2 for i in range(int(0.6 * self.no_of_nodes))}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state, Attestation(node,block,slot))

        self.analyze_node.gasper.lmd_ghost(chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 3: block2})

    def reorg(self):
       # Slot 1: Initialized
        chain_state = ChainState(3, 1, 1, 3, 0, self.genesis_block)
        block1 = Block('n', self.nodes[0], 1, self.genesis_block)

        # Slot 1: Block Listened
        self.analyze_node.state.add_block(chain_state, block1)

        # Slot 1: Attestation Listened
        attestations = {
            1: {self.nodes[i]: block1 for i in [0, 1, 2]}}

        chain_state.update_time(14)
        chain_state.update_slot(2)

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block})
        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        chain_state.set_malicious_slot()
        # Logic to see produce an empty slot in the malicious_slot
        block2 = Block('n+1', self.nodes[0], 2, block1, True)
        attestations = {2: {self.nodes[i]: block1 for i in [3, 4, ]}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, })

        chain_state.update_time(22)
        self.analyze_node.state.add_block(chain_state, block2)

        chain_state.update_time(26)
        chain_state.update_slot(3)

        attestations = {2: {self.nodes[i]: block2 for i in [5,6,7]}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))
                
        block3 = Block('n+2', self.nodes[0], 3, block1)
        self.analyze_node.state.add_block(chain_state, block3)

        # chain_state.update_time(38)
        # chain_state.update_slot(4)
        # attestations = {3: {self.nodes[i]: block3 for i in [3]}}

        # for slot, node_attestaions in attestations.items():
        #     for node, block in node_attestaions.items():
        #         self.analyze_node.state.add_attestation(chain_state,
        #                                                 Attestation(node, block, slot))

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block2})

        self.assertEqual(len([1 for slot in chain_state.reorgs if (
            slot+1) not in self.analyze_node.gasper.consensus_chain.keys() and slot in self.analyze_node.gasper.consensus_chain.keys()]), 1)


    def tearDown(self):
        del self.nodes, self.genesis_block
