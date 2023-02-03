import unittest
from unit_tests.lmdghost_test import *
from unit_tests.exante_reorg_test import *
from unit_tests.branchratio_calculation_test import *
from unit_tests.entropy_calculation_test import *
from unit_tests.mainchainrate_calculation_test import *
from unit_tests.proposer_boost_test import *


def suite():
    suite = unittest.TestSuite()
    suite.addTest(GHOST_TestCase('test_onelevel_heavyweight'))
    suite.addTest(GHOST_TestCase('test_onelevel_tieweight'))
    suite.addTest(GHOST_TestCase('test_twolevel_heavyweight'))
    suite.addTest(GHOST_TestCase('test_threelevel_heavyweight'))
    suite.addTest(GHOST_TestCase('test_from_annotated_spec'))
    suite.addTest(PB_Test('base_test_wo_pb'))
    suite.addTest(PB_Test('base_test'))
    suite.addTest(PB_Test('reorg_protection'))
    suite.addTest(ExAnteReOrg_TestCase('produce_emptyslot'))
    suite.addTest(ExAnteReOrg_TestCase('produce_emptySlot_and_blockinlater'))
    suite.addTest(ExAnteReOrg_TestCase('reorg'))
    suite.addTest(BranchRatio_TestCases('test'))
    suite.addTest(Entropy_TestCases('test'))
    suite.addTest(MainChainRate_TestCases('test'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
