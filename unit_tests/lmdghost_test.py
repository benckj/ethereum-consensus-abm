
from agent.base_utils import *
from agent.node import *
import unittest
import sys
sys.path.append('../')


class GHOST_TestCase(unittest.TestCase):
    def setUp(self):
        self.no_of_nodes = 10
        self.genesis_block = Block('0', "genesis", 0)
        self.nodes = [Node(self.genesis_block, i)
                      for i in range(self.no_of_nodes)]
        self.analyze_node = Node(self.genesis_block, self.no_of_nodes)

    def test_onelevel_heavyweight(self):
        # Just to check Heavy weight
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 2, self.genesis_block)

        chain_state = ChainState(14, 1, 3, 0, 0, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)
        self.analyze_node.state.add_block(chain_state, block2)

        attestations = {1: {self.nodes[i]: block1 for i in range(self.no_of_nodes) if i in range(
            int(0.6 * self.no_of_nodes))}, 2: {self.nodes[i]: block2 for i in range(self.no_of_nodes) if i not in range(
                int(0.6 * self.no_of_nodes))}}

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

    def test_onelevel_tieweight(self):
        # Just to check Tied weight
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 2, self.genesis_block)

        chain_state = ChainState(14, 1, 3, 0, 0, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)
        self.analyze_node.state.add_block(chain_state, block2)

        attestations = {1: {self.nodes[i]: block1 for i in range(self.no_of_nodes) if i in range(
            int(0.5 * self.no_of_nodes))}, 2: {self.nodes[i]: block2 for i in range(self.no_of_nodes) if i not in range(
                int(0.5 * self.no_of_nodes))}}

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

    def test_twolevel_heavyweight(self):
        # Just to check tied weight in level 1
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 1, self.genesis_block)

        chain_state = ChainState(14, 1, 1, 0, 0, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)
        self.analyze_node.state.add_block(chain_state, block2)

        attestations = {1: {self.nodes[i]: block1 if i in range(
            int(0.5 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        chain_state.update_slot(2)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block})
        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1})

        # Logic to see if the consensus chain shifts after the slot 1
        block3 = Block('2A', self.nodes[0], 2, block1)
        block4 = Block('2B', self.nodes[0], 2, block1)
        block5 = Block('2C', self.nodes[1], 2, block2)

        self.analyze_node.state.add_block(chain_state, block3)
        self.analyze_node.state.add_block(chain_state, block4)
        self.analyze_node.state.add_block(chain_state, block5)

        attestations = {2: {
            self.nodes[i]: block4 if i in [0, 1, 2] else block3 if i in [3, 4, 5, 6] else block5 for i in range(self.no_of_nodes)}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        chain_state.update_slot(3)

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block3})

    def test_threelevel_heavyweight(self):
        # Just to check Heavy weight
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 1, self.genesis_block)

        chain_state = ChainState(14, 1, 2, 0, 0, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)
        self.analyze_node.state.add_block(chain_state, block2)

        attestations = {1: {self.nodes[i]: block1 if i in range(
            int(0.5 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}

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

        # Logic to see if the consensus chain shifts the slot 1 also
        block3 = Block('2A', self.nodes[0], 2, block1)
        block4 = Block('2B', self.nodes[0], 2, block1)
        block5 = Block('2C', self.nodes[1], 2, block2)

        chain_state.update_slot(3)

        self.analyze_node.state.add_block(chain_state, block3)
        self.analyze_node.state.add_block(chain_state, block4)
        self.analyze_node.state.add_block(chain_state, block5)

        attestations = {2: {
            self.nodes[i]: block4 if i in [0, 1, 2, ] else block5 if i in [3, 4, 5, 6] else block3 for i in range(self.no_of_nodes)}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block3})

        # Logic to see if the consensus chain works for three levels and fights against longest chain
        block6 = Block('3A', self.nodes[0], 3, block3)
        block7 = Block('3B', self.nodes[0], 3, block3)
        block8 = Block('3C', self.nodes[1], 3, block5)

        chain_state.update_slot(4)
        self.analyze_node.state.add_block(chain_state, block6)
        self.analyze_node.state.add_block(chain_state, block7)
        self.analyze_node.state.add_block(chain_state, block8)
        chain_state.update_slot(5)
        block9 = Block('4A', self.nodes[1], 4, block8)
        self.analyze_node.state.add_block(chain_state, block9)

        attestations = {3: {
            self.nodes[i]: block6 if i in [0, 1, 2] else block7 if i in [3, 4, 5, 6] else block8 for i in range(self.no_of_nodes)}, 4: {self.nodes[6]: block9}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block3, 3: block6})

    def test_threelevel_heavyweight2(self):
        # Just to check Heavy weight
        block1 = Block('1A', self.nodes[0], 1, self.genesis_block)
        block2 = Block('1B', self.nodes[1], 1, self.genesis_block)

        chain_state = ChainState(14, 1, 2, 0, 0, self.genesis_block)
        self.analyze_node.state.add_block(chain_state, block1)
        self.analyze_node.state.add_block(chain_state, block2)

        attestations = {1: {self.nodes[i]: block1 if i in range(
            int(0.5 * self.no_of_nodes)) else block2 for i in range(self.no_of_nodes)}}

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

        # Logic to see if the consensus chain shifts the slot 1 also
        block3 = Block('2A', self.nodes[0], 2, block1)
        block4 = Block('2B', self.nodes[0], 2, block1)
        block5 = Block('2C', self.nodes[1], 2, block2)

        chain_state.update_slot(3)

        self.analyze_node.state.add_block(chain_state, block3)
        self.analyze_node.state.add_block(chain_state, block4)
        self.analyze_node.state.add_block(chain_state, block5)

        attestations = {2: {
            self.nodes[i]: block4 if i in [0, 1, 2, ] else block5 if i in [3, 4, 5, 6] else block3 for i in range(self.no_of_nodes)}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block3})

        # Logic to see if the consensus chain works for three levels and fights against longest chain
        block6 = Block('3A', self.nodes[0], 3, block3)
        block7 = Block('3B', self.nodes[0], 3, block3)
        block8 = Block('3C', self.nodes[1], 3, block5)

        chain_state.update_slot(4)
        self.analyze_node.state.add_block(chain_state, block6)
        self.analyze_node.state.add_block(chain_state, block7)
        self.analyze_node.state.add_block(chain_state, block8)
        chain_state.update_slot(5)
        block9 = Block('4A', self.nodes[1], 4, block8)
        self.analyze_node.state.add_block(chain_state, block9)

        attestations = {3: {
            self.nodes[i]: block6 if i in [0] else block7 if i in [1] else block8 for i in range(self.no_of_nodes)}, 4: {self.nodes[6]: block9}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block2, 2: block5, 3: block8, 4: block9})

    def test_from_annotated_spec(self):
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
        chain_state = ChainState(14, 1, 2, 0, 0, self.genesis_block)

        chain_state.update_slot(11)
        self.analyze_node.state.add_block(chain_state, block1)
        self.analyze_node.state.add_block(chain_state, block2)
        self.analyze_node.state.add_block(chain_state, block3)
        self.analyze_node.state.add_block(chain_state, block4)
        self.analyze_node.state.add_block(chain_state, block5)
        self.analyze_node.state.add_block(chain_state, block6)
        self.analyze_node.state.add_block(chain_state, block7)
        self.analyze_node.state.add_block(chain_state, block8)
        self.analyze_node.state.add_block(chain_state, block9)
        self.analyze_node.state.add_block(chain_state, block10)

        attestations = {6: {self.nodes[4]: block6}, 7: {self.nodes[5]: block7}, 8: {
            self.nodes[6]: block8}, 9: {self.nodes[7]: block9}, 10: {self.nodes[8]: block10}}

        for slot, node_attestaions in attestations.items():
            for node, block in node_attestaions.items():
                self.analyze_node.state.add_attestation(chain_state,
                                                        Attestation(node, block, slot))

        self.analyze_node.gasper.lmd_ghost(
            chain_state, self.analyze_node.state,)
        self.assertEqual(self.analyze_node.gasper.consensus_chain, {
                         0: self.genesis_block, 1: block1, 2: block2, 3: block3, 5: block5, 6: block6})

    def tearDown(self):
        del self.nodes, self.genesis_block
