import numpy as np

from utils.process import *
from utils.events import *

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

    def __init__(self, nodes, blockchain, validators, network, tau_block=1, tau_attest=0.1):

        self.time = 0
        self.blockchain = blockchain
        self.nodes = nodes
        self.validators = validators

        self.block_gossip_process = BlockGossipProcess(
            tau=tau_block, nodes=nodes)
        self.attestation_gossip_process = AttestationGossipProcess(
            tau=tau_attest, nodes=nodes)

        self.epoch_boundary = EpochBoundary(32*12, self.validators)


        self.processes = [self.block_gossip_process,
                          self.attestation_gossip_process]
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)

        self.network = network

    def update_lambdas(self):
        '''Lambdas are recauculated after each time increment
        '''
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)

    def calculate_time_increment(self):
        '''Function to generate the random time increment from an exponential random distribution.
        '''
        increment = (-np.log(np.random.random()) /
                     self.lambda_sum).astype('float64')
        return increment

    def trigger_event(self):
        # [Teja] Should select a node on random and do an event based on the role in that particular slot. 
        '''
            Selects the next process according to its weight and it executes the related event.
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
            increment = self.calculate_time_increment()
            print('{:.2f}---->{:.2f}'.format(self.time, self.time + increment))

            # loop over fixed and trigger if time passes fixed event time
            self.epoch_boundary.event()

            # select poisson process and trigger selected process
            self.trigger_event()
            self.time += increment

            # compute and execute number of proposal events vefore next random event.
            time_since_propose_event = (
                (self.time + increment) - self.last_propose)

            # # execute all propose events before next random event
            # for i in range(int(time_since_propose_event//self.propose_time)):
            #     # tell the nodes the new slot started and they have to attest
            #     if i == 0:
            #         for n in self.nodes:
            #             n.is_attesting = True
            #     proposer = rnd.choice(self.nodes)
            #     # TODO: mine->propose
            #     proposer.mine_block()
            #     self.last_propose += self.propose_time

            # # compute and execute number of proposal events before next random event.
            # time_since_attest_event = (
            #     (self.time + self.increment) - self.last_attest)
            # for i in range(int(time_since_attest_event//self.attest_time)):
            #     self.attestation_window = not self.attestation_window
            #     for n in self.nodes:
            #         if n.is_attesting:
            #             n.attestations.attest()

            #         n.is_attesting = self.attestation_window
            #         self.last_attest += self.attest_time

            # # trigger the random event
            # self.trigger_event()
            # update time
            self.time += increment
            print(self.time)

        return
