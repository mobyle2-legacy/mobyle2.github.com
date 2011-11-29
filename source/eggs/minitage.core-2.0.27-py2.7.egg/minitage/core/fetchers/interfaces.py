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

import re
import os
import shutil
import logging
import datetime
from distutils.dir_util import copy_tree

from minitage.core import interfaces
import minitage.core.common

class IFetcherError(Exception):
    """General Fetcher Error."""


class InvalidUrlError(IFetcherError):
    """Invalid url."""


class UpdateError(IFetcherError):
    """Update Error."""


class FetchError(IFetcherError):
    """Fetch Error."""


class InvalidRepositoryError(IFetcherError):
    """Repository is invalid."""


class FetcherNotInPathError(IFetcherError):
    """Fetcher was not found."""


class FetcherRuntimeError(IFetcherError):
    """Unknown runtime Error."""

dscms = 'git|hg|bzr|mtn'
p = 'ssh|http|https|ftp|sftp|file'
scms = 'svn|svn\+ssh|cvs'
URI_REGEX = re.compile('^(\/|((%s|%s|%s)(:\/\/)))' % (dscms, p , scms))
__logger__ = 'minitage.interfaces'

def copy_move_tree(src, dest):
    if not os.path.exists(dest):
        os.makedirs(dest)
    for f in os.listdir(src):
        fp = os.path.join(src,  f)
        dp = os.path.join(dest, f)
        if os.path.exists(dp):
            minitage.core.common.remove_path(dp)
        os.rename(fp, dp)
    minitage.core.common.remove_path(src)

class IFetcherFactory(interfaces.IFactory):
    """Interface Factory."""

    def __init__(self, config=None):
        """
        Arguments:
            - config: a configuration file with a self.name section
                    containing all needed classes.
        """

        interfaces.IFactory.__init__(self, 'fetchers', config)
        self.registerDict(
            {
                'hg': 'minitage.core.fetchers:HgFetcher',
                'bzr': 'minitage.core.fetchers:BzrFetcher',
                'git': 'minitage.core.fetchers:GitFetcher',
                'svn': 'minitage.core.fetchers:SvnFetcher',
                'static': 'minitage.core.fetchers:StaticFetcher',
            }
        )

    def __call__(self, switch):
        """return a fetcher
        Arguments:
            - switch: fetcher type
              Default ones:

                -hg: mercurial
                -svn: subversion
        """
        for key in self.products:
            klass = self.products[key]
            instance = klass(config = self.sections)
            if instance.match(switch):
                return instance

