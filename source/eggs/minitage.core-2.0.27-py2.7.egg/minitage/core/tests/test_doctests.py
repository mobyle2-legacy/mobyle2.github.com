"""
Generic Test case
"""
__docformat__ = 'restructuredtext'

import unittest
import doctest
import sys
import os
import tempfile
import shutil
import subprocess
from os import makedirs as mkdir
from shutil import copy
import logging
from distutils.dir_util import copy_tree


logging.basicConfig()
import minitage.core.tests
current_dir =  minitage.core.tests.__path__[0]

def rmdir(*args):
    dirname = os.path.join(*args)
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)

def sh(cmd, in_data=None):
    _cmd = cmd
    print cmd
    p = subprocess.Popen([_cmd], shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, close_fds=True)

    if in_data is not None:
        p.stdin.write(in_data)

    p.stdin.close()

    print p.stdout.read()

def ls(*args):
    dirname = os.path.join(*args)
    if os.path.isdir(dirname):
        filenames = os.listdir(dirname)
        for filename in sorted(filenames):
            print filename
    else:
        print 'No directory named %s' % dirname

def cd(*args):
    dirname = os.path.join(*args)
    os.chdir(dirname)

def config(filename):
    return os.path.join(current_dir, filename)


def cat(*args, **kwargs):
    filename = os.path.join(*args)
    if os.path.isfile(filename):
        data = open(filename).read()
        if kwargs.get('returndata', False):
           return data
        print data
    else:
        print 'No file named %s' % filename

def touch(*args, **kwargs):
    filename = os.path.join(*args)
    open(filename, 'w').write(kwargs.get('data',''))


#execdir = os.path.abspath(os.path.dirname(sys.executable))
tempdir = os.getenv('TEMP','/tmp')

class DoctestLayer(object):
    """"""

def default_setUp(test):
    globs = test.globs
    for p in [globs['p'],
              globs['p2'],
              globs['p3'],
              globs['wc'],]:
        if os.path.exists(p):
            shutil.rmtree(p)
        os.makedirs(p)

def default_tearDown(test):
    globs = test.globs
    if os.path.exists(globs['p']):
        shutil.rmtree(globs['p3'])
        shutil.rmtree(globs['p2'])
        shutil.rmtree(globs['wc'])

def doc_suite(test_dir, setUp=None, tearDown=None, globs=None):
    """Returns a test suite, based on doctests found in /doctest."""
    suite = []
    tmpdir = tempfile.mkdtemp()
    if globs is None:
        globs = globals()
        globs['p'] = tmpdir
        globs['path2'] = globs['p2'] = os.path.join(tmpdir, 'p2')
        globs['path3'] = globs['p3'] = os.path.join(tmpdir, 'p3')
        globs['wc'] = os.path.join(tmpdir, 'wc')

    flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE |
             doctest.REPORT_ONLY_FIRST_FAILURE)

    doctest_dir = test_dir

    # filtering files on extension
    docs = [os.path.join(doctest_dir, doc) for doc in
            os.listdir(doctest_dir) if doc.endswith('.txt')
           # if [selectable
           #     for selectable in ['bzr','hg', 'git']
           #     if selectable in doc]
           ]

    if not setUp:
        setUp = default_setUp

    if not tearDown:
        tearDown = default_tearDown

    for ftest in docs:
        test = doctest.DocFileSuite(
            ftest, optionflags=flags,
            globs=globs, setUp=setUp,
            tearDown=tearDown,
            module_relative=False
        )
        test.layer = DoctestLayer
        suite.append(test)

    return unittest.TestSuite(suite)

def test_suite():
    """returns the test suite"""
    return doc_suite(current_dir)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(test_suite()) 

