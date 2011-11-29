# Gopyright (C) 2009, Mathieu PASQUET <kiorky@cryptelium.net>
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

from minitage.core.fetchers import scm, interfaces
from minitage.core.common import MinimergeError

opts = dict(
    path=os.path.expanduser(tempfile.mkdtemp()),
    dest=os.path.expanduser(tempfile.mkdtemp()),
    wc=os.path.expanduser(tempfile.mkdtemp()),
)

prefix = os.getcwd()

class testGit(unittest.TestCase):
    """testGit"""

    def setUp(self):
        """."""
        os.chdir(prefix)
        md = tempfile.mkdtemp()
        opts.update({'path2': md})
        os.system("""
                 mkdir -p %(path2)s
                 rm -rf %(path)s
                 cd %(path2)s
                 echo '666'>file
                 git init
                 git add .
                 git commit -a -m 'initial import'
                 echo '666'>file2
                 git add .
                 git commit -m 'second revision'
                 git clone %(path2)s %(path)s
                  """ % opts)

    def tearDown(self):
        """."""
        for dir in [ opts['path'], opts['dest']]:
            if os.path.isdir(dir):
                shutil.rmtree(dir)

    def testUrlChanged(self):
        """testUrlChanged"""
        git = scm.GitFetcher()
        git.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.git')))
        self.assertFalse(
            git._has_uri_changed(
                opts['dest'],
                'file://%s' % opts['path'],
            )
        )
        self.assertTrue(git._has_uri_changed('hehe_changed', opts['dest']))

    def testRemoveVersionnedDirs(self):
        """testRemoveVersionnedDirs"""
        git = scm.GitFetcher()
        git.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.git')))
        os.mkdir(os.path.join(opts['dest'],'part'))
        git._remove_versionned_directories(opts['dest'])
        self.assertTrue(os.path.isdir(  os.path.join(opts['dest'],'part')))
        self.assertFalse(os.path.isdir( os.path.join(opts['dest'],'.git')))
        self.assertFalse(os.path.isfile(os.path.join(opts['dest'],'file2')))
        git.update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.git')))

    def testScmInvalidUri(self):
        """testScmInvalidUri"""
        git = scm.GitFetcher()
        self.assertRaises(interfaces.InvalidUrlError,
                          git.fetch, 'somewhere', 'invalidsrcuri')


    def testFetch(self):
        """testFetch"""
        git = scm.GitFetcher()
        git.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.git')))

    def testFetchToParticularRevision(self):
        """testFetchToParticularRevision"""
        git = scm.GitFetcher()
        git.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision='HEAD~'))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.git')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))

    def testUpdate(self):
        """testUpdate"""
        git = scm.GitFetcher()
        git.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision='HEAD~'))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.git')))
        git.update(opts['dest'], 'file://%s master' % opts['path'])
        self.assertTrue(os.path.isfile(os.path.join(opts['dest'], 'file2')))
        git.update(opts['dest'], 'file://%s master' % opts['path'], dict(revision='HEAD~'))
        self.assertFalse(os.path.isfile(os.path.join(opts['dest'], 'file2')))
        shutil.rmtree(opts['dest'])
        git.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision='HEAD~'))
        git.update(opts['dest'])
        self.assertTrue(os.path.isfile(os.path.join(opts['dest'], 'file2')))

    def testFetchOrUpdate_fetch(self):
        """testFetchOrUpdate_fetch"""
        git = scm.GitFetcher()
        git.fetch_or_update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.git')))

    def testFetchOrUpdate_update(self):
        """testFetchOrUpdate_update"""
        git = scm.GitFetcher()
        git.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision='HEAD~'))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.git')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))
        git.fetch_or_update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))

