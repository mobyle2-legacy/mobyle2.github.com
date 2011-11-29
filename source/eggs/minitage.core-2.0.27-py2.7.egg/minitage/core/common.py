#!/usr/bin/env python

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

import logging
try:
    from hashlib import md5
except:
    from md5 import new as md5
import os
import re
import sys
import shutil
import tempfile
import urllib2
import urlparse
import subprocess


from distutils.dir_util import copy_tree

from setuptools.package_index import PackageIndex
from pkg_resources import Requirement, resource_filename
from minitage.core.version import __version__
letter_re = re.compile('^((?P<letter>[a-zA-Z]):)(?P<path>.*)', re.U|re.S|re.I)

def newline(fic):
    "keep just one new line at the end of the config!"""
    lines = open(fic).readlines()
    lines.reverse()
    res = []
    if lines:
        begin = False
        for line in lines:
            if line.strip() != '':
                begin = True
            if begin:
                res.append(line)
    res.reverse()
    res.append('\n')
    rfic = open(fic, 'w')
    for line in res:
        if not line.endswith('\n'):
            line = '%s\n' % line
        rfic.write(line)
    rfic.flush()
    rfic.close()

class MinimergeError(Exception): pass

def splitstrip(l, token=None):
    """Split a list and return non stripped elements."""
    return [elem \
            for elem in l.split(token) \
            if elem.strip()]

def md5sum(filep):
    """Return the md5 sium of a file"""
    fobj = filep
    if isinstance(filep, basestring):
        fobj = open(filep,'rb')
    m = md5()
    while True:
        d = fobj.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()

def test_md5(filep, md5sum_ref):
    """Test if file match md5 md5sum."""
    if md5sum(filep) == md5sum_ref:
        return True

    return False


def remove_path(path):
    """Remove a path."""
    if os.path.exists(path):
        if os.path.islink(path):
            os.unlink(path) 
        elif os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    else:
        print
        print "'%s' was asked to be deleted but does not exists." % path
        print


def append_env_var(env, var, sep=":", before=True):
    """Append text to a environnement variable.
    @param env String variable to set
    @param before append before or after the variable
    """
    for path in var:
        if before:
            os.environ[env] = "%s%s%s" % (
                path, sep, os.environ.get(env, '')
            )
        else:
            os.environ[env] = "%s%s%s" % (
                os.environ.get(env, ''), sep, path
            )

def substitute(filename, search_re, replacement):
    """Substitutes text within the contents of ``filename`` matching
    ``search_re`` with ``replacement``.
    """
    search = re.compile(search_re, re.MULTILINE)
    text = open(filename).read()
    text = replacement.join(search.split(text))
    newfilename = '%s%s' % (filename, '.~new')
    newfile = open(newfilename, 'w')
    newfile.write(text)
    newfile.close()
    shutil.copymode(filename, newfilename)
    shutil.move(newfilename, filename)

def system(c, log=None):
    """Execute a command."""
    if log:
        log.debug("Running %s" % c)
    ret = os.system(c)
    if ret:
        raise SystemError('Failed', c)
    return ret

def is_local_url(url):
    if ('file://' in url
        or url.startswith('./')
        or url.startswith('/')
        or ('localhost' in url
                or '127.0.0.1' in url
                or '::1' in url)
       ):
        return True
    return False

def Popen(command, verbose=False):
    # FIXME: Popen strange behaviour
    ret = os.system(command)
    #stdout = None
    #if not verbose:
    #    stdout = subprocess.PIPE
    # p = subprocess.Popen(command,
    #                      shell=True,
    #                      stdin=subprocess.PIPE,
    #                      stdout = stdout,
    #                      stderr=subprocess.PIPE,
    #                     )
    # ret = p.wait()
    if ret != 0:
        error = ''
        #if not verbose:
        #    error = p.stdout.read()
        message = '%s\n%s' % (error,
                            '----------------------------------------------------------\n'
                            '\'%s\' failed!\n'
                            '\tPlease report all the above backtrace along\n'
                            '\t with your bug report.\n'
                            '----------------------------------------------------------\n' % (command)
                           )
        raise MinimergeError(message)

def get_from_cache(url,
                   download_cache = None,
                   logger = None,
                   file_md5 = None,
                   offline = False,
                   use_cache = True):
    """Get a file from the buildout download cache.
    Arguments:
        - url : where to fetch from
        - name: filename destination
        - download_cache: path to the dl cache
        - install_from_cache:
        - offline : offline mode
    """
    # borrowed from zc.recipe.cmmi
    if download_cache:
        if not os.path.isdir(download_cache):
            os.makedirs(download_cache)

    _, _, urlpath, _, fragment = urlparse.urlsplit(url)
    if not fragment:
        fragment = ''
    md5_re = re.compile('md5[^=]*=(.*)', re.S|re.U)
    md5_re_match = md5_re.match(fragment)
    if not file_md5 and md5_re_match:
        file_md5 = md5_re_match.groups()[0]
    filename = urlpath.split('/')[-1]
    if '\\' in filename and (sys.platform.startswith('cyg') or
                            sys.platform.startswith('win')):
        filename = os.path.basename(filename)
#    if not logger:
#        logger = logging.getLogger(filename)

    # get the file from the right place
    fname = tmp2 = file_present = ''
    if download_cache:
        # if we have a cache, try and use it
        if logger:
            logger.debug(
                'Searching cache at %s' % download_cache)
        if os.path.isdir(download_cache):
            # just cache files for now
            fname = os.path.join(download_cache, filename)

    # do not download if we have the file
    file_present = os.path.exists(fname)
    if file_present:
        if file_md5:
            if not test_md5(fname, file_md5):
                file_present = False
                bad_md5, backup = md5sum(fname), make_backup(fname)
                if logger:
                    logger.warning(
                        'MD5SUM mismatch for %s: Good:%s != Bad:%s\n'
                        'Backuping the old file but re download it!\n'
                        'A bakcup will be made in %s.'% (
                            fname,
                            file_md5,
                            bad_md5,
                            backup
                        )
                    )
        if file_present:
            if logger:
                logger.debug(
                    'Using cache file in %s' % fname
                )
    else:
        if logger:
            logger.debug(
                'Did not find %s under cache: %s' % (
                    filename,
                    download_cache)
            )

    # force re download if we do not want to use cache unless we are offline
    # or patch is a local file
    if not use_cache and not offline:
        file_present = False

    if os.path.exists(url):
        url = 'file://%s' % os.path.abspath(url)

    if not file_present:
        # static local files
        if offline and not is_local_url(url):
            # no file in the cache, but we are staying offline
            raise MinimergeError(
                "Offline mode: file from %s not found in the cache at %s" %
                (url, download_cache)
            )
        try:
            # okay, we've got to download now
            tmp2 = None
            if download_cache:
                # set up the cache and download into it
                fname = os.path.join(download_cache, filename)
                if logger:
                    logger.debug(
                        'Cache download %s as %s' % (
                            url,
                            download_cache)
                    )
            else:
                # use tempfile
                tmp2 = tempfile.mkdtemp('buildout-' + filename)
                fname = os.path.join(tmp2, filename)
            if logger:
                logger.info(
                    'Downloading %s in %s' % (url,fname)
                )

            local_file = '/not/existing/file/or/directory'
            if 'file://' in url:
                local_file = url.replace('file://', '')
                if sys.platform.startswith('win') or sys.platform.startswith('cyg'):
                    tpath = url.replace('file://', '')
                    if letter_re.match(tpath):
                        url = url.replace('file://', 'file:///')
            if os.path.isdir(local_file):
                copy_tree(local_file, fname)
            if (not os.path.exists(fname)) or use_cache == False:
                # we try to download the url with fragments, if it fails,
                # without.
                dfd = open(fname,'wb')
                try:
                    pi = PackageIndex()
                    pi._attempt_download(url, fname)
                except:
                    url, info = url.split('#', 1)
                    if 'md5' in fragment:
                        dfd.write(urlopen(url).read())
                    else:
                        raise
                dfd.flush()
                dfd.close()
            if file_md5:
                if not test_md5(fname, file_md5):
                    raise MinimergeError(
                        'MD5SUM mismatch for %s: Good:%s != Bad:%s' % (
                            fname,
                            file_md5,
                            md5sum(fname)
                        )
                    )

        except Exception, e:
            if tmp2 is not None:
                shutil.rmtree(tmp2)
            msg = 'Failed download for %s:\t%s' % (url, e)
            if download_cache:
                msg += '\nBackup of the downloaded file has been made in %s' % make_backup(fname)
            raise MinimergeError(msg)

    return fname

def make_backup(fname):
    index = 0
    backup = ''
    while os.path.exists(fname):
        backup = '%s.md5sum_mismatch.%s' % (fname, index)
        try:
            if not os.path.exists(backup):
                os.rename(fname, backup)
            else:
                index += 1
        except:
            index += 1
    return backup

def first_run():
    ## first time create default config !
    prefix = os.path.abspath(sys.exec_prefix)
    config = os.path.join(prefix, 'etc', 'minimerge.cfg')
    mm_version = __version__
    if not os.path.isfile(config):
        print """\n\n
====================================================
\t\tWELCOME TO THE MINITAGE WORLD
====================================================

You seem to be running minitage for the first time.

\t* Creating some default stuff...
\t* Generating default config: %s """ % config
        print '\t* Creating minilays dir'
        for dir in (os.path.split(config)[0],
                    os.path.join(sys.exec_prefix, 'minilays'),
                    os.path.join(sys.exec_prefix, 'logs'),
                    os.path.join(sys.exec_prefix, 'eggs', 'cache'),
                    os.path.join(sys.exec_prefix, 'cpan', '5.8'),
                    os.path.join(sys.exec_prefix, 'eggs', 'develop-cache'),
                   ):
            if not os.path.isdir(dir):
                os.makedirs(dir)
        tconfig = resource_filename(Requirement.parse(
            'minitage.core == %s' % mm_version),
            'etc/minimerge.cfg')
        changelog= resource_filename(Requirement.parse(
            'minitage.core == %s' % mm_version),
            'share/minitage/CHANGES.txt')
        readme= resource_filename(Requirement.parse(
            'minitage.core == %s' % mm_version),
            'share/minitage/README.txt')
        prefixed = re.sub('%PREFIX%',prefix, open(tconfig,'r').read())
        fic = open(config, 'w')
        fic.write(prefixed)
        fic.flush()
        fic.close()
        print '\n\n'


def which(program, environ=None, key = 'PATH', split = ':'):
    if not environ:
        environ = os.environ
    PATH=environ.get(key, '').split(split)
    for entry in PATH:
        fp = os.path.abspath(os.path.join(entry, program))
        if os.path.exists(fp):
            return fp
        if (sys.platform.startswith('win') or sys.platform.startswith('cyg'))  and os.path.exists(fp+'.exe'):
            return fp+'.exe'
    raise IOError('Program not fond: %s in %s ' % (program, PATH))

class MinibuildNotFoundException(Exception):pass
def search_latest(regex, minilays):
    for mpath, directories, files in os.walk(minilays):
        subpath = mpath.replace(
            os.path.commonprefix([minilays, mpath]),
            '')
        if subpath and (not subpath.count(os.path.sep) > 1):
            files.sort()
            files.reverse()
            for minibuild in files:
                if not minibuild.startswith('.'):
                    if re.match(regex, minibuild, re.M|re.S|re.U):
                        return minibuild
    raise MinibuildNotFoundException('Regex %s didnt match or '
                    'minibuild not found in %s.' % (regex, minilays))

GENTOO_FF_UA = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090912 Gentoo Shiretoko/3.5.3'
def urlopen(uri, ua = GENTOO_FF_UA, *args, **kwargs):
    """Fake user agent to prevent some basic sysadmins
    restrictrions."""
    request = urllib2.Request(uri)
    request.add_header('User-Agent', ua)
    opener = urllib2.build_opener()
    urlo = opener.open(request)
    return urlo

# vim:set et sts=4 ts=4 tw=80:
