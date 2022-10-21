import random as rnd

class FixedTimeEvent():
     def __init__(self, interval,time=0, offset=0):
        assert offset>=0, "offset must be positive"

        self.offset = offset
        self.interval = interval

        self.last_event = None
        self.next_event = time + self.offset

     def trigger(self, next_time):
         while next_time > self.next_event:
             self.event()
             self.counter += 1
             self.next_event += self.interval

             return True
         return False

     def event(self):
         pass

class Slot():
    # slot number
    _id = 0

    @classmethod
    def update(cls):
        cls._id += 1

    def __init__(self, committee, proposer, epoch, has_random_event=False, randomness=None):
        self.update()
        self.epoch = epoch
        self.committee = committee
        self.proposer = proposer
        if has_random_event:
            # set up random event 
            pass

    @property
    def id(self):
        return self._id

    def event(self):
        # proposer.event()
        self.proposer.slotRole = 'Proposer'
        self.proposer.event()
        for attestor in self.committee:
            attestor.slotRole = 'Validator'
            attestor.event()
        print(self.proposer,'proposed  and attested in the block in slot')

class EpochBoundary(FixedTimeEvent):
    # epoch number
    _id = 0
    slots_per_epoch = 32

    @classmethod
    def update(cls):
        cls._id += 1

    def __init__(self, interval, validators):
        super().__init__(interval)
        self.update()
        self.validators = validators
        self.shuffable_valdiators = validators
        self.no_of_validators = len(self.validators)
        self.committee_size = max(int(self.no_of_validators/self.slots_per_epoch), 10)

    @property
    def id(self):
        return self._id

    def event(self):
        """[Teja] This event should be handling multiple things.
        -> Epoch should iterate over 32 slots.
        -> Call each Slot to perform its actions
        -> later introduce a random event to select a random slot out of this particular epoch slots
         """

        comittees = self.get_committee()
        print('Epoch{}: Committees formed'.format(self._id))
        proposers = self.get_proposer()
        print('Epoch{}: Proposers formed'.format(self._id))
        for eachSlot in range(self.slots_per_epoch):
            slot = Slot(comittees[eachSlot], proposers[eachSlot], self)
            slot.event()
    
    def get_proposer(self):
        rnd.shuffle(self.shuffable_valdiators)
        return [self.shuffable_valdiators[c*self.committee_size  % len(self.validators)] for c in range(self.slots_per_epoch)]
    
    def get_committee(self):
        rnd.shuffle(self.shuffable_valdiators)
        return [[self.shuffable_valdiators[(v+c*self.committee_size) % len(self.validators)] for v in range(self.committee_size)] 
                           for c in range(self.slots_per_epoch)]
