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
import shutil
import os
import tempfile

from minitage.core.fetchers import interfaces
from minitage.core.fetchers import static as staticm

opts = dict(
    path=os.path.expanduser(tempfile.mkdtemp()),
    dest=os.path.expanduser(tempfile.mkdtemp()),
)

prefix = os.getcwd()

class testStatic(unittest.TestCase):
    """testStatic"""

    def setUp(self):
        """."""
        os.chdir(prefix)
        for dir in [ opts['path'], opts['dest']]:
            if not os.path.isdir(dir):
                os.makedirs(dir)
        f = open('%(path)s/file' % opts, 'w')
        f.write('666')
        f.flush()
        f.close()

    def tearDown(self):
        """."""
        if 'http_proxy' in os.environ:
            del os.environ['http_proxy']
        for dir in [ opts['path'], opts['dest']]:
            if os.path.isdir(dir):
                shutil.rmtree(dir)

    def testFetch(self):
        """testFetch"""
        static = staticm.StaticFetcher()
        static.fetch(opts['dest'],'file://%s/file' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.download')))
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], '.download/file')))
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file')))
        self.assertEquals(open('%s/%s' % (opts['dest'], 'file')).read(),
                               '666')

    def testProxysConfig(self):
        """testProxysConfig."""
        static = staticm.StaticFetcher({'minimerge': {'http_proxy': 'a a a'}})
        self.assertEquals(os.environ['http_proxy'], 'a a a')
        if 'http_proxy' in os.environ:
            del os.environ['http_proxy']

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testStatic))
    return suite

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testStatic))
    unittest.TextTestRunner(verbosity=2).run(suite)

# vim:set et sts=4 ts=4 tw=80:
