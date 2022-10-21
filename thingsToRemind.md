### Things to Remind 

#### To-Dos

- [ ] Added attestation aggregation if needed, Confirm with nicolo
- [ ] find out if the randomness inserted in the node should be explicitly passed, confirm how random event are generated in this case
- [ ] Do we have to seperate the event of attestation and aggregration 
- [ ] Do we have to adapt Committee is actually decided an epoch earlier, Current we do it in the same epoch

#### Important Constants
``` python 
SLOTS_PER_EPOCH = 32 (6.4 mins duration)
SECONDS_PER_SLOT = 12 seconds
MAX_VALIDATORS_PER_COMMITTEE = 2048
MAX_COMMITTEES_PER_SLOT = 64
TARGET_COMMITTEE_SIZE = 128
MAX_ATTESTATIONS=128
TARGET_AGGREGATORS_PER_COMMITTEE=16
INTERVALS_PER_SLOT= 3
```

#### Important Concepts 
- Committee is actually decided an epoch earlier 
- Block Proposal starts at slot starting
- Attestation starts at 1/3 of the slot 
- Aggregation of Attestation starts at the 2/3 of the slot