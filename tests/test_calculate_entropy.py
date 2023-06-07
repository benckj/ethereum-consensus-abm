"""Module providing Function to change path"""
import sys
import numpy as np
sys.path.append("../")
import eth_base as sample


##################
# actual testing

def test_0():
    """Simple test
    """
    #################
    # mock blockchain
    mock_blockchain = []

    genesis = sample.Block()
    mock_blockchain.append(genesis)

    block_1 = sample.Block(
        parent=genesis,
        slot_no=1
        )
    mock_blockchain.append(block_1)

    block_2 = sample.Block(
        parent=block_1,
        slot_no=2
        )
    mock_blockchain.append(block_2)

    block_3 = sample.Block(
        parent=block_2,
        slot_no=3
        )
    mock_blockchain.append(block_3)

    block_4 = sample.Block(
        parent=block_3,
        slot_no=4
        )
    mock_blockchain.append(block_4)

    # print(mock_blockchain)

    ###################
    # mock attestations

    # testing
    assert(sample.calculate_entropy(mock_blockchain) == np.log(5)-(4/5)*np.log(4))