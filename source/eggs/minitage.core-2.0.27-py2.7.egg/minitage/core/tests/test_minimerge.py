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
import tempfile

from minitage.core import api, cli, objects, core
from minitage.core import update
from minitage.core.tests import test_common
from minitage.core import tests
from minitage.core import version


__cwd__ = os.getcwd()


path = '%s/test' % os.path.expanduser(tempfile.mkdtemp())
testopts = dict(path=path)
minilay = '%(path)s/minilays/myminilay1' % testopts
class testMinimerge(unittest.TestCase):
    """testMinimerge"""

    def setUp(self):
        """."""
        os.chdir(__cwd__)
        self.minimerge10 = tempfile.mkstemp()[1]
        thisp = os.path.dirname('__file__')
        shutil.copy2(
            os.path.join(tests.__path__[0], 'minimerge_10.cfg'),
            self.minimerge10
        )
        test_common.createMinitageEnv(path)
        os.makedirs(minilay)

        minibuilds = [
"""
[minibuild]
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-0
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-4 minibuild-1
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-2
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-0
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-7
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-5
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-6
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-8
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-0 minibuild-3
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-11
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-12
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-13
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-10
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""" ]


        pythonmbs = [
#1000
"""
[minibuild]
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=dependencies
""", #1001
"""
[minibuild]
dependencies=meta-python minibuild-1005
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=dependencies
""", #1002
"""
[minibuild]
dependencies=python-2.4 minibuild-1005
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=dependencies
""", #1003
"""
[minibuild]
dependencies=python-2.5 minibuild-1005
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=dependencies
""", #1004
"""
[minibuild]
dependencies=minibuild-1005
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=dependencies
""", #1005
"""
[minibuild]
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=eggs
""",
]


        for index, minibuild in enumerate(minibuilds):
            open('%s/minibuild-%s' % (minilay, index), 'w').write(minibuild)

        os.system("""cd %s ;
                  hg init;
                  hg add ;
                  hg ci -m 1;""" % minilay)
        for index, minibuild in enumerate(pythonmbs):
            open('%s/minibuild-100%s' % (minilay, index), 'w').write(minibuild)

        # fake 3 pythons.
        for minibuild in ['python-2.4', 'python-2.5', 'python-2.6']:
            open('%s/%s' % (minilay, minibuild), 'w').write("""
[minibuild]
src_uri=http://hg.minitage.org/minitage
src_type=hg
install_method=buildout
category=dependencies""")

        open('%s/%s' % (minilay, 'meta-python'), 'w').write("""
[minibuild]
dependencies=python-2.4 python-2.5 python-2.6
src_uri=http://hg.minitage.org/minitage
src_type=hg
category=meta
install_method=buildout""")

        os.system("""
                  cd %s ;
                  echo "[paths]">.hg/hgrc
                  echo "default = %s">>.hg/hgrc
                  hg add;
                  hg ci -m 2;""" % (minilay, minilay))


    def tearDown(self):
        """."""
        os.unlink(self.minimerge10)
        os.chdir(__cwd__)
        shutil.rmtree(os.path.expanduser(path))

