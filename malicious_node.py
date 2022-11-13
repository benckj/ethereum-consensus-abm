from base_utils import *
from threading import Timer


class MaliciousNode(Node):
    def __init__(self, block, rng):
        Node.__init__(self,block, rng)

    def attack():
        pass

    def propose_block(self, value):
        print('Node {} is Malicious is trying to propose block with value {}'.format(
            self.id, value))

        schedule = Timer(15, Node.propose_block, args=(self,value))

        schedule.start()

    def gossip(self, listening_node):
        return Node.gossip(self,listening_node)
