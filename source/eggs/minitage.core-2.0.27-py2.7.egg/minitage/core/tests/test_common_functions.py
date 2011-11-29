#  Copyright (C) 2009, Mathieu PASQUET <kiorky@cryptelium.net>
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
import tempfile
import os

from minitage.core import common

path = tempfile.mkdtemp('minitagetestcomon')
tf = '%s/a'  % path

class TestCommon(unittest.TestCase):
    """TesMd5."""

    def testSplitStrip(self):
        """testSplitStrip."""
        self.assertEquals(
            common.splitstrip(' \n666\n2012\n\n\t\n'),
            ['666', '2012']
        )

    def testMd5(self):
        """testMd5."""
        open(tf,'w').write('a\n')
        self.assertTrue(
            common.test_md5(
                tf,
                '60b725f10c9c85c70d97880dfe8191b3'
            )
        )
        self.assertTrue(
            common.md5sum(tf),
            '60b725f10c9c85c70d97880dfe8191b3'
        )
        self.assertFalse(
            common.test_md5(tf,
                            'FALSE'
                           )
        )

    def testRemovePath(self):
        """testRemovePath."""
        file = tempfile.mkstemp()
        file = file[1]
        open(file,'w').write('a')
        self.assertTrue(os.path.isfile(file))
        common.remove_path(file)
        self.assertFalse(os.path.isfile(file))

        a = tempfile.mkdtemp()
        self.assertTrue(os.path.isdir(a))
        common.remove_path(a)
        self.assertFalse(os.path.isdir(a))

    def testAppendVar(self):
        """testAppendVar."""
        os.environ['TEST'] = 'test'
        self.assertEquals(os.environ['TEST'], 'test')
        common.append_env_var('TEST', ["toto"], sep='|', before=False)
        self.assertEquals(os.environ['TEST'], 'test|toto')
        common.append_env_var('TEST', ["toto"], sep='|', before=True)
        self.assertEquals(os.environ['TEST'], 'toto|test|toto')

    def testSubstitute(self):
        """testSubstitute."""
        open(tf,'w').write('foo')
        self.assertEquals(open(tf).read(), 'foo')
        common.substitute(tf,'foo','bar')
        self.assertEquals(open(tf).read(), 'bar')

    def testSystem(self):
        """testSystem."""
        self.assertRaises(SystemError, common.system, '6666')

    def testGetFromCache(self):
        """testGetFromCache."""
        ret, file = tempfile.mkstemp()
        filename = 'myfilename'
        download_cache = tempfile.mkdtemp()
        open(file, 'w').write('foo')
        self.assertRaises(
            common.MinimergeError,
            common.get_from_cache,
            'http://%s' % file,
            download_cache,
            offline = True
        )
        self.assertRaises(
            common.MinimergeError,
            common.get_from_cache,
            'file://%s' % file,
            file_md5 = 'false'
        )

        ret = common.get_from_cache('file://%s' % file,)
        self.assertEquals(open(ret).read(),'foo')
        ret = common.get_from_cache('file://%s' % file,
                                    download_cache = download_cache,)
        self.assertEquals(
            open(ret).read(),
            'foo'
        )
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommon))
    return suite

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommon))
    unittest.TextTestRunner(verbosity=2).run(suite)

# vim:set et sts=4 ts=4 tw=80:
