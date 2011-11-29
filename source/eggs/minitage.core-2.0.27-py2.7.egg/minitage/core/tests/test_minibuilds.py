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

import ConfigParser
import optparse
import os
import shutil
import sys
import unittest
import StringIO
import tempfile

try:
    from os import uname
except:
    from platform import uname

from minitage.core import api, objects
from minitage.core.tests import test_common

mb_path = os.path.expanduser('~/iamatest-1.0')

class testMinibuilds(unittest.TestCase):
    """Test cli usage for minimerge."""

    def testValidNames(self):
        """testValidNames"""
        mb = api.Minibuild(path=mb_path)
        valid_names = []
        valid_names.append('meta-toto')
        valid_names.append('test-toto')
        valid_names.append('toto')
        valid_names.append('test-1.0')
        valid_names.append('test-test-1.0')
        valid_names.append('test-1.0.3')
        valid_names.append('test-1.0_beta444')
        valid_names.append('test-1.0_py2.4')
        valid_names.append('test-1.0_py2.5')
        valid_names.append('test-1.0_beta444_pre20071024')
        valid_names.append('test-1.0_alpha44')
        valid_names.append('test-1.0_alpha44_pre20071024')
        valid_names.append('test-1.0_pre20071024')
        valid_names.append('test-1.0_branch10')
        valid_names.append('test-1.0_branchHEAD10')
        valid_names.append('test-1.0_tagHEAD10')
        valid_names.append('test-1.0_r1')
        valid_names.append('test-1.0_rHEAD')
        valid_names.append('test-1.0_rTIP')
        for i in valid_names:
            # will fail if raise error anyway
            self.assertTrue(objects.check_minibuild_name(i))
        invalid_names = []
        invalid_names.append('test-')
        invalid_names.append('test-1.0_prout4')
        invalid_names.append('test-1.0_py3k')
        invalid_names.append('test_prout4-1.0')
        invalid_names.append('test-test-')
        invalid_names.append('meta-meta-')
        invalid_names.append('test-1.0_brancha10')
        invalid_names.append('test-1.0_branch.10')
        invalid_names.append('test-1.0_rnot')
        invalid_names.append('meta-')
        for i in invalid_names:
            # will fail if raise error anyway
            self.assertFalse(objects.check_minibuild_name(i))
        minibuild1 = """
[minibuild]
dependencies=python
src_type=hg
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
install_method=buildout
category=eggs
        """
        nvmbp ='/tmp/notvalidforminitage-'
        open(nvmbp,'w').write(minibuild1)
        mb = api.Minibuild(path=nvmbp)
        self.assertRaises(objects.InvalidMinibuildNameError, mb.load)
        os.remove(nvmbp)

    def testDepends(self):
        """testDepends"""
        minibuild1 = """
[minibuild]
dependencies=python
dependencies-linux=linux
dependencies-darwin=darwin
dependencies-freebsd=freebsd
src_type=hg
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
install_method=buildout
category=eggs
"""
        open(mb_path,'w').write(minibuild1)
        mb = api.Minibuild(path=mb_path).load()
        self.assertTrue('python' in mb.dependencies)
        tuname = uname()[0].lower()
        self.assertTrue(tuname in mb.dependencies)

    def testValidMinibuilds(self):
        """testValidMinibuilds"""
        minibuild1 = """
[minibuild]
dependencies=python
src_type=hg
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
install_method=buildout
category=eggs
"""
        open(mb_path,'w').write(minibuild1)
        mb = api.Minibuild(path=mb_path).load()
        self.assertTrue(True)

    def testNoMinibuildSection(self):
        """testNoMinibuildSection"""
        minibuild2 = """
[iamnotcalledminibuild]
dependencies=python
src_type=hg
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
install_method=buildout
category=eggs
"""
        open(mb_path,'w').write(minibuild2)
        mb = api.Minibuild(path=mb_path)
        self.assertRaises(objects.NoMinibuildSectionError, mb.load)

    def testInvalidConfig(self):
        """testInvalidConfig"""
        minibuild3 = """
dependencies=python
src_type=hg
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
install_method=buildout
category=eggs
"""
        open(mb_path,'w').write(minibuild3)
        mb = api.Minibuild(path=mb_path)
        self.assertRaises(objects.InvalidConfigFileError, mb.load)

    def testUriWithoutFetchMethod(self):
        """testUriWithoutFetchMethod"""
        minibuild = """
[minibuild]
category=eggs
dependencies=python
install_method=buildout
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
"""
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        self.assertRaises(objects.MissingFetchMethodError, mb.load)

    def testInvalidSrcType(self):
        """testInvalidSrcType"""
        minibuild = """
[minibuild]
category=eggs
dependencies=python
install_method=buildout
src_type=invalid
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
"""
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        self.assertRaises(objects.InvalidFetchMethodError, mb.load)
    def testSrcOpts(self):
        """testSrcOpts"""
        minibuild = """
[minibuild]
category=eggs
dependencies=python
install_method=buildout
src_type=hg
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_opts=-r666
"""
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        self.assertEquals('-r666', mb.src_opts)

    def testMeta(self):
        """testMeta"""
        minibuild = """
[minibuild]
dependencies=python
"""
        open(mb_path,'w').write(minibuild)
        # no tests there, if it has errors in loading, it will fail anyway...
        mb = api.Minibuild(path=mb_path).load()
        self.failUnless('python' in mb.dependencies)

    def testDefaults(self):
        """testDefaults"""
        minibuild = """
[minibuild]
dependencies=python
"""
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path).load()
        self.assertTrue(True)

    def testCategory(self):
        """testCategory"""
        minibuild = """
[minibuild]
dependencies=python
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_type=hg
install_method=buildout
category=eggs
"""
#        open(mb_path,'w').write(minibuild)
#        mb = api.Minibuild(path=mb_path).load()
#        self.assertEquals(mb.category,'eggs')
#
#        minibuild = """
#[minibuild]
#dependencies=python
#src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
#src_type=hg
#install_method=buildout
#category=invalid
#"""
#        mb = None
#        open(mb_path,'w').write(minibuild)
#        mb = api.Minibuild(path=mb_path)
#        self.assertRaises(objects.InvalidCategoryError, mb.load)

        minibuild = """
[minibuild]
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_type=hg
install_method=buildout
"""
#        mb = None
#        open(mb_path,'w').write(minibuild)
#        mb = api.Minibuild(path=mb_path)
#        self.assertRaises(objects.MissingCategoryError, mb.load)
#
#        minibuild = """
#[minibuild]
#src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
#src_type=hg
#install_method=buildout
#category=hehe/bypassed
#category-bypass = true
#"""
#        mb = None
#        open(mb_path,'w').write(minibuild)
#        mb = api.Minibuild(path=mb_path)
#        self.assertRaises(objects.InvalidCategoryError, mb.load)

        minibuild = """
[minibuild]
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_type=hg
install_method=buildout
category=bypassed
category-bypass = true
"""
        mb = None
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        self.assertEquals(mb.category, 'bypassed')

    def testMinibuildWithoutInstallMethodNeitherDependencies(self):
        """testMinibuildWithoutInstallMethodNeitherDependencies"""
        minibuild = """
[minibuild]
url=prout
"""
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        self.assertRaises(objects.EmptyMinibuildError, mb.load)


    def testLazyLoad(self):
        """testLazyLoad"""
        minibuild = """
[minibuild]
dependencies=python
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_type=hg
install_method=buildout
category=eggs
"""
        # minibuild is ok, just trying to get the catgory.
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        self.assertEquals(mb.category,'eggs')

        minibuild = """
[minibuild]
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_type=hg
install_method=buildout
category=eggs
"""
        # minibuild is ok, just trying to get the catgory.
        open(mb_path,'w').write(minibuild)
        mbd = api.Minibuild(path=mb_path)
        self.assertEquals(mbd.dependencies, [])
