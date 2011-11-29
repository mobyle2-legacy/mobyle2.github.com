# -*- coding: utf-8 -*-
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
import tempfile
from cStringIO import StringIO

from minitage.core.core import newline


def write(file, content):
    fic = open(file, 'w')
    fic.write(content)
    fic.flush()
    fic.close()

class testNewLine(unittest.TestCase):
    """testNewLine"""

    def setUp(self):
        """."""
        self.file = tempfile.mkstemp()[1]

    def tearDown(self):
        """."""
        if os.path.exists(self.file):
            os.unlink(self.file)

    def testNewLine(self):
        """testNewLine"""
        write(self.file,
"""
tata
test
"""
        )
        newline(self.file)
        self.assertEquals(
            '\ntata\ntest\n\n',
            open(self.file).read()
        )
        write(self.file,
"""
tata
test"""
        )
        newline(self.file)
        self.assertEquals(
            '\ntata\ntest\n\n',
            open(self.file).read()
        )


    def testEmptyFile(self):
        """testEmptyFile"""
        write(self.file,
              """"""
        )
        newline(self.file)
        self.assertEquals(
            '\n',
            open(self.file).read()
        )

    def testUtf8(self):
        """tUtf8"""
        write(self.file,
              """çà@~#ø€ç±ø"""
        )
        newline(self.file)
        self.assertEquals(
            '\xc3\xa7\xc3\xa0@~#\xc3\xb8\xe2\x82\xac\xc3\xa7\xc2\xb1\xc3\xb8\n\n',
            open(self.file).read()
        )

    def multipleLines(self):
        """multipleLines"""
        write(self.file,
"""
tata
test




"""
        )
        newline(self.file)
        self.assertEquals(
            '\ntata\ntest\n\n',
            open(self.file).read()
        )



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testNewLine))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(test_suite())