class IFetcher(interfaces.IProduct):
    """Interface for fetching a package from somewhere.
    Basics
         To register a new fetcher to the factory you ll have 2 choices:
             - Indicate something in a config.ini file and give it to the
               instance initialization.
               Example::
                   [fetchers]
                   type=mymodule.mysubmodule.MyFetcherClass

             - register it manually with the .. function::register
               Example::
                   >>> klass = getattr(module,'superklass')
                   >>> factory.register('svn', klass)
    What a fetcher needs to be a fetcher
        Locally, the methods in the interfaces ;)
        Basically, it must implement
            - match: select the fetcher
            - checkout, update_wc, goto_revision get/update the source
            - is_valid_src_uri to know if the src url is good
            - _has_uri_changed to know if we get the source from the last repo
              we got from or a new one.
    """

    def __init__(self,
                 name,
                 executable = None ,
                 config = None,
                 metadata_directory = None,
                 default_revision = 'HEAD',):
        """
        Attributes:
            - name : name of the fetcher
            - executable : path to the executable. Either absolute or local.
            - metadata_directory: optionnal, the metadata directory for the scm
        """
        interfaces.IProduct.__init__(self)
        self.name = name
        self.executable = None
        self.metadata_directory = metadata_directory
        if not config:
            config = {}
        self.config = config
        self.executable = executable
        self._scm_found = None
        self.default_revision = default_revision
        mconfig = config.get('minimerge', {})
        self._proxies = {
            'http_proxy': mconfig.get('http_proxy', None),
            'https_proxy': mconfig.get('https_proxy', None),
            'ftp_proxy': mconfig.get('ftp_proxy', None),
        }
        for proxy_type in self._proxies:
            if self._proxies[proxy_type]:
                os.environ[proxy_type] = self._proxies[proxy_type]

    def update(self, dest, uri, opts=None, verbose=False):
        """
        Update a package.
        Arguments:
            - uri : check out/update uri
            - opts : arguments for the fetcher

                - revision: particular revision to deal with.
                - args: misc arguments to give to the underlying program
                - goto-revision-args: misc arguments to give to udpate to a specified version
        """
        self.log.debug('Updating %s / %s' % (dest, uri))
        if not opts:
            opts = {}
        try:
            self.check_valid_co(dest, uri)
        except:
            self.log.warning(
                'The working copy seems not to be a %s '
                'repository. Getting a new working copy.' % self.name
            )
            self.fetch(dest, uri, opts, verbose)
        if uri and self._has_uri_changed(dest, uri):
            self.log.warning('Url has changed, '
                             'archiving and getting '
                             'a new working copy.'
            )
            self.fetch(dest, uri, opts, verbose)
        else:
            self.update_wc(dest, uri, opts, verbose)
            self.goto_revision(dest, uri, opts, verbose)
            self.log.info(
                'Updated %s / %s (%s) [%s].' % (
                    dest,
                    uri,
                    opts.get('revision',
                             self.default_revision),
                    self.name
                )
            )
        self.check_valid_co(dest, uri)

    def fetch(self, dest, uri, opts=None, verbose=False):
        """Fetch a package.
        Arguments:
            - uri : check out/update uri
            - dest: destination to fetch to
            - opts : arguments for the fetcher

                - revision: particular revision to deal with.
                - args: misc arguments to give to the underlying program
                - goto-revision-args: misc arguments to give to udpate to a specified version
        """
        if opts is None:
            opts = {}
        # checkout somewhere else if we have conflicts
        checkout_dest = dest
        destination_empty = False
        if os.path.exists(dest):
            if self.archive_previous_co(dest):
                checkout_dest = os.path.join(checkout_dest, '%s-tmp' % self.name)
            if len(os.listdir(dest)) == 0:
                destination_empty = True
                checkout_dest = os.path.join(checkout_dest, '%s-tmp' % self.name)
        if self.is_valid_src_uri(uri):
            self.checkout(checkout_dest, uri, opts, verbose)
            if checkout_dest != dest:
                if not destination_empty:
                    self.log.warning(
                        'Checkout directory is not the same as the '
                        'destination, copying content to it. This may '
                        'happen when you say to download to somwhere '
                        'where it exists files before doing the '
                        'checkout'
                    )
                copy_move_tree(checkout_dest, dest)
            self.goto_revision(dest, uri, opts, verbose)
            self.log.info(
                'Checkouted %s / %s (%s) [%s].' % (
                    dest,
                    uri,
                    opts.get('revision',
                             self.default_revision),
                    self.name
                )
            )
        else:
            raise interfaces.InvalidUrlError('this uri \'%s\' is invalid' % uri)
        self.check_valid_co(dest, uri)

    def fetch_or_update(self, dest, uri, opts = None, verbose=False):
        """Fetch or update a package (call the one of those 2 methods).
        Arguments:
            - uri : check out/update uri
            - opts : arguments for the fetcher
            - verbose: set to True to be verbose
        """
        if os.path.isdir(os.path.join(dest, self.metadata_directory)):
            self.update(dest, uri, opts, verbose)
        else:
            self.fetch(dest, uri, opts, verbose)

    def check_valid_co(self, dest, uri):
        """
        Check if the final directory is a checkouted copy of url.
        """
        if not os.path.isdir(
            os.path.join(dest, self.metadata_directory)
        ):
            message = '%s' % (
                'Unexpected fetch error on \'%s\'\n'
                'The directory \'%s\' is not '
                'a valid %s repository' % (uri, dest, self.name)
            )
            raise InvalidRepositoryError(message)

    def _check_scm_presence(self):
        """check if the scm is in he path"""
        for path in os.environ.get('PATH', '').split(':'):
            exe = os.path.join(path, self.executable)
            if os.path.exists(exe):
                self._scm_found = True
                break

        if not getattr(self, '_scm_found', False):
            message = '%s is not in your path, ' % self.executable
            message += 'please install it or maybe get it into your PATH'
            raise FetcherNotInPathError(message)

    def _scm_cmd(self, command, verbose=False):
        """Helper to run scm commands."""
        self._check_scm_presence()
        logging.getLogger(__logger__).debug(
            'Running %s %s ' % (self.executable, command))
        try:
            minitage.core.common.Popen('%s %s' % (self.executable, command), verbose)
        except Exception, e:
            raise FetcherRuntimeError('%s' % e)

    def _remove_versionned_directories(self, dest):
        """Remove all directories which contains history.
        part is a special directory, that s where we make install, we will not remove it !
        Arguments
            - dest the working copy
        """
        not_versionned = ['part']
        for filep in os.listdir(dest):
            if not filep in not_versionned:
                path = os.path.join(dest, filep)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

    def warn_trailing_slash(self, dest, uri):
        """Check if the url jhave a trailing slash."""
        if uri == '%s/' % self.get_uri(dest):
            self.log.warning(
                'It seems that the url given do not need the trailing slash (%s). '
                'You would have better not to keep trailing slash in your urls '
                'if you don\'t have to.' % uri)
            return True
        return False

    def archive_previous_co(self, dest):
        """
        Return True if archived
        False otherwise
        """
        if os.path.isdir(dest):
            if len(os.listdir(dest)) != 0:
                oldpath = os.path.join(
                    dest,
                    '%s.old.%s' % (
                        os.path.basename(dest),
                        datetime.datetime.now().strftime( '%d%m%y%H%M%S')
                    )
                )
                boldpath = os.path.basename(oldpath)
                self.log.warning(
                    'Destination %s already exists and is not empty, '
                    'moving it away in %s for further user '
                    'examination' % (dest, oldpath)
                )
                if not os.path.isdir(oldpath):
                    os.makedirs(oldpath)
                    for p, porig, pdest in [(p,
                                             os.path.join(dest, p),
                                             os.path.join(oldpath, p))
                                             for p in os.listdir(dest)
                                             if not p == boldpath]:
                        if os.path.exists(pdest):
                            minitage.core.common.remove_path(pdest)
                        os.rename(porig, pdest)
                return True
        return False

#
# TO IMPLEMENT IN FETCHERS
#

    def checkout(self, dest, uri, ops=None, verbose=False):
        """
        Checkout an url to a working copy.
        """
        raise NotImplementedError('The method is not implemented')

    def update_wc(self, dest, uri, ops=None, verbose=False):
        """
        Really update the working copy.
        """
        raise NotImplementedError('The method is not implemented')

    def goto_revision(self, dest, uri, ops=None, verbose=False):
        """
        Go to a particular revision.
        """
        raise NotImplementedError('The method is not implemented')

    def is_valid_src_uri(self, uri):
        """Valid an uri.
        Return:
            boolean if the uri is valid or not
        """
        raise NotImplementedError('The method is not implemented')

    def _has_uri_changed(self, dest, uri):
        """Does the uri we fetch from in the working changed or not.
        Arguments
            - dest the working copy
            - uri the uri to fetch from
        Return
            - True if the uri in the working copy changed
        """
        raise NotImplementedError('The method is not implemented')

    def match(self, switch):
        """Test if the switch match the module."""
        raise NotImplementedError('The method is not implemented')

# vim:set et sts=4 ts=4 tw=80:
