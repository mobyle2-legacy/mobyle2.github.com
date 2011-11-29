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
from minitage.core import  makers

class TestInterfaces(unittest.TestCase):
    """TestInterfaces"""

    def testIMaker(self):
        """testIMaker"""
        i = makers.interfaces.IMaker()
        self.assertRaises(NotImplementedError,
                          i.install, 'foo', {'bar':'loo'})
        self.assertRaises(NotImplementedError,
                          i.reinstall, 'foo', {'bar':'loo'})
        self.assertRaises(NotImplementedError,
                          i.match, 'foo')
        self.assertRaises(NotImplementedError,
                          i.get_options, 'foo', 'foo')

    def testFactory(self):
        """testFactory"""
        f = makers.interfaces.IMakerFactory()
        buildout = f('buildout')
        self.assertEquals(buildout.__class__.__name__,
                          makers.buildout.BuildoutMaker.__name__)
        self.assertEquals(buildout.__module__,
                          makers.buildout.BuildoutMaker\
                          .__module__)
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestInterfaces))
    return suite

# vim:set et sts=4 ts=4 tw=80:
