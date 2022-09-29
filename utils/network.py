import networkx as nx


class Network:
    """Object to manage the peer-to-peer network. It is a wrapper of networkx.Graph right now.
    INPUT
    - G,    a networkx.Graph object
    """

    def __init__(self, G):
        # G is a networkx Graph
        self.network = G
        # TODO: remove lcc..
        lcc_set = max(nx.connected_components(self.network), key=len)
        self.network = self.network.subgraph(lcc_set).copy()

    def __len__(self):
        return len(self.network)

    # TODO: nodes -> peers
    def set_neighborhood(self, nodes):
        # dict map nodes in the nx.graph to nodes on p2p network
        nodes_dict = dict(zip(self.network.nodes(), nodes))
        # save peer node object as an attribute of nx node
        nx.set_node_attributes(self.network, values=nodes_dict, name='node')

        for n in self.network.nodes():
            m = self.network.nodes[n]["node"]
            # save each neighbour in the nx.Graph inside the peer node object
            for k in self.network.neighbors(n):
                m.neighbors.add(self.network.nodes[k]["node"])
