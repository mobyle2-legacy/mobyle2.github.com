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
import minitage.core.interfaces as interfaces
import minitage.core.fetchers as fetchers
from minitage.core.fetchers import scm

class testInterfaces(unittest.TestCase):
    """testInterfaces"""

    def testIFetcher(self):
        """testIFetcher"""
        i = fetchers.interfaces.IFetcher('ls', 'ls')
        self.assertRaises(NotImplementedError,
                          i.update, 'foo', 'bar')
        self.assertRaises(NotImplementedError,
                          i.fetch_or_update, 'foo', 'bar')
        self.assertRaises(NotImplementedError,
                          i.fetch, 'foo', 'bar')
        self.assertRaises(NotImplementedError,
                          i.is_valid_src_uri, 'foo')
        self.assertRaises(NotImplementedError,
                          i.match, 'foo')
        self.assertRaises(NotImplementedError,
                          i._has_uri_changed, 'foo', 'bar')

    def testURI(self):
        """testURI"""
        re = fetchers.interfaces.URI_REGEX
        self.assertEquals(re.match('http://tld').groups()[1], 'http')
        self.assertEquals(re.match('mtn://tld').groups()[1], 'mtn')
        self.assertEquals(re.match('svn://tld').groups()[1], 'svn')
        self.assertEquals(re.match('cvs://tld').groups()[1], 'cvs')
        self.assertEquals(re.match('bzr://tld').groups()[1], 'bzr')
        self.assertEquals(re.match('https://tld').groups()[1], 'https')
        self.assertEquals(re.match('ftp://tld').groups()[1], 'ftp')
        self.assertEquals(re.match('hg://tld').groups()[1], 'hg')
        self.assertEquals(re.match('git://tld').groups()[1], 'git')
        self.assertEquals(re.match('ssh://tld').groups()[1], 'ssh')
        self.assertEquals(re.match('sftp://tld').groups()[1], 'sftp')
        self.assertEquals(re.match('file://tld').groups()[1], 'file')
        self.assertEquals(re.match('svn+ssh://tld').groups()[1], 'svn+ssh')

    def testInit(self):
        """testInit"""
        f = fetchers.interfaces.IFetcher('ls', 'ls', metadata_directory='.ls')
        self.assertEquals(f.name,'ls')
        self.assertEquals(f.executable,'ls')
        self.assertEquals(f.metadata_directory,'.ls')
        f = fetchers.interfaces.IFetcher('ls','/bin/ls')
        self.assertEquals(f.executable,'/bin/ls')

    def testFactory(self):
        """testFactory"""
        f = fetchers.interfaces.IFetcherFactory()
        svn = f('svn')
        hg = f('hg')
        self.assertEquals(hg.__class__.__name__,
                          fetchers.scm.HgFetcher.__name__)
        self.assertEquals(svn.__class__.__name__,
                          fetchers.scm.SvnFetcher.__name__)
        self.assertEquals(svn.__module__,
                          fetchers.scm.SvnFetcher.__module__)
        self.assertEquals(hg.__module__,
                          fetchers.scm.HgFetcher.__module__)
def test_suite():            
    suite = unittest.TestSuite()
    return suite   

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testInterfaces))
    unittest.TextTestRunner(verbosity=2).run(suite)

# vim:set et sts=4 ts=4 tw=80:
