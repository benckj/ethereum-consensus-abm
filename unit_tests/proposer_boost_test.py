
from agent.base_utils import *
from agent.node import *
import unittest
import sys
sys.path.append('../')


class PB_Test(unittest.TestCase):
    def setUp(self):
        self.no_of_nodes = 12
        self.genesis_block = Block('0', "genesis", 0)
        self.nodes = [Node(self.genesis_block, i)
                      for i in range(self.no_of_nodes)]
        self.analyze_node = Node(self.genesis_block, self.no_of_nodes)

    def base_test_wo_pb(self):
        """ 
        This tests provides a base for the next test to compare the working model of 
        proposer vote boost in lmdghost as the outcomes are different with minor change in the 
        proposer vote boost passed in `ChainState` as 0
        """

        chain_state = ChainState(3, 1, 1, 10, 0, self.genesis_block)
        chain_state.update_time(6)
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)

        chain_state.update_slot(2)
        chain_state.update_time(14)
        block2 = Block('1B', self.nodes[1], 2, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block2)

        attestations = {1: {self.nodes[i]: block1 for i in range(self.no_of_nodes) if i in range(
            int(0.5 * self.no_of_nodes))}, 2: {self.nodes[i]: block2 for i in range(self.no_of_nodes) if i not in range(
                int(0.5 * self.no_of_nodes))}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        chain_state.update_slot(3)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block})
        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

    def base_test(self):
        """ 
        This tests the above base scenario just by updating the `ChainState` with proposer vote boost value as 0.4

        """

        chain_state = ChainState(3, 1, 1, 10, 0.4, self.genesis_block)
        chain_state.update_time(9)
        block1 = Block('n+1', self.nodes[0], 1, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)

        # Check the block is not on time, so there is no proposer boost here
        self.assertEqual(self.analyze_node.state.proposer_booster, None)

        attestations = {
            1: {self.nodes[i]: block1 if i == 4 else self.genesis_block for i in range(5)}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        chain_state.update_slot(2)
        chain_state.update_time(14)
        block2 = Block('n+2', self.nodes[1], 2, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block2)

        # Asserts the proposer booster added to the node
        self.assertEqual(self.analyze_node.state.proposer_booster, block2)

        self.assertEqual(self.analyze_node.gasper.get_cummulative_weight_subTree(
            block2, self.analyze_node.state, chain_state), 4)

        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block})
        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 2: block2})
        

    def reorg_protection(self):
       # Slot 1: Initialized
        chain_state = ChainState(3, 1, 1, 3, 0.4, self.genesis_block)
        block1 = Block('n', self.nodes[0], 1, self.genesis_block)

        # Slot 1: Block Listened on time
        self.analyze_node.state.add_block(chain_state, block1)

        # Slot 1: Attestation Listened on time
        attestations = {
            1: {self.nodes[i]: block1 for i in [0, 1, 2]}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        chain_state.update_time(14)
        chain_state.update_slot(2)

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

        # Assuming the attestation of the analyze node at this moment is for the empty slot to previous head
        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, })

        chain_state.update_time(22)
        self.analyze_node.state.add_block(chain_state, block2)

        chain_state.update_time(26)
        chain_state.update_slot(3)

        attestations = {2: {self.nodes[i]: block2 for i in [5]}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        block3 = Block('n+2', self.nodes[0], 3, block1)
        self.analyze_node.state.add_block(chain_state, block3)

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 3: block3})

        self.assertEqual(len([1 for slot in chain_state.reorgs if (
            slot+1) not in self.analyze_node.gasper.consensus_chain.keys() and slot in self.analyze_node.gasper.consensus_chain.keys()]), 0)

    def tearDown(self):
        del self.nodes, self.genesis_block