#
#        minibuild = """
#[minibuild]
#dependencies=python
#src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
#src_type=hg
#install_method=buildout
#category=invalid
#"""
#        mb = None
#        open(mb_path,'w').write(minibuild)
#        mb = api.Minibuild(path=mb_path)
#        self.assertRaises(objects.MinibuildException, mb.__getattribute__, 'category')

    def tearDown(self):
        """."""
        os.remove(mb_path)

    def setUp(self):
        """."""
        open(mb_path,'w').write('')


    def testInvalidInstallMethod(self):
        """testInvalidInstallMethod."""
        minibuild = """
[minibuild]
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_type=hg
install_method=buildoutaaaaaaaaaaaaa
category=zope
"""
        mb = None
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        self.assertRaises(objects.InvalidInstallMethodError, mb.load)

        minibuild = """
[minibuild]
src_uri=https://hg.minitage.org/minitage/buildouts/ultimate-eggs/elementtreewriter-1.0/
src_type=hg
install_method=buildoutaaaaaaaaaaaaa
category=zope
install-method-bypass = true
"""
        mb = None
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        self.assertEquals(mb.install_method, 'buildoutaaaaaaaaaaaaa')

    def testRevision(self):
        """testRevision"""
        minibuilds = [
            {'minibuild': """
[minibuild]
category=eggs
dependencies=python
install_method=buildout
src_type=hg
src_uri=${minitage-eggs}/${minitage-dependencies}
src_opts=${minitage-misc}
             """,
             'revision': 0}, {'minibuild': """
[minibuild]
category=eggs
dependencies=python
install_method=buildout
src_type=hg
src_uri=${minitage-eggs}/${minitage-dependencies}
src_opts=${minitage-misc}
revision=1
                              """, 'revision': 1}]

        for minibuild in minibuilds:
            open(mb_path, 'w').write(minibuild['minibuild'])
            mb = api.Minibuild(path=mb_path)
            mb.load()
            self.assertEquals(minibuild['revision'], mb.revision)

    def testWrite(self):
        """testRevision"""
        minibuilds = ["""
[minibuild]
#comment
category=eggs
dependencies=python
install_method=buildout
src_type=hg
src_uri=${minitage-eggs}/${minitage-dependencies}
                      """,]
        minibuild = minibuilds[0]
        data = dict(
            dependencies = ['foo', 'bar'],
            install_method = '',
            src_uri = 'foo2',
            description = 'foo3',
            src_type = 'svn',
            url = 'foo5',
            revision = '666',
            category = 'foo7',
            src_opts = 'foo9',
            src_md5 = 'foo10',
        )
        open(mb_path, 'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        mb.load()
        self.assertNotEquals(mb.category, 'foo7')
        mb.write(**data)
        self.assertEquals(
            open(mb_path).read(), 
            '\n[minibuild]\n'
            '#comment\n'
            'category=foo7\n'
            'dependencies=foo bar\n'
            'install_method=\n'
            'src_type=svn\n'
            'src_uri=foo2\n'
            'description = foo3\n'
            'url = foo5\n'
            'src_md5 = foo10\n'
            'src_opts = foo9\n'
            'revision = 666\n\n'
        )
        self.assertEquals(mb.category, 'foo7')
        del data['description']
        del data['dependencies']
        open(mb_path, 'w').write(minibuild)
        mb = api.Minibuild(path=mb_path)
        mb.load() 
        mb.write(**data)
        self.assertEquals(
            open(mb_path).read(), 
            '\n[minibuild]\n'
            '#comment\n'
            'category=foo7\n'
            'dependencies=python\n'
            'install_method=\n'
            'src_type=svn\n'
            'src_uri=foo2\n'
            'url = foo5\n'
            'src_md5 = foo10\n'
            'src_opts = foo9\n'
            'revision = 666\n\n'
        )


    def testVars(self):
        """testVars"""
        minibuild = """
[minibuild]
category=eggs
dependencies=python
install_method=buildout
src_type=hg
src_uri=${minitage-eggs}/${minitage-dependencies}
src_opts=${minitage-misc}
"""
        configs = """
[minitage.variables]
minitage-dependencies = http://hg.minitage.org/minitage/buildouts/dependencies
minitage-misc = ${minitage-eggs}/${minitage-dependencies}
minitage-eggs = http://hg.minitage.org/minitage/buildouts/eggs
"""
        s = tempfile.mkstemp()[1]
        f = open(s, 'w')
        f.write(configs)
        f = open(s, 'r')
        config = ConfigParser.ConfigParser()
        config.readfp(f)
        open(mb_path,'w').write(minibuild)
        mb = api.Minibuild(path=mb_path,
                           minitage_config=config
                           )
        mb.load()
        self.assertEquals('http://hg.minitage.org'
                          '/minitage/buildouts/eggs'
                          '/http://hg.minitage.org'
                          '/minitage/buildouts'
                          '/dependencies', mb.src_opts)
        self.assertEquals('http://hg.minitage.org'
                          '/minitage/buildouts/eggs'
                          '/http://hg.minitage.org'
                          '/minitage/buildouts'
                          '/dependencies', mb.src_uri)
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testMinibuilds))
    return suite

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testMinibuilds))
    unittest.TextTestRunner(verbosity=2).run(suite)