#    def testGetInstalledPackage(self):
#        """testGetInstalledPackage"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        os.makedirs(py24p)
#        minimerge.record_minibuild(py24)
#        mb = minimerge.get_installed_minibuild(py24)
#        # packasdge is not installed properly
#        self.assertTrue(mb is None)
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        minimerge._fetch(py24)
#        minimerge._do_action('install', [py24])
#        # package is installed
#        mb = minimerge.get_installed_minibuild(py24)
#        self.assertEquals(os.path.join(py24p, '.minitage', 'minibuild'), mb.path)
#
#    def testRecordMinibuild(self):
#        """testRecordMinibuild"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        os.makedirs(py24p)
#        minimerge.record_minibuild(py24)
#        self.assertTrue(
#            '[minibuild]' in open(
#                os.path.join(py24p, '.minitage', 'minibuild')
#            ).read()
#        )
#
#    def testIsPackageToBeInstalled(self):
#        """testIsPackageToBeInstalled"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        minimerge._action = 'delete'
#        self.assertFalse(minimerge.is_package_to_be_installed(py24))
#        minimerge._action = 'install'
#        self.assertTrue(minimerge.is_package_to_be_installed(py24))
#        minimerge._fetch(py24)
#        self.assertTrue(minimerge.is_package_to_be_installed(py24))
#        minimerge._do_action('install', [py24])
#        self.assertFalse(minimerge.is_package_to_be_installed(py24))
#
#    def testIsPackageToBeReInstalled(self):
#        """testIsPackageToBeReInstalled"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        minimerge.action = 'reinstall'
#        self.assertTrue(minimerge.is_package_to_be_installed(py24))
#        self.assertFalse(minimerge.is_package_to_be_reinstalled(py24))
#        # we cant reinstall as it is not installed
#        minimerge._fetch(py24)
#        self.assertTrue(minimerge.is_package_to_be_installed(py24))
#        self.assertFalse(minimerge.is_package_to_be_reinstalled(py24))
#        # we cant reinstall as it is not the wanted action
#        minimerge._do_action('install', [py24])
#        minimerge._action = 'install'
#        self.assertFalse(minimerge.is_package_to_be_reinstalled(py24))
#        self.assertFalse(minimerge.is_package_to_be_installed(py24))
#        # reinstalling
#        minimerge._action = 'reinstall'
#        self.assertTrue(minimerge.is_package_to_be_reinstalled(py24))
#        self.assertFalse(minimerge.is_package_to_be_installed(py24))
#        # reinstall will run always
#        minimerge._do_action('reinstall', [py24])
#        self.assertTrue(minimerge.is_package_to_be_reinstalled(py24))
#        self.assertFalse(minimerge.is_package_to_be_installed(py24))
#
#    def testIsPackageToBeUpdated(self):
#        """testIsPackageToBeUpdated"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        minimerge.action = 'install'
#        minimerge._fetch(py24)
#        # package is not installed or just installed, no update
#        self.assertFalse(minimerge.is_package_to_be_updated(py24))
#        minimerge._do_action('install', [py24])
#        self.assertFalse(minimerge.is_package_to_be_updated(py24))
#        minimerge._action = 'install'
#        self.assertFalse(minimerge.is_package_to_be_updated(py24))
#        # we have enabled update unconditionnally
#        minimerge._update = True
#        self.assertTrue(minimerge.is_package_to_be_updated(py24))
#        minimerge._do_action('install', [py24])
#        self.assertTrue(minimerge.is_package_to_be_updated(py24))
#        # new revision
#        minimerge._action = 'install'
#        minimerge._update = False
#        content = open(py24.path).read()
#        self.assertFalse(minimerge.is_package_to_be_updated(py24))
#        fic = open(py24.path, 'w')
#        fic.write(content+'\nrevision=666\n')
#        fic.close()
#        py24 = api.Minibuild(path=py24.path, config=minimerge._config)
#        self.assertTrue(minimerge.is_package_to_be_updated(py24))
#        # new revision is installed, no update
#        minimerge._do_action('install', [py24])
#        self.assertFalse(minimerge.is_package_to_be_updated(py24))
#
#    def testIsPackageToBeDeleted(self):
#        """testIsPackageToBeDeleted"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        minimerge.action = 'install'
#        # package is not install, no delete
#        self.assertFalse(minimerge.is_package_to_be_deleted(py24))
#        minimerge._fetch(py24)
#        self.assertFalse(minimerge.is_package_to_be_deleted(py24))
#        minimerge._do_action('install', [py24])
#        # action is not delete
#        self.assertFalse(minimerge.is_package_to_be_deleted(py24))
#        # package must be deleted
#        minimerge._action = 'delete'
#        self.assertTrue(minimerge.is_package_to_be_deleted(py24))
#        minimerge._do_action('delete', [py24])
#        # package is not installed no more, no delete
#        self.assertFalse(minimerge.is_package_to_be_deleted(py24))
#
#    def testIsPackageToBeFetched(self):
#        """testIsPackageToBeFetched"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        self.assertTrue(minimerge.is_package_src_to_be_fetched(py24))
#        os.makedirs(py24p)
#        # package is not installed and unrelated
#        self.assertRaises(core.MinimergeError, minimerge.is_package_src_to_be_fetched, py24)
#        #fic = open(os.path.join(py24p, 'buildout.cfg'), 'w')
#        #fic.write()
#        #fic.close()
#        # package is incomplete
#        #self.assertTrue(minimerge.is_package_src_to_be_fetched(py24))
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        minimerge._fetch(py24)
#        minimerge._do_action('install', [py24])
#        # user package is fetched / up to date
#        self.assertFalse(minimerge.is_package_src_to_be_fetched(py24))
#        # user needs update
#        minimerge._update = True
#        self.assertFalse(minimerge.is_package_src_to_be_fetched(py24))
#        # package has new revision
#        minimerge._update = False
#        content = open(py24.path).read()
#        fic = open(py24.path, 'w')
#        fic.write(content+'\nrevision=666\n')
#        fic.close()
#        py24 = api.Minibuild(path=py24.path, config=minimerge._config)
#        self.assertFalse(minimerge.is_package_src_to_be_fetched(py24))
#
#    def testIsPackageToBeSrcUpdated(self):
#        """testIsPackageToBeSrcUpdated"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        os.makedirs(py24p)
#        # package is not installed
#        self.assertFalse(minimerge.is_package_src_to_be_updated(py24))
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        minimerge._fetch(py24)
#        minimerge._do_action('install', [py24])
#        # user package is fetched / up to date
#        self.assertFalse(minimerge.is_package_src_to_be_updated(py24))
#        # user needs update
#        minimerge._update = True
#        self.assertTrue(minimerge.is_package_src_to_be_updated(py24))
#        # package has new revision
#        minimerge._update = False
#        content = open(py24.path).read()
#        fic = open(py24.path, 'w')
#        fic.write(content+'\nrevision=666\n')
#        fic.close()
#        py24 = api.Minibuild(path=py24.path, config=minimerge._config)
#        self.assertTrue(minimerge.is_package_src_to_be_updated(py24))
#
#
#    def testGetRevisionAndHasNewRevision(self):
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        minimerge._fetch(py24)
#        minimerge._do_action('install', [py24])
#        # first install version 1
#        rev = minimerge.get_installed_revision(py24)
#        self.assertEquals(rev, 0)
#        self.assertFalse(minimerge.has_new_revision(py24))
#        content = open(py24.path).read()
#        fic = open(py24.path, 'w')
#        fic.write(content)
#        fic.write('\nrevision=1\n')
#        fic.close()
#        py24 = api.Minibuild(path=py24.path, config=minimerge._config)
#        self.assertTrue(minimerge.has_new_revision(py24))
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        minimerge._fetch(py24)
#        minimerge._do_action('install', [py24])
#        rev = minimerge.get_installed_revision(py24)
#        self.assertEquals(rev, 1)
#        py24 = api.Minibuild(path=py24.path, config=minimerge._config)
#        self.assertFalse(minimerge.has_new_revision(py24))
#
#    def testPackageMark(self):
#        """testPackageMark"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        self.assertFalse(minimerge.get_package_mark(py24, 'fetched'))
#        minimerge.set_package_mark(py24, 'fetched', 'iamatest')
#        self.assertTrue(minimerge.is_package_marked(py24, 'fetched'))
#        self.assertTrue(
#            isinstance(
#                minimerge.get_package_mark_as_file(py24, 'fetched'),
#                file
#            )
#        )
#        self.assertEquals(minimerge.get_package_mark(py24, 'fetched'), 'iamatest')
#
#    def testFetchPackageMark(self):
#        """testFetchPackageMark"""
#        package = test_common.createPackage(path)
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        py24 = minimerge._find_minibuild('python-2.4')
#        py24p = minimerge.get_install_path(py24)
#        if os.path.exists(py24p): shutil.rmtree(py24p)
#        py24.src_uri = 'file://%s' % package
#        py24.src_type = 'static'
#        self.assertFalse(minimerge.get_package_mark(py24, 'fetch'))
#        minimerge._fetch(py24)
#        self.assertTrue(minimerge.get_package_mark(py24, 'fetch'))
#
#    def testIsInstalled(self):
#       """testIsInstalled"""
#       package = test_common.createPackage(path)
#       sys.argv = [sys.argv[0], '--config',
#                   '%s/etc/minimerge.cfg' % path, 'foo']
#       opts = cli.do_read_options()
#       minimerge = api.Minimerge(opts)
#       py24 = minimerge._find_minibuild('python-2.4')
#       py24p = minimerge.get_install_path(py24)
#       if os.path.exists(py24p): shutil.rmtree(py24p)
#       mb = minimerge._find_minibuild('minibuild-0')
#       py24.src_uri = 'file://%s' % package
#       py24.src_type = 'static'
#       self.assertFalse(minimerge.is_installed(py24))
#       minimerge._fetch(py24)
#       self.assertFalse(minimerge.is_installed(py24))
#       minimerge._do_action('install', [py24])
#       self.assertTrue(minimerge.is_installed(py24))
#       # test reinstall
#       minimerge._do_action('install', [py24])
#       self.assertTrue(minimerge.is_installed(py24))
#
#    def testFindMinibuild(self):
#        """testFindMinibuild"""
#        # create minilays in the minilays dir, seeing if they get putted in
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        mb = minimerge._find_minibuild('minibuild-0')
#        self.assertEquals('minibuild-0', mb.name)
#
#    def testComputeDepsWithNoDeps(self):
#        """testComputeDepsWithNoDeps
#        m0 depends on nothing"""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        computed_packages = minimerge._compute_dependencies(['minibuild-0'])
#        mb = computed_packages[0]
#        self.assertEquals('minibuild-0', mb.name)
#
#    def testSimpleDeps(self):
#        """testSimpleDeps
#        test m1 -> m0"""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        computed_packages = minimerge._compute_dependencies(['minibuild-1'])
#        mb = computed_packages[0]
#        self.assertEquals(mb.name, 'minibuild-0')
#        mb = computed_packages[1]
#        self.assertEquals(mb.name, 'minibuild-1')
#
#    def testChainedandTreeDeps(self):
#        """testChainedandTreeDeps
#        Will test that this tree is safe:
#              -       m3
#                      /
#                     m2
#                     / \
#                    m4 m1
#                     \/
#                     m0
#
#               -   m9
#                  / \
#                 m0 m3
#        """
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        computed_packages = minimerge._compute_dependencies(['minibuild-3'])
#        wanted_list = ['minibuild-0', 'minibuild-4',
#                       'minibuild-1', 'minibuild-2', 'minibuild-3']
#        self.assertEquals([mb.name for mb in computed_packages], wanted_list)
#        computed_packages = minimerge._compute_dependencies(['minibuild-9'])
#        wanted_list = ['minibuild-0', 'minibuild-4', 'minibuild-1',
#                       'minibuild-2', 'minibuild-3', 'minibuild-9']
#        self.assertEquals([mb.name for mb in computed_packages], wanted_list)
#
#    def testRecursivity(self):
#        """testRecursivity
#        check that:
#             - m5  -> m6 -> m7
#             - m8  -> m8
#             - m10 -> m11 -> m12 -> m13 -> m10
#        will throw some recursity problems.
#        """
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#
#        minimerge = api.Minimerge(opts)
#        self.assertRaises(core.CircurlarDependencyError,
#                          minimerge._compute_dependencies, ['minibuild-6'])
#
#        minimerge = api.Minimerge(opts)
#        self.assertRaises(core.CircurlarDependencyError,
#                          minimerge._compute_dependencies, ['minibuild-8'])
#
#        minimerge = api.Minimerge(opts)
#        self.assertRaises(core.CircurlarDependencyError,
#                          minimerge._compute_dependencies, ['minibuild-13'])
#
#    def testMinibuildNotFound(self):
#        """testMinibuildNotFound
#        INOTINANYMINILAY does not exist"""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'foo']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        self.assertRaises(core.MinibuildNotFoundError,
#                          minimerge._find_minibuild, 'INOTINANYMINILAY')
#
#    def testCutDeps(self):
#        """testCutDeps"""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path,
#                    '--jump', 'minibuild-2',
#                    'minibuild-1', 'minibuild-2', 'minibuild-3']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        p =  minimerge._cut_jumped_packages(
#            minimerge._find_minibuilds(
#                ['minibuild-1', 'minibuild-2', 'minibuild-3']
#            )
#        )
#        self.assertEquals(
#            p,
#            minimerge._find_minibuilds(['minibuild-2', 'minibuild-3'])
#        )
#        minimerge._jump = '666'
#        q =  minimerge._cut_jumped_packages(
#            minimerge._find_minibuilds(
#                ['minibuild-1', 'minibuild-2', 'minibuild-3'])
#        )
#        self.assertEquals(
#            q,
#            minimerge._find_minibuilds(
#                ['minibuild-1', 'minibuild-2', 'minibuild-3']
#            )
#        )
#
#
#    def testFetchOffline(self):
#        """testFetchOffline"""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, '--offline', 'minibuild-0']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        self.assertTrue(minimerge._offline)
#
#
#    def testSelectPython(self):
#        """testSelectPython.
#        Goal of this test is to prevent uneccesary python versions
#        to be built.
#        """
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'minibuild-1000']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        self.assertTrue(minimerge._action, 'install')
#
#        # we install a dependency which is not a egg
#        # result is false, no eggs dict in return.
#        computed_packages0, p0 = minimerge._select_pythons(
#            minimerge._compute_dependencies(['minibuild-1000']))
#        self.assertFalse(p0)
#
#        # we install a dep that require meta-python
#        # the dict must contains eggs 2.6
#        # available python = 2.4/2.5/2.6
#        self._packages = ['minibuild-1001']
#        computed_packages1, p1 = minimerge._select_pythons(
#            minimerge._compute_dependencies(['minibuild-1001']))
#        for i in ['2.6']:
#            self.assertTrue(i in p1['minibuild-1005'])
#            self.assertTrue('python-%s' % i
#                            in [c.name for c in computed_packages1]
#                           )
#        # we fake a python-2.4 installation
#        os.makedirs(
#            os.path.join(minimerge._prefix, 'dependencies', 'python-2.4')
#        )
#
#        # we install a dep that require meta-python
#        # the dict must contains eggs 2.4 as there is
#        # a python2.4 allready installed
#        self._packages = ['minibuild-1001']
#        computed_packages1, p1 = minimerge._select_pythons(
#            minimerge._compute_dependencies(['minibuild-1001']))
#        for i in ['2.4']:
#            self.assertTrue(i in p1['minibuild-1005'])
#            self.assertTrue('python-%s' % i
#                            in [c.name for c in computed_packages1]
#                           )
#
#        # we install a dep that require python-2.4 but depends
#        # on a python egg 'minibuild-1005'
#        # the dict must contains eggs part againts 2.4
#        # available python = 2.4
#        deps = minimerge._compute_dependencies(['minibuild-1002'])
#        self._packages = ['minibuild-1002']
#        computed_packages2, p2 = minimerge._select_pythons(deps)
#        self.assertTrue('python-2.4'
#                        in [c.name for c in computed_packages2]
#                       )
#        self.assertTrue('python-2.5'
#                        not in [c.name for c in computed_packages2]
#                       )
#        self.assertTrue('2.4' in p2['minibuild-1005'])
#        self.assertTrue('2.5' not in p2['minibuild-1005'])
#
#        # we install a dep that require python-2.5
#        # the dict must contains eggs ==  2.5
#        # available python = 2.5
#        deps = minimerge._compute_dependencies(['minibuild-1003'])
#        self._packages = ['minibuild-1003']
#        computed_packages3, p3 = minimerge._select_pythons(deps)
#        self.assertTrue('python-2.5'
#                        in [c.name for c in computed_packages3]
#                       )
#        self.assertTrue('python-2.4'
#                        not in [c.name for c in computed_packages3]
#                       )
#        self.assertTrue('2.5' in p3['minibuild-1005'])
#        self.assertTrue('2.4' not in p3['minibuild-1005'])
#
#        # we install a dep that require only a egg, no pytthon
#        # is specified specificly
#        # the dict must contains eggs ==  2.4
#        # available python = 2.4
#        # thus because we created a fake 'python-2.4'
#        self._packages = ['minibuild-1004']
#        computed_packages4, p4 = minimerge._select_pythons(
#            minimerge._compute_dependencies(['minibuild-1004']))
#        for i in ['2.4']:
#            self.assertTrue(i in p4['minibuild-1005'])
#            self.assertTrue('python-%s'%i
#                            in [c.name for c in computed_packages4]
#                           )
#        # we install an egg directly
#        # the dict must contains eggs ==  2.5/2.4/2.6
#        # available python (ones installed):  2.4
#        self._packages = ['minibuild-1005']
#        minimerge._packages = ['minibuild-1005']
#        computed_packagest, pt = minimerge._select_pythons(
#            minimerge._compute_dependencies(['minibuild-1005']))
#        for i in ['2.4']:
#            self.assertTrue(i in pt['minibuild-1005'])
#            self.assertTrue('python-%s'%i
#                            in [c.name for c in computed_packagest]
#                           )
#        for i in ['2.5', '2.6']:
#            self.assertFalse(i in pt['minibuild-1005'])
#            self.assertFalse('python-%s'%i
#                            in [c.name for c in computed_packagest]
#                           )
#
#
#    def testActionDelete(self):
#        """testActionDelete."""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'minibuild-0']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#
#        ipath = '%s/dependencies/python-%s' % (path, '2.4')
#        test_common.make_dummy_buildoutdir(ipath)
#
#        py24 = minimerge._find_minibuild('python-2.4')
#        self.assertTrue(os.path.isdir(ipath))
#        minimerge._do_action('delete', [py24])
#        self.assertTrue(not os.path.isdir(ipath))
#
#    def testActionInstall(self):
#        """testActionInstall."""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'minibuild-0']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#
#        for i in ['2.4', '2.5']:
#            test_common.make_dummy_buildoutdir(
#                '%s/dependencies/python-%s' % (path, i)
#            )
#
#        test_common.make_dummy_buildoutdir(
#            '%s/eggs/%s' % (path, 'minibuild-1005')
#        )
#
#        my_d = {'python-2.4': '2.4'}
#        py24 = minimerge._find_minibuild('python-2.4')
#        respy24 = '%s/dependencies/python-2.4/testres' % path
#        minimerge._do_action('install', [py24], my_d)
#        py25 = minimerge._find_minibuild('python-2.5')
#        respy25 = '%s/dependencies/python-2.5/testres' % path
#
#        minimerge._do_action('install', [py24], my_d)
#        self.assertEquals(open(respy24,'r').read(), 'bar')
#        minimerge._do_action('install', [py25], my_d)
#        self.assertEquals(open(respy25,'r').read(), 'bar')
#
#        m1005 = minimerge._find_minibuild('minibuild-1005')
#        m1005res =   '%s/eggs/minibuild-1005/testres' % path
#        m1005res24 = '%s/eggs/minibuild-1005/testres2.4' % path
#        m1005res25 = '%s/eggs/minibuild-1005/testres2.5' % path
#        minimerge._do_action('install', [m1005], {'minibuild-1005' :
#                                                  ['2.4', '2.5']})
#        self.assertEquals(open(m1005res24,'r').read(), '2.4')
#        self.assertEquals(open(m1005res25,'r').read(), '2.5')
#        self.assertFalse(os.path.isfile(m1005res))
#
#    def testInvalidAction(self):
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'minibuild-0']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        test_common.make_dummy_buildoutdir(
#            '%s/dependencies/python-2.4' % path
#        )
#        py = minimerge._find_minibuild('python-2.4')
#        self.assertRaises(core.ActionError,
#                          minimerge._do_action,
#                          'invalid',
#                          [py]
#                         )
#
#    def testSync(self):
#        """testSync."""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'minibuild-0']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        os.system("cd %s;hg up -r 0" % minilay)
#        self.assertFalse(os.path.isfile('%s/%s' % (minilay, 'minibuild-1000')))
#        minimerge._sync()
#        self.assertTrue(
#            os.path.isdir(
#                '%s/minilays/%s' %
#                (path, 'dependencies')
#            )
#        )
#        self.assertTrue(os.path.isfile('%s/%s' % (minilay, 'minibuild-1000')))
#
#
#    def testFetchOnline(self):
#        """testFetchOnline"""
#        sys.argv = [sys.argv[0], '--config',
#                    '%s/etc/minimerge.cfg' % path, 'minibuild-0']
#        opts = cli.do_read_options()
#        minimerge = api.Minimerge(opts)
#        self.assertFalse(minimerge._offline)
#        minimerge._fetch(minimerge._find_minibuild('minibuild-0'))
#        self.assertTrue(os.path.isdir('%s/eggs/minibuild-0/.hg' % path))



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testMinimerge))
    return suite

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testMinimerge))
    unittest.TextTestRunner(verbosity=2).run(suite)


