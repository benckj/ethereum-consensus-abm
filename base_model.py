import numpy as np
import networkx as nx
from utils.attestation import *
from utils.block import *
from utils.network import *
from node import *
from utils.process import *


class Gillespie:
    '''
    The Gillespie class combines all the different classes to a single model.
    ONce it ran, you can parse the resulting objects which are: Gillespie.nodes, Gillespie.blockchain.
    INPUT:
    - nodes         - list of Node objects
    - blockchain    - list of Block objects, contains only genesis block upon initiating
    - network       - Network object (which stores the network on which miners interact) (Not necessarily needed)
    - tau_block     - float, block gossip latency
    - tau_attest    - float, attestation gossip latency
    '''

    def __init__(self, nodes, blockchain, network, tau_block=1, tau_attest=0.1):

        self.time = 0
        self.blockchain = blockchain
        self.nodes = nodes

        self.block_gossip_process = BlockGossipProcess(
            tau=tau_block, nodes=nodes)
        self.attestation_gossip_process = AttestationGossipProcess(
            tau=tau_attest, nodes=nodes)

        self.processes = [self.block_gossip_process,
                          self.attestation_gossip_process]
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)

        self.network = network
        # TODO: change to 12
        self.propose_time = 8
        self.attest_time = 4

    def update_lambdas(self):
        '''Lambdas are recauculated after each time increment
        '''
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)

    def increment_time(self):
        '''Function to generate the random time increment from an exponential random distribution.
        '''
        # TODO: add a rng in the init and pass it to all random functions.
        self.increment = (-np.log(np.random.random()) /
                          self.lambda_sum).astype('float64')
        #self.time += self.increment

    def trigger_event(self):
        '''Selects the next process according to its weight and it executes the related event.
        '''
        # TODO: add RNG
        select_process = rnd.choices(
            population=self.processes, weights=self.lambdas, k=1)[0]
        select_process.event()

    def proposal(self):
        # TODO: implement w/ commitee, slots, epochs
        pass

    def run(self, stopping_time):
        '''Runs the model for a given stopping time.
        '''
        self.last_propose = 0
        self.last_attest = 0
        self.attestation_window = True

        while self.time < stopping_time:

            # self.update_lambdas()
            # generate next random increment time and save it in self.increment
            # TODO: naming is misleading. Change increment)_time() name.
            self.increment_time()

            # compute and execute number of proposal events vefore next random event.
            time_since_propose_event = (
                (self.time + self.increment) - self.last_propose)
            # execute all propose events before next random event
            for i in range(int(time_since_propose_event//self.propose_time)):
                # tell the nodes the new slot started and they have to attest
                if i == 0:
                    for n in self.nodes:
                        n.is_attesting = True
                proposer = rnd.choice(self.nodes)
                # TODO: mine->propose
                proposer.mine_block()
                self.last_propose += self.propose_time

            # compute and execute number of proposal events before next random event.
            time_since_attest_event = (
                (self.time + self.increment) - self.last_attest)
            for i in range(int(time_since_attest_event//self.attest_time)):
                self.attestation_window = not self.attestation_window
                for n in self.nodes:
                    if n.is_attesting:
                        n.attestations.attest()

                    n.is_attesting = self.attestation_window
                    self.last_attest += self.attest_time

            # trigger the random event
            self.trigger_event()
            # update time
            self.time += self.increment
            print(self.time)

        return


class Model:
    '''Initiates the model and builds it around the parameters given
    model.gillespie.run to run the simulation.
    All objects are contained in the class.
    '''

    def __init__(self,
                 graph=None,
                 tau_block=None,
                 tau_attest=None,
                 ):

        self.tau_block = tau_block
        self.tau_attest = tau_attest

        self.blockchain = [Block()]
        self.network = Network(graph)
        self.N = len(self.network)
        self.nodes = [Node(blockchain=self.blockchain.copy()
                           )
                      for i in range(self.N)]

        self.network.set_neighborhood(self.nodes)

        self.gillespie = Gillespie(
            nodes=self.nodes,
            blockchain=self.blockchain,
            network=self.network,
            tau_block=self.tau_block,
            tau_attest=self.tau_attest,
        )

    def results(self):
        d = {"test": 1}
        return d


if __name__ == "__main__":
    net_p2p = nx.random_degree_sequence_graph(
        [3 for i in range(40)])
    lcc_set = max(nx.connected_components(net_p2p), key=len)
    net_p2p = net_p2p.subgraph(lcc_set).copy()
    net_p2p = nx.convert_node_labels_to_integers(
        net_p2p, first_label=0)
    model = Model(
        graph=net_p2p
    )
    model.gillespie.run(2e2)
    model.results()
