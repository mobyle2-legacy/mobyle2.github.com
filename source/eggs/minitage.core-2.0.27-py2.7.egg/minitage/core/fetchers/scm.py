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

import os
import subprocess
import re
import datetime
import logging
from distutils.dir_util import copy_tree

from minitage.core.fetchers import interfaces

__logger__ = 'minitage.fetchers.scm'

class OfflineModeRestrictionError(interfaces.IFetcherError):
    """Restriction error in offline mode."""

class HgFetcher(interfaces.IFetcher):
    """ Mercurial Fetcher.
    Example::
        >>> import minitage.core.fetchers.scm
        >>> hg = scm.HgFetcher()
        >>> hg.fetch_or_update('http://uri','/dir',{revision='tip'})
    """

    def __init__(self, config = None):
        self.config =  config
        interfaces.IFetcher.__init__(self, 'Mercurial', 'hg', config, '.hg', 'tip')
        self.log = logging.getLogger(__logger__)

    def checkout(self, dest, uri, opts, verbose=True):
        args = opts.get('args', '')
        if not verbose:
            args += ' -q '
        self._scm_cmd('clone %s %s %s' % (args, uri, dest), verbose)

    def update_wc(self, dest, uri, opts, verbose=True):
        if not uri:
            uri = ''
        args = opts.get('args', '')
        vargs = ''
        if not verbose:
            vargs += ' -q '
        self._scm_cmd('pull %s -f %s %s -R %s' % (vargs, uri, args, dest), verbose)

    def goto_revision(self, dest, uri, opts, verbose=True):
        args = opts.get('goto-revision-args', '')
        if not verbose:
            args += ' -q '
        if 'revision' in opts:
            args += '-C -r%s' % opts['revision']
        self._scm_cmd('up %s -R %s' % (args, dest), verbose)

    def is_valid_src_uri(self, uri):
        """See interface."""
        match = interfaces.URI_REGEX.match(uri)
        if match \
           and (match.groups()[2] in ['file', 'hg', 'ssh', 'http', 'https', '/']
                or match.groups()[0] == '/'):
            return True
        return False

    def match(self, switch):
        """See interface."""
        if switch == 'hg':
            return True
        return False

    def get_uri(self, dest):
        """get Mercurial url"""
        self._check_scm_presence()
        try:
            cwd = os.getcwd()
            os.chdir(dest)
            self.log.debug('Running %s %s in %s' % (
                self.executable,
                'showconfig |grep paths.default',
                dest
            ))
            process = subprocess.Popen(
                '%s %s' % (
                    self.executable,
                    'showconfig |grep paths.default'
                ),
                shell = True, stdout=subprocess.PIPE
            )
            ret = process.wait()
            if ret != 0:
                message = '%s failed to achieve correctly.' % self.name
                raise interfaces.FetcherRuntimeError(message)
            dest_uri = re.sub('([^=]*=)\s*(.*)',
                          '\\2',
                          process.stdout.read().strip()
                         )
            os.chdir(cwd)
            return dest_uri
        except Exception, instance:
            os.chdir(cwd)
            raise instance

    def _has_uri_changed(self, dest, uri):
        """See interface."""
        # file is removed on the local uris
        uri = uri.replace('file://', '')
        # in case we were not hg before
        if not os.path.isdir(os.path.join(dest, self.metadata_directory)):
            return True
        if self.warn_trailing_slash(dest, uri):
            return False
        if uri != self.get_uri(dest):
            return True
        return False


