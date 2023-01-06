from constants import *


class FixedTimeEvent():
    def __init__(self, interval, time=0, offset=0, rng=None):
        if not interval >= 0:
            raise ValueError("Interval must be positive")

        self.rng = rng
        self.interval = interval

        # Initialize offset of an event
        self.offset = offset

        # [To Be Deleted]
        # self.last_event = None
        self.next_event = time + self.offset
        self.counter = 0

    def trigger(self, next_time):
        while next_time > self.next_event:
            print(next_time)
            self.counter += 1
            self.event()
            self.next_event += self.interval

            return True
        return False

    def event(self):
        pass


class EpochEvent(FixedTimeEvent):
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

    def __repr__(self):
        return 'Chain Epoch {}'.format(self.counter)


class SlotEvent(FixedTimeEvent):
    def __init__(self, interval, validators, epoch_event, rng=None):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.epoch_event = epoch_event
        self.malicious_slot = False

    def event(self):
        print('proposing block for slot: {}'.format(self.counter))
        proposer = self.epoch_event.proposers[self.counter %
                                              SLOTS_PER_EPOCH]

        for validator_node in [v for v in self.epoch_event.committees[self.counter % SLOTS_PER_EPOCH - 1]]:
            validator_node.is_attesting = True

        proposer.propose_block(self.counter, 'E{}_S{}'.format(
            self.epoch_event.counter, self.counter))

        print('Proposer Node {}: Consensus View {} Consensus Attestations: {}'.format(
            proposer, proposer.gasper.consensus_chain, proposer.attestations))

        malicious_committee = False
        for validator_node in [v for v in self.epoch_event.committees[self.counter % SLOTS_PER_EPOCH]]:
            if validator_node.malicious:
                malicious_committee = True

        if proposer.malicious and malicious_committee:
            self.malicious_slot = True
            print(
                'Malicious Node, So disabling block gossiping to honest node'.format(proposer))
            for validator_node in proposer.malicious_neighbors:
                validator_node.obstruct_gossiping = True
            proposer.obstruct_gossiping = True

    def __repr__(self):
        return 'Chain Slot {}'.format(self.counter)


class AttestationEvent(FixedTimeEvent):
    def __init__(self, interval, offset, slot_event, epoch_event, rng=None):
        super().__init__(interval, offset, rng=rng)
        self.slot_event = slot_event
        self.epoch_event = epoch_event

    def event(self):
        print('providing attestation for slot: {}'.format(self.slot_event.counter))
        for validator_node in self.epoch_event.committees[self.slot_event.counter % SLOTS_PER_EPOCH]:
            if ~validator_node.is_attesting: 
                continue
            print('Called node {} for attesting'.format(validator_node))
            validator_node.attest(self.slot_event.counter)
            print('Attestor Node {}: Consensus View {} Consensus Attestations: {}'.format(
                validator_node, validator_node.gasper.consensus_chain, validator_node.attestations))

    def __repr__(self):
        return 'Chain Attestation {}'.format(self.counter)


class AdversaryEvent(FixedTimeEvent):
    def __init__(self, interval, offset, slot_event, epoch_event, rng=None):
        super().__init__(interval, offset, rng=rng)
        self.epoch_event = epoch_event
        self.slot_event = slot_event

    def event(self):
        if self.slot_event.malicious_slot:
            print('Malicious Event: release the obstruction of the gossiping the block to rest of the peers for slot: {}'.format(
                self.slot_event.counter))
            proposer = self.epoch_event.proposers[self.slot_event.counter %
                                                  SLOTS_PER_EPOCH]
            for validator_node in proposer.malicious_neighbors:
                validator_node.obstruct_gossiping = False
            proposer.obstruct_gossiping = False

    def __repr__(self):
        return 'Chain Slot {}'.format(self.slot_event.counter)
