"""Module providing Function to change path"""
import sys
import numpy as np
sys.path.append("../")
import eth_base as sample
import networkx as nx


##################
# actual testing

def test_0():
    """Simple test
    """
    #################
    # mock blockchain
    net_p2p = nx.grid_graph(dim=(3, 3))
    net = sample.Network(net_p2p)

    # print(mock_blockchain)

    ###################
    # mock attestations

    # testing
    assert(sample.calculate_diameter(net) == 4)