class testBzr(unittest.TestCase):
    """testBzr"""

    def setUp(self):
        """."""
        os.chdir(prefix)
        os.system("""
                 mkdir -p  %(path)s
                 cd %(path)s
                 echo '666'>file
                 bzr init
                 bzr add .
                 bzr ci -m 'initial import'
                 echo '666'>file2
                 bzr add
                 bzr ci -m 'second revision'
                 """ % opts)

    def tearDown(self):
        """."""
        for dir in [ opts['path'], opts['dest']]:
            if os.path.isdir(dir):
                shutil.rmtree(dir)

    def testUrlChanged(self):
        """testUrlChanged"""
        bzr = scm.BzrFetcher()
        bzr.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.bzr')))
        self.assertFalse(
            bzr._has_uri_changed(
                opts['dest'],
                'file://%s' % opts['path'],
            )
        )
        self.assertTrue(bzr._has_uri_changed('hehe_changed', opts['dest']))

    def testRemoveVersionnedDirs(self):
        """testRemoveVersionnedDirs"""
        bzr = scm.BzrFetcher()
        bzr.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.bzr')))
        os.mkdir(os.path.join(opts['dest'],'part'))
        bzr._remove_versionned_directories(opts['dest'])
        self.assertTrue(os.path.isdir(  os.path.join(opts['dest'],'part')))
        self.assertFalse(os.path.isdir( os.path.join(opts['dest'],'.bzr')))
        self.assertFalse(os.path.isfile(os.path.join(opts['dest'],'file2')))
        bzr.update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.bzr')))

    def testScmInvalidUri(self):
        """testScmInvalidUri"""
        bzr = scm.BzrFetcher()
        self.assertRaises(interfaces.InvalidUrlError,
                          bzr.fetch, 'somewhere', 'invalidsrcuri')


    def testFetch(self):
        """testFetch"""
        bzr = scm.BzrFetcher()
        bzr.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.bzr')))

    def testFetchToParticularRevision(self):
        """testFetchToParticularRevision"""
        bzr = scm.BzrFetcher()
        bzr.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision=0))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.bzr')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))

    def testUpdate(self):
        """testUpdate"""
        bzr = scm.BzrFetcher()
        bzr.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision=0))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.bzr')))
        bzr.update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))
        bzr.update(opts['dest'], 'file://%s' % opts['path'], dict(revision=0))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))

    def testFetchOrUpdate_fetch(self):
        """testFetchOrUpdate_fetch"""
        bzr = scm.BzrFetcher()
        bzr.fetch_or_update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.bzr')))

    def testFetchOrUpdate_update(self):
        """testFetchOrUpdate_update"""
        bzr = scm.BzrFetcher()
        bzr.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision=0))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.bzr')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))
        bzr.fetch_or_update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))



class testHg(unittest.TestCase):
    """testHg"""

    def setUp(self):
        """."""
        os.chdir(prefix)
        os.system("""
                 mkdir -p  %(path)s         2>&1 >> /dev/null
                 cd %(path)s                2>&1 >> /dev/null
                 echo '666'>file            2>&1 >> /dev/null
                 hg init                    2>&1 >> /dev/null
                 hg add                     2>&1 >> /dev/null
                 hg ci -m 'initial import'  2>&1 >> /dev/null
                 echo '666'>file2           2>&1 >> /dev/null
                 hg add                     2>&1 >> /dev/null
                 hg ci -m 'second revision' 2>&1 >> /dev/null
                 """ % opts)

    def tearDown(self):
        """."""
        for dir in [ opts['path'], opts['dest']]:
            if os.path.isdir(dir):
                shutil.rmtree(dir)

    def testUrlChanged(self):
        """testUrlChanged"""
        hg = scm.HgFetcher()
        hg.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.hg')))
        self.assertFalse(
            hg._has_uri_changed(
                opts['dest'],
                'file://%s' % opts['path'],
            )
        )
        self.assertTrue(hg._has_uri_changed('hehe_changed', opts['dest']))

    def testRemoveVersionnedDirs(self):
        """testRemoveVersionnedDirs"""
        hg = scm.HgFetcher()
        hg.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.hg')))
        os.mkdir(os.path.join(opts['dest'],'part'))
        hg._remove_versionned_directories(opts['dest'])
        self.assertTrue(os.path.isdir(  os.path.join(opts['dest'],'part')))
        self.assertFalse(os.path.isdir( os.path.join(opts['dest'],'.hg')))
        self.assertFalse(os.path.isfile(os.path.join(opts['dest'],'file2')))
        hg.update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.hg')))

    def testScmInvalidUri(self):
        """testScmInvalidUri"""
        hg = scm.HgFetcher()
        self.assertRaises(interfaces.InvalidUrlError,
                          hg.fetch, 'somewhere', 'invalidsrcuri')


    def testFetch(self):
        """testFetch"""
        hg = scm.HgFetcher()
        hg.fetch(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.hg')))

    def testFetchToParticularRevision(self):
        """testFetchToParticularRevision"""
        hg = scm.HgFetcher()
        hg.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision=0))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.hg')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))

    def testUpdate(self):
        """testUpdate"""
        hg = scm.HgFetcher()
        hg.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision=0))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.hg')))
        hg.update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))
        hg.update(opts['dest'], 'file://%s' % opts['path'], dict(revision=0))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))

    def testFetchOrUpdate_fetch(self):
        """testFetchOrUpdate_fetch"""
        hg = scm.HgFetcher()
        hg.fetch_or_update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.hg')))

    def testFetchOrUpdate_update(self):
        """testFetchOrUpdate_update"""
        hg = scm.HgFetcher()
        hg.fetch(opts['dest'], 'file://%s' % opts['path'], dict(revision=0))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['dest'], '.hg')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))
        hg.fetch_or_update(opts['dest'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['dest'], 'file2')))


