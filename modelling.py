import networkx as nx

from utils.attestation import *
from utils.block import *
from utils.network import *
from node import *
from gillespie import *

class Model:
    '''
    This is used to build the network needed and parameterize the Gillespie Model
    Initiates the model and builds it around the parameters given model.gillespie.run to run the simulation.
    All objects are contained in the class.
    '''
    def __init__(self,
                 graph=None,
                 tau_block=None,
                 tau_attest=None,
                 ):

        self.tau_block = tau_block
        self.tau_attest = tau_attest

        self.blockchain = [Block('genesis')]
        self.network = Network(graph)
        self.no_of_nodes = len(self.network)
        self.nodes = [Node(blockchain=self.blockchain.copy()
                           )
                      for i in range(self.no_of_nodes)]

        self.network.set_neighborhood(self.nodes)

        self.gillespie = Gillespie(
            nodes=self.nodes,
            validators=self.nodes,
            blockchain=self.blockchain,
            network=self.network,
            tau_block=self.tau_block,
            tau_attest=self.tau_attest,
        )

    def results(self):
        d = {"test": 1}
        return d


if __name__ == "__main__":
    # As mentioned in the Stochatic Modelling paper, 
    # the number of neighbors fixed but have to experiment multiple topologies
    net_p2p = nx.random_degree_sequence_graph(
        [6 for i in range(40)])
    lcc_set = max(nx.connected_components(net_p2p), key=len)
    net_p2p = net_p2p.subgraph(lcc_set).copy()
    net_p2p = nx.convert_node_labels_to_integers(
        net_p2p, first_label=0)
    model = Model(
        graph=net_p2p,
        tau_block=1,
        tau_attest=1
    )
    model.gillespie.run(2e2)
    model.results()