class SvnFetcher(interfaces.IFetcher):
    """Subversion Fetcher.
    Example::
        >>> import minitage.core.fetchers.scm
        >>> svn = scm.SvnFetcher()
        >>> svn.fetch_or_update('http://uri','/dir',{revision='HEAD'})
    """

    def __init__(self, config = None):
        self.config =  config
        interfaces.IFetcher.__init__(self, 'subversion', 'svn', config, '.svn',
                                    'HEAD')
        self.log = logging.getLogger(__logger__)

    def checkout(self, dest, uri, opts, verbose=True):
        args = opts.get('args', '')
        if not verbose:
            args += ' -q '
        args = '%s %s' % (args, opts.get('goto-revision-args', ''))
        if 'revision' in opts:
            args += '-r %s' % opts['revision']
        self._scm_cmd('co %s %s %s' % (args, uri, dest), verbose=True)

    def update_wc(self, dest, uri, opts, verbose=True):
        args = opts.get('args', '')
        if not verbose:
            args += ' -q '
        args = '%s %s' % (args, opts.get('goto-revision-args', ''))
        if 'revision' in opts:
            args += '-r %s' % opts['revision']
        self._scm_cmd('up %s %s' % (args, dest), verbose)

    def goto_revision(self, dest, uri, opts, verbose,  passive = True):
        if not passive:
            self.update_wc(dest, uri, opts, verbose)

    def is_valid_src_uri(self, uri):
        """See interface."""
        match = interfaces.URI_REGEX.match(uri)
        if match \
           and match.groups()[2] \
           in ['file', 'svn', 'svn+ssh', 'http', 'https']:
            return True
        return False

    def match(self, switch):
        """See interface."""
        if switch == 'svn':
            return True
        return False

    def get_uri(self, dest):
        """Get url."""
        self._check_scm_presence()
        process = subprocess.Popen(
            '%s %s' % (
                self.executable,
                'info %s|grep -i url' % dest
            ),
            shell = True, stdout=subprocess.PIPE
        )
        ret = process.wait()
        # we werent svn
        if ret != 0:
            return None
        return re.sub(
            '([^:]*:)\s*(.*)', '\\2',
            process.stdout.read().strip()
        )

    def _has_uri_changed(self, dest, uri):
        """See interface."""
        if self.warn_trailing_slash(dest, uri):
            return False
        if uri != self.get_uri(dest):
            return True
        return False

class BzrFetcher(interfaces.IFetcher):
    """ Bazaar Fetcher.
    Example::
        >>> import minitage.core.fetchers.scm
        >>> bzr = scm.BzrFetcher()
        >>> bzr.fetch_or_update('http://uri','/dir',{revision='last:1'})
    """

    def __init__(self, config = None):
        self.config =  config
        interfaces.IFetcher.__init__(self, 'bazaar', 'bzr', config, '.bzr',
                                     'last:1')
        self.log = logging.getLogger(__logger__)

    def checkout(self, dest, uri, opts, verbose=True):
        args = opts.get('args', '')
        if not verbose:
            args += ' -q '
        self._scm_cmd('checkout %s %s %s' % (args, uri, dest), verbose)

    def update_wc(self, dest, uri, opts, verbose=True):
        args = opts.get('args', '')
        if not uri:
            uri = ''
        if not verbose:
            args += ' -q '
        self._scm_cmd('pull %s %s -d %s' % (args, uri, dest), verbose)

    def goto_revision(self, dest, uri, opts, verbose=True):
        args = opts.get('goto-revision-args', '')
        if not verbose:
            args += ' -q '
        if 'revision' in opts:
            args += '--overwrite -r%s' % opts['revision']
            self._scm_cmd('pull %s %s -d %s' % (
                args, uri, dest), verbose
            )

    def is_valid_src_uri(self, uri):
        """See interface."""
        match = interfaces.URI_REGEX.match(uri)
        bzrmatch = re.compile('[a-zA-Z1-9]*:(.*)').match(uri)
        if match \
           and match.groups()[2] \
           in ['file', 'bzr', 'sftp', 'http',
               'https', 'bzr+http', 'bzr+https',
               'bzr+ssh', 'svn+file',
               'svn', 'svn+http', 'svn+https'] or bzrmatch:
            return True
        return False

    def match(self, switch):
        """See interface."""
        if switch == 'bzr':
            return True
        return False

    def get_uri(self, dest):
        """get bazaar url"""
        self._check_scm_presence()
        try:
            cwd = os.getcwd()
            os.chdir(dest)
            self.log.debug('Running %s %s in %s' % (
                self.executable,
                ' info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3',
                dest
            ))
            process = subprocess.Popen(
                '%s %s' % (
                    self.executable,
                    ' info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3',
                ),
                shell = True, stdout=subprocess.PIPE
            )
            ret = process.wait()
            if ret != 0:
                message = '%s failed to achieve correctly.' % self.name
                raise interfaces.FetcherRuntimeError(message)
            dest_uri = re.sub(
                '([^=]*=)\s*(.*)',
                '\\2',
                process.stdout.read().strip()
            )
            if '\n' in dest_uri:
                # return 'checkout branch'
                dest_uri = dest_uri.split('\n')[0]
            os.chdir(cwd)
            return dest_uri
        except Exception, instance:
            os.chdir(cwd)
            raise instance

    def _has_uri_changed(self, dest, uri):
        """See interface."""
        # file is removed on the local uris
        uri = uri.replace('file://', '')
        repouri = self.get_uri(dest).replace('file://', '')
        # in case we were not bzr before
        if not os.path.isdir(os.path.join(dest, self.metadata_directory)):
            return True
        if self.warn_trailing_slash(dest, uri):
            return False
        if uri != repouri:
            return True
        return False