class testSvn(unittest.TestCase):
    """testSvn"""

    def setUp(self):
        """."""
        os.chdir(prefix)
        # make an svn repo
        os.system("""
                 mkdir -p  %(path)s                  2>&1 >> /dev/null
                 cd %(path)s                         2>&1 >> /dev/null
                 svnadmin create .                   2>&1 >> /dev/null
                 mkdir -p  %(dest)s                  2>&1 >> /dev/null
                 svn co file://%(path)s %(dest)s     2>&1 >> /dev/null
                 cd %(dest)s                         2>&1 >> /dev/null
                 echo '666'>file                     2>&1 >> /dev/null
                 svn add file                        2>&1 >> /dev/null
                 svn ci -m 'initial import'          2>&1 >> /dev/null
                 cho '666'>file2                    2>&1 >> /dev/null
                 svn add file2                       2>&1 >> /dev/null
                 svn ci -m 'second revision'         2>&1 >> /dev/null
                 svn up                              2>&1 >> /dev/null
                 """ % opts)

    def tearDown(self):
        """."""
        for dir in [opts['wc'], opts['path'], opts['dest']]:
            if os.path.isdir(dir):
                shutil.rmtree(dir)

    def testUrlChanged(self):
        """testUrlChanged"""
        svn = scm.SvnFetcher()
        svn.fetch(opts['wc'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'], '.svn')))
        self.assertFalse(
            svn._has_uri_changed(
                opts['wc'],
                'file://%s' % opts['path'],
            )
        )
        self.assertTrue(svn._has_uri_changed(opts['wc'], 'hehe_changed'))

    def testRemoveVersionnedDirs(self):
        """testRemoveVersionnedDirs"""
        svn = scm.SvnFetcher()
        svn.fetch(opts['wc'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'], '.svn')))
        svn._has_uri_changed(opts['wc'], 'file://%s' % opts['path'])
        os.mkdir('%s/%s' % (opts['wc'],'part'))
        svn._remove_versionned_directories(opts['wc'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'],'part')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['wc'],'file2')))
        svn.fetch(opts['wc'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'], '.svn')))

    def testScmInvalidUri(self):
        """testScmInvalidUri"""
        svn = scm.SvnFetcher()
        self.assertRaises(interfaces.InvalidUrlError,
                          svn.fetch, 'somewhere', 'invalidsrcuri')

    def testInvalidReturn(self):
        """testInvalidReturn"""
        svn = scm.SvnFetcher()
        svn.executable = 'notsvn'
        # shell will not find that command, heh
        self.assertRaises(interfaces.FetcherNotInPathError,
                          svn.fetch, 'somewhere', 'file://nowhere')

        svn = scm.SvnFetcher()
        # prevent mercurial from writing in dest ;)
        if not os.path.isdir(opts['wc']):
            os.makedirs(opts['wc'])
        os.chmod(opts['wc'], 660)
        # it will crash luke
        self.assertRaises(interfaces.FetcherRuntimeError,
                          svn.fetch, opts['wc'], 'file://%s' % opts['path'])
        os.removedirs(opts['wc'])

    def testFetch(self):
        """testFetch"""
        svn = scm.SvnFetcher()
        svn.fetch(opts['wc'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'], '.svn')))

    def testFetchToParticularRevision(self):
        """testFetchToParticularRevision"""
        svn = scm.SvnFetcher()
        svn.fetch(opts['wc'], 'file://%s' % opts['path'], dict(revision=1))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'], '.svn')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['wc'], 'file2')))

    def testUpdate(self):
        """testUpdate"""
        svn = scm.SvnFetcher()
        svn.fetch(opts['wc'], 'file://%s' % opts['path'], dict(revision=1))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'], '.svn')))
        svn.update(opts['wc'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['wc'], 'file2')))
        svn.update(opts['wc'], 'file://%s' % opts['path'], dict(revision=1))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['wc'], 'file2')))

    def testFetchOrUpdate_fetch(self):
        """testFetchOrUpdate_fetch"""
        svn = scm.SvnFetcher()
        svn.fetch_or_update(opts['wc'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['wc'], 'file2')))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'], '.svn')))

    def testFetchOrUpdate_update(self):
        """testFetchOrUpdate_update"""
        svn = scm.SvnFetcher()
        svn.fetch(opts['wc'], 'file://%s' % opts['path'], dict(revision=1))
        self.assertTrue(os.path.isdir('%s/%s' % (opts['wc'], '.svn')))
        self.assertFalse(os.path.isfile('%s/%s' % (opts['wc'], 'file2')))
        svn.fetch_or_update(opts['wc'], 'file://%s' % opts['path'])
        self.assertTrue(os.path.isfile('%s/%s' % (opts['wc'], 'file2')))

def test_suite():
    suite = unittest.TestSuite()
    #suite.addTest(unittest.makeSuite(testBzr))
    #suite.addTest(unittest.makeSuite(testHg))
    #suite.addTest(unittest.makeSuite(testSvn))
    #suite.addTest(unittest.makeSuite(testGit))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(test_suite())

# vim:set et sts=4 ts=4 tw=80:
