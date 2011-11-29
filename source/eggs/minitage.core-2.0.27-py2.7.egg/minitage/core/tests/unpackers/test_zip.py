
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

from minitage.core.unpackers import interfaces

prefix = os.getcwd()

path = tempfile.mkdtemp()

class testZip(unittest.TestCase):
    """testZip."""

    def tearDown(self):
        """."""
        shutil.rmtree(path)
        os.makedirs(path)

    def testZipfile(self):
        """testZipfile."""
        os.chdir(path)
        os.system("""
                  mkdir a b;
                  echo "aaaa"> a/toto;
                  zip -qr toto.zip a;
                  rm -rf a""")
        self.assertFalse(os.path.isdir('a'))
        f = interfaces.IUnpackerFactory()
        zip = f('%s/toto.zip' % path)
        zip.unpack('%s/toto.zip' % path)
        zip.unpack('%s/toto.zip' % path, '%s/b' % path)
        self.assertTrue(os.path.isfile('a/toto'))
        self.assertEquals(open('a/toto').read(),'aaaa\n')
        self.assertTrue(os.path.isfile('b/a/toto'))

    def DesactivatedtestBz2file(self):
        """testTarbz2file."""
        os.chdir(path)
        os.system("""
                  mkdir a;
                  echo "aaaa"> a/toto;
                  bzip2 -kcz a/toto>toto.bz2;
                  rm -rf a""")
        self.assertFalse(os.path.isdir('a'))
        f = interfaces.IUnpackerFactory()
        tar = f('%s/toto.bz2' % path)
        tar.unpack('%s/toto.bz2' % path)
        self.assertTrue(os.path.isfile('toto'))
        self.assertEquals(open('a/toto').read(),'aaaa\n')

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testZip))
    unittest.TextTestRunner(verbosity=2).run(suite)

# vim:set et sts=4 ts=4 tw=80:
