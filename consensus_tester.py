from base_utils import *
from consensus_utils import *
import numpy as np


def lmd_ghost_tester():

    # creating a lmd ghost tester
    zeroBlock = Block('0', emitter="genesis", emitter_slot=-1)
    B1Block = Block('1B', emitter="tester", emitter_slot=0, parent=zeroBlock)
    B2Block = Block('2B', emitter="tester", emitter_slot=1, parent=B1Block)
    C2Block = Block('2C', emitter="tester", emitter_slot=1, parent=B1Block)
    D2Block = Block('2D', emitter="tester", emitter_slot=1, parent=B1Block)
    F3Block = Block('3F', emitter="tester", emitter_slot=2, parent=D2Block)
    E3Block = Block('3E', emitter="tester", emitter_slot=2, parent=C2Block)
    D3Block = Block('3D', emitter="tester", emitter_slot=2, parent=C2Block)
    C3Block = Block('3C', emitter="tester", emitter_slot=2, parent=C2Block)
    B3Block = Block('3B', emitter="tester", emitter_slot=2, parent=B2Block)
    B4Block = Block('4B', emitter="tester", emitter_slot=3, parent=D3Block)
    C4Block = Block('4B', emitter="tester", emitter_slot=3, parent=F3Block)
    B5Block = Block('5B', emitter="tester", emitter_slot=4, parent=C4Block)

    blockchain = {zeroBlock, B1Block, B2Block, B3Block, B4Block, B5Block,
                  C2Block, C3Block, C4Block, D2Block, D3Block, E3Block, F3Block}
    testnode = Node([zeroBlock, B1Block, B2Block, B3Block, B4Block, B5Block, C2Block,
                    C3Block, C4Block, D2Block, D3Block, E3Block, F3Block], rng=np.random.default_rng())
    testnode1 = Node([zeroBlock, B1Block, B2Block, B3Block, B4Block, B5Block, C2Block,
                     C3Block, C4Block, D2Block, D3Block, E3Block, F3Block], rng=np.random.default_rng())
    testnode2 = Node([zeroBlock, B1Block, B2Block, B3Block, B4Block, B5Block, C2Block,
                     C3Block, C4Block, D2Block, D3Block, E3Block, F3Block], rng=np.random.default_rng())
    testnode3 = Node([zeroBlock, B1Block, B2Block, B3Block, B4Block, B5Block, C2Block,
                     C3Block, C4Block, D2Block, D3Block, E3Block, F3Block], rng=np.random.default_rng())
    testnode4 = Node([zeroBlock, B1Block, B2Block, B3Block, B4Block, B5Block, C2Block,
                     C3Block, C4Block, D2Block, D3Block, E3Block, F3Block], rng=np.random.default_rng())

    attestations = {-1: {testnode: zeroBlock, testnode1: zeroBlock, testnode2: zeroBlock, testnode3: zeroBlock, testnode4: zeroBlock, },
                     0: {testnode: B1Block, testnode1: B1Block, testnode2: B1Block, testnode3: B1Block, testnode4: B1Block, },
                     1: {testnode: D2Block, testnode1: C2Block, testnode2: C2Block, testnode3: C2Block, testnode4: B2Block, },
                     2: {testnode: F3Block, testnode1: E3Block, testnode2: D3Block, testnode3: C3Block, testnode4: B3Block},
                     3: {testnode: C4Block, testnode2: B4Block},
                     4: {testnode: B5Block, }, }
    gasper = Gasper(zeroBlock)
    consensus_block = gasper.lmd_ghost(
        blockchain=blockchain, attestations=attestations)


if __name__ == "__main__":
    lmd_ghost_tester()
