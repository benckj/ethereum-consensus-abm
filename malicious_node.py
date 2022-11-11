from base_utils import *


class MaliciousNode(Node):
    def __init__(self, block, rng):
        super().__init__(block, rng)

    def attack():
        pass

    def propose_block(self, value):
        print('Node {} is Malicious is trying to propose block with value {}'.format(
            self.id, value))
        return super().propose_block(value)

    def gossip(self, listening_node):
        return super().gossip(listening_node)