class GitFetcher(interfaces.IFetcher):
    """ Bazaar Fetcher.
    Example::
        >>> import minitage.core.fetchers.scm
        >>> git = scm.GitFetcher()
        >>> git.fetch_or_update('http://uri','/dir',{revision='HEAD'})
    """

    def __init__(self, config = None):
        self.config =  config
        interfaces.IFetcher.__init__(self, 'git', 'git', config, '.git', 'HEAD')
        self.log = logging.getLogger(__logger__)

    def checkout(self, dest, uri, opts, verbose=True):
        args = opts.get('args', '')
        if not verbose:
            args += ' -q '
        self._scm_cmd('clone  %s %s %s' % (args, uri, dest), verbose)

    def update_wc(self, dest, uri, opts, verbose=True):
        args = opts.get('args', '')
        if not verbose:
            args += ' -q '
        cwd = os.getcwd()
        os.chdir(dest)
        if not uri or (not self._has_uri_changed(dest, uri)):
            uri = ''
        try:
            self._scm_cmd('pull %s %s' % (args, uri), verbose)
        except Exception, e:
            os.chdir(cwd)
        os.chdir(cwd)

    def goto_revision(self, dest, uri, opts, verbose=True):
        args = opts.get('goto-revision-args', '')
        if not verbose:
            args += ' -q '
        if 'revision' in opts:
            cwd = os.getcwd()
            os.chdir(dest)
            self._scm_cmd(
                'reset %s --hard %s' % (
                    args,
                    opts['revision'],
                ),
                verbose
            )
            os.chdir(cwd)

    def is_valid_src_uri(self, uri):
        """See interface."""
        match = interfaces.URI_REGEX.match(uri)
        gitmatch = re.compile('[a-zA-Z1-9]*:(.*)').match(uri)
        if match \
           and match.groups()[2] \
           in ['file', 'git', 'rsync', 'http',
               'https', 'svn'] or gitmatch:
            return True
        return False

    def match(self, switch):
        """See interface."""
        if switch == 'git':
            return True
        return False


    def get_uri(self, dest):
        """get git url"""
        self._check_scm_presence()
        try:
            cwd = os.getcwd()
            os.chdir(dest)
            self.log.debug('Running %s %s in %s' % (
                self.executable,
                'config --get remote.origin.url',
                dest
            ))
            process = subprocess.Popen('%s config --get remote.origin.url' % self.executable,
                                       shell = True, stdout=subprocess.PIPE)
            ret = process.wait()
            if ret >1 :
                message = '%s failed to achieve correctly.' % self.name
                raise interfaces.FetcherRuntimeError(message)
            dest_uri = process.stdout.read().strip()
            os.chdir(cwd)
            return dest_uri
        except Exception, instance:
            os.chdir(cwd)
            raise instance

    def _has_uri_changed(self, dest, uri):
        """See interface."""
        # in case we were not git before
        if not os.path.isdir(os.path.join(dest, self.metadata_directory)):
            return True
        if self.warn_trailing_slash(dest, uri):
            return False
        if uri != self.get_uri(dest):
            return True
        return False

# vim:set et sts=4 ts=4 tw=80:
