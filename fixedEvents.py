from threading import Timer
from constants import *


class FixedTimeEvent():
    def __init__(self, interval, time=0, offset=0, rng=None):
        if not interval >= 0:
            raise ValueError("Interval must be positive")

        self.rng = rng

        self.offset = offset
        self.interval = interval

        self.last_event = None
        self.next_event = time + self.offset

        self.counter = 0

    def trigger(self, next_time):
        while next_time > self.next_event:
            print(next_time)
            self.event()
            self.counter += 1
            self.next_event += self.interval

            return True
        return False

    def event(self):
        pass


class EpochBoundary(FixedTimeEvent):
    def __init__(self, interval, validators, rng=None):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.committees = []
        self.proposers = []

        self.v_n = len(self.validators)
        self.committee_size = int(self.v_n/SLOTS_PER_EPOCH)
        self.leftover = self.v_n - (self.committee_size * SLOTS_PER_EPOCH)

    def event(self):
        self.rng.shuffle(self.validators)
        self.committees = [[self.validators[v+c*self.committee_size] for v in range(self.committee_size)]
                           for c in range(SLOTS_PER_EPOCH)]

        self.proposers = [self.rng.choice(self.validators)
                          for c in range(SLOTS_PER_EPOCH)]

        j = list(range(SLOTS_PER_EPOCH))
        self.rng.shuffle(j)
        for i in range(1, self.leftover+1):
            self.committees[j[i-1]].append(self.validators[-i])

        print(self.committees, self.proposers)
        print('New Epoch: Committees formed')


class SlotBoundary(FixedTimeEvent):
    def __init__(self, interval, validators, epoch_boundary, rng=None):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.epoch_boundary = epoch_boundary

    def event(self):
        proposer = self.epoch_boundary.proposers[self.counter %
                                                 SLOTS_PER_EPOCH]
        proposer.propose_block(self.counter, 'E{}_S{}'.format(
            self.epoch_boundary.counter, self.counter))

        print('Proposer Node {}: Consensus View {}'.format(
            self.epoch_boundary.proposers[self.counter %
                                          SLOTS_PER_EPOCH], self.epoch_boundary.proposers[self.counter %
                                                                                          SLOTS_PER_EPOCH].gasper.consensus_chain, ))



class AttestationBoundary(FixedTimeEvent):
    def __init__(self, interval, offset, slot_boundary, epoch_boundary, rng=None):
        super().__init__(interval, offset, rng=rng)
        self.slot_boundary = slot_boundary
        self.epoch_boundary = epoch_boundary

    def event(self):
        for v in [v for v in self.epoch_boundary.committees[self.slot_boundary.counter % SLOTS_PER_EPOCH]]:
            print('Proposer Node {}: Consensus View {}'.format(v, v.gasper.consensus_chain, ))
            print('Called node {} for attesting'.format(v))
            v.attest(self.slot_boundary.counter)
