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

import sys
import os
import shutil
import unittest
import tempfile

from minitage.core import interfaces, makers, fetchers
from minitage.core.tests  import test_common
from minitage.core import api
from minitage.core import cli



ocwd = os.getcwd()
path = tempfile.mkdtemp()
ipath = tempfile.mkdtemp()
shutil.rmtree(path)
shutil.rmtree(ipath)
config=os.path.join(path,'etc','minimerge.cfg')
testopts = dict(path=path)
class TestBuildout(unittest.TestCase):
    """testBuildout"""

    def setUp(self):
        """."""
        os.chdir(ocwd)
        test_common.createMinitageEnv(path)
        test_common.make_dummy_buildoutdir(ipath)

    def tearDown(self):
        """."""
        if os.path.isdir(path):
            shutil.rmtree(path)
        if os.path.isdir(ipath):
            shutil.rmtree(ipath) 

    def testDelete(self):
        """testDelete"""
        p = '%s/%s' % (path, 'test2')
        if not os.path.isdir(p):
            os.mkdir(p)
        mf = makers.interfaces.IMakerFactory()
        b = mf('buildout')
        self.assertTrue(os.path.isdir(p))
        b.delete(p)
        self.assertFalse(os.path.isdir(p))

    def testInstall(self):
        """testInstall"""
        mf = makers.interfaces.IMakerFactory(config)
        buildout = mf('buildout')
        # must not die ;)
        buildout.install(ipath)
        self.assertTrue(True)

    def testInstallPart(self):
        """testInstall"""
        mf = makers.interfaces.IMakerFactory(config)
        buildout = mf('buildout')
        # must not die ;)
        buildout.install(ipath, {'parts': 'y'})
        self.assertEquals(open('%s/testbar' % ipath,'r').read(), 'foo')
        os.remove('%s/testbar' % ipath)


    def testInstallMultiPartStr(self):
        """testInstallMultiPartStr"""
        mf = makers.interfaces.IMakerFactory(config)
        buildout = mf('buildout')
        buildout.install(ipath, {'parts': ['y', 'z']})
        buildout.install(ipath, {'parts': 'y z'})
        self.assertEquals(open('%s/testbar' % ipath,'r').read(), 'foo')
        self.assertEquals(open('%s/testres' % ipath,'r').read(), 'bar')
        os.remove('%s/testbar' % ipath)
        os.remove('%s/testres' % ipath)


    def testInstallMultiPartList(self):
        """testInstallMultiPartList"""
        mf = makers.interfaces.IMakerFactory(config)
        buildout = mf('buildout')
        buildout.install(ipath, {'parts': ['y', 'z']})
        self.assertEquals(open('%s/testbar' % ipath,'r').read(), 'foo')
        self.assertEquals(open('%s/testres' % ipath,'r').read(), 'bar')
        os.remove('%s/testbar' % ipath)
        os.remove('%s/testres' % ipath)

    def testReInstall(self):
        """testReInstall"""
        mf = makers.interfaces.IMakerFactory(config)
        buildout = mf('buildout')
        # must not die ;)
        buildout.install(ipath)
        buildout.reinstall(ipath)
        self.assertTrue(True)

    def testGetOptions(self):
        """testGetOptions."""
        sys.argv = [sys.argv[0], '--config',
                    '%s/etc/minimerge.cfg' % path, 'minibuild-0']
        opts = cli.do_read_options()
        minimerge = api.Minimerge(opts)
        open('minibuild', 'w').write("""
[minibuild]
install_method=buildout
""")
        minibuild = api.Minibuild('minibuild')
        minibuild.category = 'eggs'
        minibuild.name = 'toto'
        mf = makers.interfaces.IMakerFactory(config)
        buildout = mf('buildout')
        pyvers = {'python_versions': ['2.4', '2.5']}
        options = buildout.get_options(minimerge, minibuild, **pyvers)
        self.assertEquals(options['parts'],
                          ['site-packages-2.4', 'site-packages-2.5'])
        minibuild.category = 'dependencies'
        options = buildout.get_options(minimerge, minibuild, **pyvers)
        minibuild.category = 'zope'
        options = buildout.get_options(minimerge, minibuild, **pyvers)
        self.assertEquals(options['parts'], [])

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBuildout))
    return suite

# vim:set et sts=4 ts=4 tw=80:
