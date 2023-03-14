import numpy as np


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

    def __init__(self, processes, rng=np.random.default_rng()):
        self.rng = rng
        self.processes = processes
        self.lambdas = [process.lam for process in self.processes]
        self.lambda_sum = np.sum(self.lambdas)
        self.lambda_weighted = [process.lam /
                                self.lambda_sum for process in self.processes]

    def calculate_time_increment(self):
        '''Function to generate the random time increment from an exponential random distribution.
        '''
        increment = (-np.log(np.random.random()) /
                     self.lambda_sum).astype('float64')
        return increment

    def select_event(self):
        '''Selects the next process according to its weight and it executes the related event.
        '''
        select_process = self.rng.choice(
            self.processes, p=self.lambda_weighted)
        return select_process
