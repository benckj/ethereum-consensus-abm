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

    print(sample.calculate_average_shortest_path(net))
    # testing
    assert(sample.calculate_average_shortest_path(net) == 2.0)
