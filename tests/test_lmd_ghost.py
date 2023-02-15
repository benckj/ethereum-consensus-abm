"""Module providing Function to change path"""
import sys
sys.path.append("../")
import eth_base as sample


##################
# actual testing

def test_0():
    "Simple test"
    B0 = sample.Block(emitter="genesis", parent=None, slot_no=0)
    B1 = sample.Block(emitter="genesis", parent=B0, slot_no=1)
    B2 = sample.Block(emitter="genesis", parent=B1, slot_no=2)
    B3 = sample.Block(emitter="genesis", parent=B2, slot_no=3)
    B4 = sample.Block(emitter="genesis", parent=B3, slot_no=4)
    B5 = sample.Block(emitter="genesis", parent=B3, slot_no=5)
    B6 = sample.Block(emitter="genesis", parent=B5, slot_no=6)
    B7 = sample.Block(emitter="genesis", parent=B5, slot_no=7)
    B8 = sample.Block(emitter="genesis", parent=B4, slot_no=8)
    B9 = sample.Block(emitter="genesis", parent=B5, slot_no=9)
    B10 = sample.Block(emitter="genesis", parent=B8, slot_no=10)

    blockchain = {B0, B1, B2, B3, B4, B5, B6, B7, B8, B9, B10}

    attestations = {'a': [B6],
					'b': [B7],
					'c': [B8],
					'd': [B9],
					'e': [B10],
                    'f': [B9]}

    test = sample.lmd_ghost(blockchain, attestations)
    assert(test is B9)


def test_1():
    "test tie-breaker"
    B0 = sample.Block(emitter="genesis", parent=None, slot_no=0)
    B1 = sample.Block(emitter="genesis", parent=B0, slot_no=1)
    B2 = sample.Block(emitter="genesis", parent=B1, slot_no=2)
    B3 = sample.Block(emitter="genesis", parent=B2, slot_no=3)
    B4 = sample.Block(emitter="genesis", parent=B3, slot_no=4)
    B5 = sample.Block(emitter="genesis", parent=B3, slot_no=5)
    B6 = sample.Block(emitter="genesis", parent=B5, slot_no=6)
    B7 = sample.Block(emitter="genesis", parent=B5, slot_no=7)
    B8 = sample.Block(emitter="genesis", parent=B4, slot_no=8)
    B9 = sample.Block(emitter="genesis", parent=B5, slot_no=9)
    B10 = sample.Block(emitter="genesis", parent=B8, slot_no=10)

    blockchain = {B0, B1, B2, B3, B4, B5, B6, B7, B8, B9, B10}

    attestations = {'a': [B6],
					'b': [B7],
					'c': [B8],
					'd': [B9],
					'e': [B10],
                }

    test = []
    for l in range(10):
        test.append(sample.lmd_ghost(blockchain, attestations))
    for l in range(10):
        assert(test[l] is test[0])


def test_2():
    "Test genesis only"
    B0 = sample.Block(emitter="genesis", parent=None, slot_no=0)

    blockchain = {B0}

    attestations = {}

    test = sample.lmd_ghost(blockchain, attestations)
    assert(test is B0)


def test_3():
    "Test chain only"
    B0 = sample.Block(emitter="genesis", parent=None, slot_no=0)
    B1 = sample.Block(emitter="genesis", parent=B0, slot_no=1)

    blockchain = {B0, B1}

    attestations = {}

    test = sample.lmd_ghost(blockchain, attestations)
    assert(test is B1)


def test_4():
    "Test chain only"
    B0 = sample.Block(emitter="genesis", parent=None, slot_no=0)
    B1 = sample.Block(emitter="genesis", parent=B0, slot_no=1)

    blockchain = {B0, B1}

    attestations = {"a": [B1]}

    test = sample.lmd_ghost(blockchain, attestations)
    assert(test is B1)


def test_5():
    "Test chain only"
    B0 = sample.Block(emitter="genesis", parent=None, slot_no=0)
    B1 = sample.Block(emitter="genesis", parent=B0, slot_no=1)

    blockchain = {B0, B1}

    attestations = {"a": [B0]}

    test = sample.lmd_ghost(blockchain, attestations)
    assert(test is B1)


def test_5():
    "Test chain only"
    B0 = sample.Block(emitter="genesis", parent=None, slot_no=0)

    blockchain = {B0}

    attestations = {"a": [B0]}

    test = sample.lmd_ghost(blockchain, attestations)
    assert(test is B0)


