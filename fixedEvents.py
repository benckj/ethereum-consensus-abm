from threading import Timer


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
        self.comittees = []
        self.proposers = []

        self.slots_per_epoch = 32
        self.v_n = len(self.validators)
        self.committee_size = int(self.v_n/self.slots_per_epoch)
        self.leftover = self.v_n - (self.committee_size * self.slots_per_epoch)

    def event(self):
        self.rng.shuffle(self.validators)
        self.comittees = [[self.validators[v+c*self.committee_size] for v in range(self.committee_size)]
                          for c in range(self.slots_per_epoch)]

        self.proposers = [self.rng.choice(self.validators)
                          for c in range(self.slots_per_epoch)]

        j = list(range(self.slots_per_epoch))
        self.rng.shuffle(j)
        for i in range(1, self.leftover+1):
            self.comittees[j[i-1]].append(self.validators[-i])

        print(self.comittees, self.proposers)
        print('New Epoch: Committees formed')


class SlotBoundary(FixedTimeEvent):
    def __init__(self, interval, validators, epoch_boundary, rng=None):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.epoch_boundary = epoch_boundary

    def event(self):
        proposer = self.epoch_boundary.proposers[self.counter %
                                                 self.epoch_boundary.slots_per_epoch]
        proposer.propose_block('E{}_S{}'.format(
            self.epoch_boundary.counter, self.counter))
        print('Block proposed {}'.format(proposer.local_blockchain))

        # schedule = Timer(4, self.activate_attesting)
        # schedule.start()
        self.activate_attesting()

    def activate_attesting(self):
        print('activating attesting for slot:{}'.format(self.counter))
        for v in self.epoch_boundary.comittees[self.counter % self.epoch_boundary.slots_per_epoch]:
            v.is_attesting = True


class AttestationBoundary(FixedTimeEvent):
    def __init__(self, interval, offset, slot_boundary, epoch_boundary, rng=None):
        super().__init__(interval, offset, rng=rng)
        self.slot_boundary = slot_boundary
        self.epoch_boundary = epoch_boundary

    def event(self):
        print(' attesting in the fixed event')
        for v in [v for v in self.epoch_boundary.comittees[self.slot_boundary.counter % self.epoch_boundary.slots_per_epoch] if v.is_attesting == True]:
            v.attestations_ledger.attest()
