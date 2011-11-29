import unittest

from zopeskel.tests.test_zopeskeldocs import test_suite as doc_test_suite
from zopeskel.tests.test_base import test_suite as base_test_suite
from zopeskel.tests.test_vars import test_suite as vars_test_suite
from zopeskel.tests.test_zopeskel_script import test_suite as script_test_suite

def test_suite():
    """ it appears that the order here makes a difference, ensure that doc_test_suite
        is always added last
    """
    suite = unittest.TestSuite([
        base_test_suite(),
        vars_test_suite(),
        script_test_suite(),
        doc_test_suite(),
    ])
    return suite
    
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')