 #Copyright (C) 2009, Mathieu PASQUET <kiorky@cryptelium.net>
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
import sys
import os
import tempfile
import shutil

from minitage.core import core, cli, api
from minitage.core.tests import test_common 


path = os.path.expanduser(tempfile.mkdtemp())
shutil.rmtree(path)

class TestCli(unittest.TestCase):
    """Test cli usage for minimerge."""
    def setUp(self):
        """."""
        test_common.createMinitageEnv(path)

    def tearDown(self):
        """."""
        shutil.rmtree(os.path.expanduser(path)) 
    
    def testActions(self):
        """Test minimerge actions."""
        actions = {'-R': 'reinstall',
                   '--rm': 'delete',
                   '--install': 'install',
                   '--sync': 'sync'}
        sys.argv = [sys.argv[0], '-c', 'non existing', 'foo']
        self.assertRaises(core.InvalidConfigFileError, cli.do_read_options)
        for action in actions:
            sys.argv = [sys.argv[0], action, '--config', os.path.join(path, 'etc', 'minimerge.cfg'), 'foo']
            opts = cli.do_read_options()
            minimerge = api.Minimerge(opts)
            self.assertEquals(getattr(minimerge, '_action'), opts['action'])

        sys.argv = [sys.argv[0], '--config', os.path.join(path, 'etc', 'minimerge.cfg'), 'foo']
        opts = cli.do_read_options()
        minimerge = api.Minimerge(opts)
        self.assertEquals(getattr(minimerge, '_action'), opts['action'])

        sys.argv = [sys.argv[0], '--config', os.path.join(path, 'etc', 'minimerge.cfg'), '--rm']
        self.assertRaises(core.NoPackagesError, cli.do_read_options)

        sys.argv = [sys.argv[0], '--config', os.path.join(path, 'etc', 'minimerge.cfg'), '--install', '--rm', 'foo']
        self.assertRaises(core.TooMuchActionsError, cli.do_read_options)

        sys.argv = [sys.argv[0], '--config', os.path.join(path, 'etc', 'minimerge.cfg'), '--reinstall', '--rm', 'foo']
        self.assertRaises(core.ConflictModesError, cli.do_read_options)

        sys.argv = [sys.argv[0], '--config', os.path.join(path, 'etc', 'minimerge.cfg'), '--fetchonly', '--offline', 'foo']
        self.assertRaises(core.ConflictModesError, cli.do_read_options)

        sys.argv = [sys.argv[0], '--config', os.path.join(path, 'etc', 'minimerge.cfg'), '--jump', 'foo', '--nodeps', 'foo']
        self.assertRaises(core.ConflictModesError, cli.do_read_options)

        sys.argv = [sys.argv[0], '--config', os.path.join(path, 'etc', 'minimerge.cfg'), '--reinstall', '--config',
                    'iamafilewhichdoesnotexist', 'foo']
        self.assertRaises(core.InvalidConfigFileError, cli.do_read_options)

    def testModes(self):
        """Test minimerge modes."""
        modes = ('offline', 'fetchonly', 'ask',
                 'debug', 'nodeps', 'pretend')
        for mode in modes:
            sys.argv = [sys.argv[0], '--%s' % mode, '--config' , os.path.join(path, 'etc', 'minimerge.cfg'), 'foo']
            opts = cli.do_read_options()
            minimerge = api.Minimerge(opts)
            self.assertTrue(getattr(minimerge, '_%s' % mode, False))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCli))
    return suite

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCli))
    unittest.TextTestRunner(verbosity=2).run(suite)

