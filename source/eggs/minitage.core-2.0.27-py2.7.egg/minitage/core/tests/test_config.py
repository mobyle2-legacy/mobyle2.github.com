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
import optparse
import ConfigParser

from minitage.core  import api, cli, core

class testConfig(unittest.TestCase):
    """ test cli usage for minimerge"""

    def testConfig(self):
        """testConfig"""
        path = '%s/iamauniqueminiermgeconfigtest' % sys.exec_prefix
        mydict = {'path': path}
        test1 = """
touch %(path)s
cat << EOF > %(path)s
[minimerge]
minilays =
    dir1
    $HOME/test_minimerge1
EOF""" % mydict
        os.system(test1)
        sys.argv = [sys.argv[0], '--config', path, 'bar']
        opts = cli.do_read_options()
        minimerge = api.Minimerge(opts)

        test2 = """
touch %(path)s
cat << EOF > %(path)s
i am not a config file
EOF""" % mydict
        os.system(test2)
        sys.argv = [sys.argv[0], '--config', path, 'bar']
        opts = cli.do_read_options()
        self.assertRaises(core.InvalidConfigFileError, api.Minimerge, opts)
        # cleanup
        os.remove(path)

def test_suite():            
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testConfig))
    return suite    

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testConfig))
    unittest.TextTestRunner(verbosity=2).run(suite)

