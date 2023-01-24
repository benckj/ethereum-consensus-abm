from .constants import *
import logging


class FixedTimeEvent():
    def __init__(self, interval, time=0, offset=0, rng=None):
        if not interval >= 0:
            raise ValueError("Interval must be positive")

        self.rng = rng
        self.interval = interval

        # Initialize offset of an event
        self.offset = offset

        self.next_event = time + self.offset
        self.counter = 0

    def trigger(self, time):
        while time > self.next_event:
            self.logging.debug(time)
            self.counter += 1
            response = self.event()
            self.next_event += self.interval
            return response
        return 

    def event(self):
        pass


class EpochEvent(FixedTimeEvent):
    def __init__(self, interval, validators, chainstate, rng=None, logging=logging):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.committees = []
        self.proposers = []
        self.logging = logging.getLogger('Epoch')
        self.v_n = len(self.validators)
        self.committee_size = int(self.v_n/SLOTS_PER_EPOCH)
        self.leftover = self.v_n - (self.committee_size * SLOTS_PER_EPOCH)
        self.chainstate = chainstate
        self.malicious_validators = [v for v in self.validators if v.malicious]

    def event(self):
        self.chainstate.update_epoch(self.counter)
        self.rng.shuffle(self.validators)
        self.committees = [[self.validators[v+c*self.committee_size] for v in range(self.committee_size)]
                           for c in range(SLOTS_PER_EPOCH)]

        self.proposers = [self.rng.choice(self.validators)
                          for c in range(SLOTS_PER_EPOCH)]

        j = list(range(SLOTS_PER_EPOCH))
        self.rng.shuffle(j)
        for i in range(1, self.leftover+1):
            self.committees[j[i-1]].append(self.validators[-i])

        self.logging.debug('New Epoch: Committees formed')

        return

    def __repr__(self):
        return 'Chain Epoch {}'.format(self.counter)


class SlotEvent(FixedTimeEvent):
    def __init__(self, interval, validators, epoch_event, chainstate, rng=None, logging=logging):
        super().__init__(interval, rng=rng)
        self.validators = validators
        self.epoch_event = epoch_event
        self.malicious_slot = False
        self.logging = logging.getLogger('Slot')
        self.chainstate = chainstate

    def event(self):
        self.logging.debug('proposing block for slot: {}'.format(self.counter))
        proposer = self.epoch_event.proposers[self.counter %
                                              SLOTS_PER_EPOCH]

        # Update chainstate parameters
        self.chainstate.update_slot(self.counter)
        self.chainstate.update_slot_committee_weight(len(self.epoch_event.committees[self.counter % SLOTS_PER_EPOCH]))

        # turn off the attesting power of the node if they have exercised the attesting in the previous slot
        for validator_node in [v for v in self.epoch_event.committees[(self.counter-1) % SLOTS_PER_EPOCH] if v.is_attesting == True]:
            validator_node.is_attesting = False

        # Enable the attesting power of the node if they exist in the slot
        for validator_node in [v for v in self.epoch_event.committees[self.counter % SLOTS_PER_EPOCH] if v.is_attesting == False]:
            validator_node.is_attesting = True

        proposer.propose_block(self.chainstate)

        self.logging.debug('Proposer Node {}: Consensus View {} Consensus Attestations: {}'.format(
            proposer, proposer.gasper.consensus_chain, proposer.state.attestations))

        malicious_committee = False
        for validator_node in self.epoch_event.committees[self.counter % SLOTS_PER_EPOCH]:
            if validator_node.malicious:
                malicious_committee = True

        if proposer.malicious and malicious_committee:
            self.malicious_slot = True
            attestation = None
            self.logging.warn('Malicious Node {}, So disabling block gossiping to honest node and coping the block and attestation to the rest of malicious group'.format(proposer))
            for validator_node in self.epoch_event.malicious_validators:
                validator_node.obstruct_gossiping = True
                validator_node.state.add_block(self.counter, block)

            for validator_node in self.epoch_event.malicious_validators:
                if validator_node.is_attesting: 
                    attestation = validator_node.attest(self.counter)

            for validator_node in self.epoch_event.malicious_validators:
                if not validator_node.is_attesting: 
                    validator_node.state.add_attestation(attestation)

    def __repr__(self):
        return 'Chain Slot {}'.format(self.counter)


class AttestationEvent(FixedTimeEvent):
    def __init__(self, interval, offset, epoch_event, chainstate, rng=None, logging=logging):
        super().__init__(interval, offset, rng=rng)
        self.epoch_event = epoch_event
        self.logging = logging.getLogger('Attestation')
        self.chainstate = chainstate

    def event(self):
        self.logging.debug('providing attestation for slot: {}'.format(self.chainstate.slot))
        for validator_node in self.epoch_event.committees[self.chainstate.slot % SLOTS_PER_EPOCH]:
            if validator_node.is_attesting:                 
                validator_node.attest(self.chainstate)
                self.logging.debug('Attestor Node {}: Consensus View {} Consensus Attestations: {}'.format(
                    validator_node, validator_node.gasper.consensus_chain, validator_node.state.attestations))

    def __repr__(self):
        return 'Attestation Event {}'.format(self.counter)


class AdversaryEvent(FixedTimeEvent):
    def __init__(self, interval, offset, slot_event, epoch_event, chainstate, rng=None, logging=logging):
        super().__init__(interval, offset, rng=rng)
        self.epoch_event = epoch_event
        self.slot_event = slot_event
        self.logging = logging.getLogger('Attack')
        self.chainstate = chainstate

    def event(self):
        if self.slot_event.malicious_slot:
            self.logging.warn('Malicious Event: release the obstruction of the gossiping the block to rest of the peers for slot: {}'.format(
                self.slot_event.counter))
            for validator_node in self.epoch_event.validators:
                if validator_node.malicious:
                    validator_node.obstruct_gossiping = False

    def __repr__(self):
        return 'Chain Slot {}'.format(self.slot_event.counter)
