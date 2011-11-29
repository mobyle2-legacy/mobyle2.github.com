# Copyright (C) 2009, Mathieu PASQUET <kiorky@cryptelium.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the <ORGANIZATION> nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.



__docformat__ = 'restructuredtext en'

import unittest

from minitage.core.collections import LazyLoadedList, LazyLoadedDict

class testLazyLoadedLists(unittest.TestCase):
    """LazyLoadedList tests."""

    def testLoadedStateChanges(self):
        """Test lazy loading of lazyLoadedLists."""
        lazyLoadedList = LazyLoadedList()
        self.assertFalse(lazyLoadedList.isLoaded())
        lazyLoadedList.append('foo')
        self.assertFalse(lazyLoadedList.isLoaded())
        item = lazyLoadedList[0]
        self.assertTrue(lazyLoadedList.isLoaded())

    def testIn(self):
        """Test insertion in list."""
        lazyLoadedList = LazyLoadedList()
        self.assertFalse(lazyLoadedList.isLoaded())
        self.assertFalse('foo' in lazyLoadedList)
        lazyLoadedList.append('foo')
        self.assertTrue('foo' in lazyLoadedList)
        self.assertTrue(lazyLoadedList.isLoaded())

    def testAdd(self):
        """Test append on list."""
        lazyLoadedList = LazyLoadedList()
        self.assertFalse(lazyLoadedList.isLoaded())
        lazyLoadedList.append(0)
        self.assertTrue(0 == lazyLoadedList.index(0))
        self.assertTrue(lazyLoadedList.isLoaded())

    def testSlices(self):
        """Test sub slices of list."""
        lazyLoadedList = LazyLoadedList()
        self.assertFalse(lazyLoadedList.isLoaded())
        for i in range(5):
            lazyLoadedList.append(i)
        self.assertFalse(lazyLoadedList.isLoaded())
        ta = lazyLoadedList[:2]
        tb = lazyLoadedList[4:]
        tc = lazyLoadedList[:]
        self.assertTrue(lazyLoadedList.isLoaded())
        self.assertTrue([0, 1] == ta)
        self.assertTrue([0, 1, 2, 3, 4] == tc)
        self.assertTrue([4] == tb)


class testLazyLoadedDicts(unittest.TestCase):
    """LazyLoadedDict tests."""

    def testLoadedStateChanges(self):
        """Test lazy loading of lazyLoadedDict."""
        lazyLoadedDict = LazyLoadedDict()
        self.assertFalse(0 in lazyLoadedDict.items)
        lazyLoadedDict[0] = 'foo'
        self.assertFalse(0 in lazyLoadedDict.items)
        item = lazyLoadedDict[0]
        self.assertTrue(0 in lazyLoadedDict.items)

    def testIn(self):
        """Test in operator in dictonary."""
        lazyLoadedDict = LazyLoadedDict()
        self.assertFalse('foo' in lazyLoadedDict.items)
        self.assertFalse('foo' in [key for key in lazyLoadedDict])
        lazyLoadedDict['foo'] = 'foo'
        self.assertTrue('foo' in [key for key in lazyLoadedDict])
        self.assertFalse('foo' in lazyLoadedDict.items)
        a = lazyLoadedDict['foo']
        self.assertTrue(a and 'foo' in lazyLoadedDict.items)

    def testNotIn(self):
        """Test non-appartenance of an element in the dictonary."""
        lazyLoadedDict = LazyLoadedDict()
        self.assertFalse('foo' in lazyLoadedDict.items)
        self.assertTrue('foo'  not in lazyLoadedDict.items)
        self.assertFalse('foo' in [key for key in lazyLoadedDict])
        lazyLoadedDict['foo'] = 'foo'
        self.assertTrue('foo' in [key for key in lazyLoadedDict])
        self.assertFalse('foo' in lazyLoadedDict.items)
        a = lazyLoadedDict['foo']
        self.assertTrue(a and 'afoo' not in lazyLoadedDict.items)

    def testAdd(self):
        """Test addition of an element in the dictonary."""
        lazyLoadedDict = LazyLoadedDict()
        self.assertFalse(0 in lazyLoadedDict.items)
        lazyLoadedDict[0] = 0
        keys = [key for key in lazyLoadedDict]
        self.assertTrue(lazyLoadedDict.has_key(0))
        item = lazyLoadedDict[0]
        self.assertTrue(len(lazyLoadedDict.items) == 1)

def test_suite():            
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testLazyLoadedLists))
    suite.addTest(unittest.makeSuite(testLazyLoadedDicts))
    return suite 

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testLazyLoadedLists))
    suite.addTest(unittest.makeSuite(testLazyLoadedDicts))
    unittest.TextTestRunner(verbosity=2).run(suite)

