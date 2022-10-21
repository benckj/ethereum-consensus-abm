import random as rnd

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
    
    def __init__(self, tau, nodes):
        super().__init__(tau)
        self.nodes = nodes
        
    def event(self):
        #TODO: from nodes sampling to edges sampling
        gossiping_node = rnd.choice(self.nodes)
        listening_node = rnd.choice(list(gossiping_node.neighbors))
        gossiping_node.gossip(listening_node)
        return
    
class AttestationGossipProcess(Process):
    """The process to manage attestation gossiping
    INPUT:
    - nodes,    list of Nodes obejct
    - tau,      float, process latency
    """
    def __init__(self, tau, nodes):
        super().__init__(tau)
        self.nodes = nodes
        
    def event(self):
        gossiping_node = rnd.choice(self.nodes)
        # [Teja] handle attestation gossip here
        # gossiping_node.attestations.send_attestation_message()
        print(gossiping_node, 'gossips an attestation here')
        return
