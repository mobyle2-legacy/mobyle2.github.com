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
import os
import sys
import shutil
import optparse
import ConfigParser

from minitage.core import interfaces

class test(object):
        """."""


path = os.path.expanduser('~/iamauniquetestfileformatiwillberemoveafterthetest')


class testInterfaces(unittest.TestCase):
    """testInterfaces"""

    def testFactory(self):
        """testFactory"""
        config = """
[minibuild]
dependencies=python
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_type=hg
install_method=buildout
category=invalid

[minitage.interface]
item1=minitage.core.tests.test_interfaces:test
"""
        open('%s' % path, 'w').write(config)
        try:
            interfaces.IFactory('not', path)
        except interfaces.InvalidConfigForFactoryError,e:
            self.assertTrue(isinstance(e,
                                       interfaces.InvalidConfigForFactoryError))

        i = interfaces.IFactory('interface', path)
        self.assertEquals(i.products['item1'].__name__, 'test')
        self.assertRaises(interfaces.InvalidComponentClassError,
                          i.register, 'foo', 'foo.Bar')
        self.assertRaises(NotImplementedError, i.__call__, 'foo')

    def testProduct(self):
        """testProduct"""
        p = interfaces.IProduct()
        self.assertRaises(NotImplementedError, p.match, 'foo')
def test_suite():            
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testInterfaces)) 
    return suite     

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(test_suite())

# vim:set et sts=4 ts=4 tw=80:
