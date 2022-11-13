import numpy as np

class Process:
    '''Parent class for processes. 
    INPUT:
    - tau,  float, the latency
    '''

    def __init__(self, tau):
        self.__tau = tau
        self.__lam = 1/tau

    @property
    def tau(self):
        return self.__tau

    @tau.setter
    def tau(self, value):
        self.__tau = value
        self.__lam = 1/self.__tau

    @property
    def lam(self):
        return self.__lam

    def event(self):
        pass


class BlockGossipProcess(Process):
    """The process to manage block gossiping
    INPUT:
    - nodes,    list of Nodes obejct
    - tau,      float, process latency
    """

    def __init__(self, tau, edges, rng=np.random.default_rng()):
        self.edges = edges
        self.num_edges = len(edges)

        super().__init__((tau/self.num_edges))
        self.rng = rng

    def event(self):
        gossiping_node, listening_node = self.rng.choice(self.edges)
        gossiping_node.gossip(listening_node)
        return


class AttestationGossipProcess(Process):
    """The process to manage attestation gossiping
    INPUT:
    - nodes,    list of Nodes obejct
    - tau,      float, process latency
    """

    def __init__(self, tau, nodes, rng=np.random.default_rng()):
        super().__init__(tau)
        self.rng = rng

        self.nodes = nodes

    # TODO: logic should count messaged that are in the queue and select only those
    def event(self):
        gossiping_node = self.rng.choice(self.nodes)
        gossiping_node.attestations_ledger.send_attestation_message()
        return

