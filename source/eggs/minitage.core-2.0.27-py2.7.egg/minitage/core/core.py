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
import sys
import ConfigParser
import datetime
import logging
import logging.config
import random
import copy
import re
import shutil
from cStringIO import StringIO
from distutils.dir_util import copy_tree
import pkg_resources
import subprocess

from iniparse import ConfigParser as WritableConfigParser

from minitage.core import objects
from minitage.core.fetchers import interfaces as fetchers
from minitage.core.makers import interfaces as makers
from minitage.core.version import __version__
from minitage.core import update as up
from minitage.core.common import newline

try:
    from os import uname
except:
    from platform import uname

DEFAULT_BINARIES_URL = 'http://distfiles.minitage.org/public/externals/minitage/packages'
CORE_MINILAYS_URLBASE = 'https://github.com/minitage/minilays'

class MinimergeError(Exception):
    """General Minimerge Error"""


class NoPackagesError(MinimergeError):
    """No packages are given to merge"""


class ConflictModesError(MinimergeError):
    """Minimerge used without arguments."""


class InvalidConfigFileError(MinimergeError):
    """Minimerge config file is not valid."""


class TooMuchActionsError(MinimergeError):
    """Too much actions are given to do"""


class CliError(MinimergeError):
    """General command line error"""

class ActionError(MinimergeError):
    """General action error"""


class MinibuildNotFoundError(MinimergeError):
    """Minibuild is not found."""


class CircurlarDependencyError(MinimergeError):
    """There are circular dependencies in the dependency tree"""


PYTHON_VERSIONS = ('2.4', '2.5', '2.6')



def get_default_arch():
    arch = uname()[4]
    arch32_re = re.compile('i[345678]86')
    binary_arch = '32'
    if arch32_re.match(arch):
        binary_arch = '32'
    if '32' in arch:
        binary_arch = '32'
    if '64' in arch:
        binary_arch = '64'
    return binary_arch

class Minimerge(object):
    """Minimerge object."""

    def store_config(self, configp=None):
        if not configp:
            configp = self._config_path
        shutil.copy2(configp, configp+'.sav')
        fic = open(configp, 'w')
        self._wconfig.write(fic)
        fic.flush()
        fic.close()
        newline(configp)

    def get_binary_urls(self, package):
        urls = []
        src = package.name
        src += '-binary.tar.gz'
        for url in self.binaries_urls:
            urls.append('%s/%s/%s/%s' % (url,
                                         self.binaries_platform,
                                         self.binaries_arch,
                                         src)
                       )
        return urls

    def __init__(self, options=None):
        """Options are taken from the section 'minimerge'
        in the configuration file  then can be overriden
        in the input dictionnary.
        Arguments:
            - options:

                - jump: package in the dependency tree to jump to
                - packages: packages list to handle *mandatory*
                - debug: debug mode
                - fetchonly: just get the packages
                - fetchfirst: if True, fetch all packages before building
                - offline: do not try to connect outside
                - nodeps: Squizzes all dependencies
                - action: what to do *mandatory*
                - sync: sync mode
                - config: configuration file path *mandatory*
                - binary: allow use of binaries in the form:
                        http://binaryurl/platform/arch/package_name(-packageversion)*.tar.gz
                - flags :

                    - ask: prompt to continue
                    - pretend: do nothing that print what would be done.
                    - verbose: True to be verbose.
        """
        self.verbose = options.get('verbose', False)
        self.history_dir = '.minitage'
        self._config_path = os.path.expanduser(options.get('config'))
        if not os.path.isfile(self._config_path):
            message = 'The config file is invalid: %s' % self._config_path
            raise InvalidConfigFileError(message)

        if not options.get('nolog', False):
            self._init_logging(self.verbose)

        if options is None:
            options = {}
        # first try to read the config in
        # - command line
        # - exec_prefix
        # - ~/.minimerge.cfg
        # We have the corresponding file allready filled in option._config, see
        # `minimerge.core.cli`
        #

        # read our config
        self._config = ConfigParser.ConfigParser()
        self._wconfig = WritableConfigParser()
        try:
            self._config.read(self._config_path)
            self._wconfig.read(self._config_path)
        except:
            message = 'The config file is invalid: %s' % self._config_path
            raise InvalidConfigFileError(message)

        # prefix is setted in the configuration file
        # it defaults to sys.exec_prefix
        self._prefix = self._config._sections.get('minimerge', {}) \
                                .get('prefix', sys.exec_prefix)

        self.backup_path = os.path.join(self._prefix, 'backups')
        # modes
        # for offline and debug mode, we see too if the flag is not set in the
        # configuration file
        self._jump = options.get('jump', False)
        self._nodeps = options.get('nodeps', False)
        self._debug = options.get('debug', self._config._sections\
                                  .get('minimerge', {}).get('debug', False))
        self._fetchonly = options.get('fetchonly', False)
        self._fetchfirst = options.get('fetchfirst', False)
        self._only_dependencies = options.get('only_dependencies', False)
        self._all_python_versions = options.get('all_python_versions', False)
        self._update = options.get('update', False)
        self._upgrade = options.get('upgrade', True)
        self._pretend = options.get('pretend', False)
        self._ask = options.get('ask', False)
        self._offline = options.get('offline', self._config._sections\
                                    .get('minimerge', {}).get('offline', False))

        self._packages = options.get('packages', [])

        # what are we doing
        self._action = options.get('action', False)

        self._minilays = []
        minilays_search_paths = []
        # minilays can be ovvrided by env["MINILAYS"]
        minilays_search_paths.extend(
            os.environ.get('MINILAYS', '').strip().split()
        )
        self.first_run = options.get('first_run', False)
        # minilays are in minilays/
        minilays_parent = os.path.join(self._prefix, 'minilays')
        self.minilays_parent = minilays_parent
        if os.path.isdir(minilays_parent):
            minilays_search_paths.extend([os.path.join(minilays_parent, dir)
                                        for dir in os.listdir(minilays_parent)])
        # they are too in etc/minmerge.cfg[minilays]
        minimerge_section = self._config._sections.get('minimerge', {})
        minilays_section = minimerge_section.get('minilays', '')
        minilays_search_paths.extend(minilays_section.strip().split())

        # minitage binaries
        self.use_binaries = options.get('binary', False)

        self.binaries_urls = minimerge_section.get('binaries_url', '').strip().split()
        self.binaries_platform = minimerge_section.get('binaries_platform', '').strip()
        self.binaries_arch = minimerge_section.get('binaries_arch', '').strip()
        if not self.binaries_platform in ('linux2'):
            if not self.binaries_platform == sys.platform:
                self.binaries_platform = None
        if not self.binaries_arch in ('32', '64'):
            self.binaries_arch = None
        if not self.binaries_urls:
            self.binaries_urls.append(DEFAULT_BINARIES_URL)
        if not self.binaries_arch:
            self.binaries_arch = get_default_arch()
        if not self.binaries_platform:
            self.binaries_platform = sys.platform

        # installed binaries packages
        self._binaries = []

        # sortings pathes to let the default minilays be at worse priority
        def minilays_sort(path, path2):
            if os.path.dirname(path2) == self.minilays_parent:
                if os.path.basename(
                    path2
                ) in self.get_default_minilays():
                    return -1
            if os.path.dirname(path) == self.minilays_parent:
                if os.path.basename(
                    path
                ) in self.get_default_minilays():
                    return 1
            return 0
        minilays_search_paths.sort(minilays_sort)

        # filtering valid ones
        # and mutating into real Minilays objects
        self._minilays = [objects.Minilay(
            path = os.path.expanduser(dir),
            minitage_config = copy.deepcopy(self._config)) \
            for dir in minilays_search_paths if os.path.isdir(dir)]
        if options.get('reinstall_minilays', False):
            self.reinstall_minilays()
        self.pyvers = {}
        # TODO: desactivating :: need MORE TESTS !!!
        if not options.get('skip_self_upgrade', False):
            self.update()


    def update(self):
        updates = up.UPDATES.keys()
        updates.sort()
        callables_versions = {}
        if not self._wconfig.has_section('updates'):
            self._wconfig.add_section('updates')
        self.store_config()
        todo = []

        # mark everything done on new minitiage
        if self.first_run:
            for update in updates:
                self._wconfig.set('updates', update, 'done')
            self.store_config()
        else:
            for update in updates:
                done = False
                try:
                    done = self._wconfig.get('updates', update, 'foo') == 'done'
                except:
                    pass
                if not done:
                    old_version =v = pkg_resources.parse_version(update)
                    current_version = pkg_resources.parse_version(__version__)
                    if old_version <= current_version:
                        for u in up.UPDATES[update]:
                            if not u in callables_versions:
                                callables_versions[u] = []
                            callables_versions[u].append(update)
                            if not u in todo:
                                todo.append(u)

            if todo:
                self.logger.info('Minitage needs updates, running them now!')
                for t in todo:
                    try:
                        t(self)
                        for version in callables_versions[t]:
                            self._wconfig.set('updates', version, 'done')
                    except Exception, e:
                        self.store_config()
                        self.logger.error('Update failed, please either bugreport or '
                                          'contact the developers on IRC: '
                                          '#minitage@irc.freenode.org')
                        self.logger.error('Give them this snippet: %s' % todo)
                        self.logger.error('Give them this error also: %s' % e)
                        sys.exit(1)
        self.store_config()

    def find_minibuild(self, package):
        """
        @param package str minibuild to find
        Exceptions
            - MinibuildNotFoundError if the packages is not found is any minilay.

        Returns
            - The minibuild found
        """
        for minilay in self._minilays:
            if package in minilay:
                return minilay[package]
        message = 'The minibuild \'%s\' was not found' % package
        raise MinibuildNotFoundError(message)

    def find_minibuilds(self, packages):
        """
        @param package list minibuild to find
        Exceptions
            - MinibuildNotFoundError if the packages is not found is any minilay.

        Returns
            - The minibuild found
        """
        cpackages = []
        for package in packages:
            cpackages.append(self._find_minibuild(package))
        return cpackages

    def compute_dependencies(self, packages = None, ancestors = None):
        """
        @param package list list of packages to get the deps
        @param ancestors list list of tuple(ancestor,level of dependency)
        Exceptions
            - CircurlarDependencyError in case of curcular dependencies trees

        Returns
            - Nothing but self.computed_packages is filled with needed
            dependencies. Not that this list must be reversed.
        """
        if packages is None:
            packages = []
        if ancestors is None:
            ancestors = []

        for package in packages:
            mb = self._find_minibuild(package)
            # test if we have not already the package in our deps list, then
            # ...
            # if we have no ancestor, the end of the list is fine.
            index = len(ancestors)
            # if we have ancestors
            if ancestors:
                # we must check ancestor installation priority:
                #  we must install dependencies prior to the first
                #  package which have the dependency in its list
                for ancestor in ancestors:
                    if mb.name in ancestor.dependencies:
                        index = ancestors.index(ancestor)
                        break
            # last check if package is not already there.
            if not mb in ancestors:
                ancestors.insert(index, mb)
            # unconditionnaly parsing dependencies, even if the package is
            # already there to detect circular dependencies
            try:
                ancestors = self._compute_dependencies(mb.dependencies,
                                                       ancestors=ancestors)
            except RuntimeError,e:
                message = 'Circular dependency around %s and ancestors: \'%s\''
                raise CircurlarDependencyError(message %
                                         (mb.name, [m.name for m in ancestors]))
        return ancestors

    def is_package_src_to_be_fetched(self, package):
        """Does the package folder need to be fetched/unpacked"""
        downloaded, incomplete, ret = False, False, False
        destination = self.get_install_path(package)
        if os.path.exists(destination):
            files = [f for f in os.listdir(destination) if not f.startswith('.')]
            if not files:
                incomplete = True
            if package.install_method == 'buildout':
                cfg = package.minibuild_config._sections.get(
                    'minibuild',
                    {}
                ).get(
                    'buildout_config',
                    'buildout.cfg'
                )
                cfg_fp = os.path.join(
                    self.get_install_path(package),
                    cfg
                )
                if not os.path.exists(cfg_fp):
                    raise MinimergeError(
                        'The directory already present in %s previous to co/updating the code '
                        'seems to be incomplete or unrelated '
                        'as it does not have the buildout \'%s\' (%s).\n'
                        '\tPlease move it to another place or change it to '
                        'adequate the minibuild \'%s\' (%s) specification.' % (
                            self.get_install_path(package), cfg, cfg_fp,
                            package.name, package.path
                        )
                    )
                    incomplete = True
        if incomplete or not os.path.exists(destination):
            ret = True
        return ret

    def is_package_src_to_be_updated(self, package):
        """Does the package folder need to be updated"""
        ret = False
        if (self._update
            or self.has_new_revision(package)
            or not self.is_installed(package)
           ):
            ret = True
        return ret

    def is_package_to_be_installed(self, package):
        """Does this package need to be installed."""
        ret = False
        if (not self.is_installed(package)
            and (self._action in ['install', 'reinstall'])):
            ret = True
        return ret

    def is_package_to_be_reinstalled(self, package):
        """Does this package need to be installed."""
        ret = False
        if (
            (
                (self._action == 'reinstall')
                and self.is_installed(package)
            )
            or (
                self.is_package_to_be_upgraded(package)
               )
        ):
            ret = True
        return ret

    def is_package_to_be_upgraded(self, package):
        """Does this package need to be upgraded."""
        ret = False
        if (self.is_installed(package)
            and self.has_new_revision(package)
            and (self._action in ['install', 'reinstall'])):
            ret = True
        return ret

    def is_package_to_be_updated(self, package):
        """Does this package need to be upgraded."""
        ret = False
        if (self.is_installed(package)
            and ((self._update)
                 or (self._action in ['install', 'reinstall']
                     and self.has_new_revision(package))
                )
           ):
            ret = True
        return ret

    def is_package_to_be_deleted(self, package):
        """Does this package need to be upgraded."""
        ret = False
        if (self.is_installed(package)
            and (self._action in ['delete'])):
            ret = True
        return ret

    def is_package_marked(self, package, marker):
        """Does the history contain the specific marker"""
        fmarker = self.get_package_mark_common(package, marker)
        if os.path.exists(fmarker):
            return True
        return False

    def get_package_mark_common(self, package, marker):
        """Get from the history the specific marker common function"""
        ipath = self.get_install_path(package)
        hd = os.path.join(ipath, self.history_dir, 'markers')
        return os.path.join(hd, marker)


    def get_package_mark(self, package, marker):
        """Get from the history the specific marker"""
        fmarker = self.get_package_mark_common(package, marker)
        if os.path.exists(fmarker):
            return open(fmarker).read()
        return ''

    def get_package_mark_as_file(self, package, marker):
        """Get from the history the specific marker file descriptor"""
        fmarker = self.get_package_mark_common(package, marker)
        if os.path.exists(fmarker):
            return open(fmarker)

    def get_package_mark_path(self, package, marker):
        """Get from the history the specific marker filepath"""
        fmarker = self.get_package_mark_common(package, marker)
        if os.path.exists(fmarker):
            return fmarker

    def set_package_mark(self, package, marker, text=''):
        """Set in the history the specific marker with the wanted value"""
        ipath = self.get_install_path(package)
        hd = os.path.join(ipath, self.history_dir, 'markers')
        if not os.path.exists(hd):
            os.makedirs(hd)
        fic = open(os.path.join(hd, marker), 'w')
        fic.write(text)
        fic.close()

    def record_minibuild(self, package):
        """Copy in the history the current minibuild"""
        ipath = self.get_install_path(package)
        hd = os.path.join(ipath, self.history_dir)
        hdm = os.path.join(hd, 'minibuild')
        if not os.path.exists(hd):
            os.makedirs(hd)
        shutil.copy2(package.path, hdm)

    def get_installed_minibuild(self, package):
        """Get in the history the relevant minibuild"""
        mb = None
        ipath = self.get_install_path(package)
        hd = os.path.join(ipath, self.history_dir)
        hdm = os.path.join(hd, 'minibuild')
        if self.is_installed(package):
            if os.path.exists(hdm):
                mb = objects.Minibuild(path=hdm, minitage_config=self._config)
            else:
                # packae is installed but without history, old minitage versions
                # take the reference minibuild as the installed one.
                mb = package
        return mb

    def is_installed(self, package):
        ip = self.get_install_path(package)
        hd = os.path.join(ip, self.history_dir)
        ret = False
        if package.category == 'eggs':
            versions = []
            pm = self.pyvers
            if package.name in pm:
                versions = pm[package.name]
            for version in versions:
                if self.is_package_marked(package, 'install-%s' % version):
                    ret = True
                else:
                    ret = False
                    break
        # minitage has got the revision and history system
        elif self.is_package_marked(package, 'install'):
            ret = True
        return ret


    def has_new_revision(self, package):
        """Does this package has a new revision to be installed"""
        oldrev = self.get_installed_revision(package)
        ret = False
        if oldrev is not None:
            if package.revision > oldrev:
                ret = True
        return ret

    def get_installed_revision(self, package):
        """Get the installed revision of a package"""
        revision = None
        if self.is_installed(package):
            mb = self.get_installed_minibuild(package)
            if mb:
                revision = mb.revision
        return revision

    def _fetch(self, package):
        """
        @param param minitage.core.objects.Minibuid the minibuild to fetch
        Exceptions
           - MinimergeFetchComponentError if we do not found any component to
             fetch the package.
           - The fetcher exception.
        """
        self.logger.debug('Will fetch package %s.' % (package.name))
        destination = self.get_install_path(package)
        dest_container = os.path.dirname(destination)
        fetcherFactory = fetchers.IFetcherFactory(self._config_path)
        # add maybe the scm to the path if it is avalaible
        mfetcher = fetcherFactory(package.src_type)
        sfetcher = fetcherFactory('static')
        # in dependencies dir.
        #try to add scms merged via minitage to the path.
        deps = os.path.join(
            self.getPrefix(), 'dependencies')
        scm = getattr(mfetcher, 'executable', None)
        if scm:
            # do we minimerged yet
            # and added a dependency directory?
            if os.path.exists(deps):
                for path in os.listdir(deps):
                    fp = os.path.join(
                        deps,
                        path,
                        'parts', 'part', 'bin')
                    if os.path.exists(
                        os.path.join(fp, scm)):
                        self.logger.debug(
                            'Adding %s to your path, this will '
                            'enable %s \'scm\'.' % (fp, scm)
                        )
                        os.environ['PATH'] = '%s%s%s' % (
                            fp, ':', os.environ['PATH']
                    )
        # add also minitage top /bin directory
        os.environ['PATH'] = '%s%s%s' % (
            os.path.join(self._prefix, 'bin'),
            ':',
            os.environ['PATH']
        )

        urls_descriptions = []
        if self.use_binaries:
            urls_descriptions.extend([(True, sfetcher, url)
                                      for url in self.get_binary_urls(package)])
        urls_descriptions.append((False, mfetcher, package.src_uri,))
        # create categ dir
        if not os.path.isdir(dest_container):
            os.makedirs(dest_container)
        for is_binary, fetcher, src_uri in urls_descriptions:
            try:
                if self.is_package_src_to_be_fetched(package):
                    self.logger.info('Fetching package %s from %s.' % (
                        package.name, src_uri)
                    )
                    fetcher.fetch(destination, src_uri)
                    self.set_package_mark(package, 'fetch', 'fetch')
                    downloaded = True
                if self.is_package_src_to_be_updated(package):
                    self.logger.info('Updating package %s from %s.' % (
                        package.name, src_uri)
                    )
                    if fetcher._has_uri_changed(destination, package.src_uri):
                        temp = os.path.join(os.path.dirname(destination),
                                            'minitage-checkout-tmp',
                                            package.name)
                        if os.path.isdir(temp):
                            shutil.rmtree(temp)
                        fetcher.fetch(temp, package.src_uri)
                        copy_tree(temp, destination)
                        shutil.rmtree(temp)
                    else:
                        fetcher.update( destination, src_uri)
                    self.set_package_mark(package, 'fetch', 'fetch')
                    downloaded = True
                if is_binary and downloaded:
                    self.logger.info('Using binary package: %s' % package.name)
                    self._binaries.append(package)
                break
            except Exception, e:
                # ignore fetching errors from binary, we just make error
                # if we cant get the source archive.
                if is_binary:
                    continue
                raise

    def _do_action(self, action, packages, pyvers = None):
        """Do action.
        Install, delete, generate .env,  or reinstall a list of packages (minibuild instances).
        Arguments
            - action: reinstall|install|delete|generate_env action to do.
            - packages: minibuilds to deal with in order!
            - pyvers: dict(package, [pythonver,]
        """
        if pyvers is None:
            pyvers = {}

        maker_kwargs = {}

        mf = makers.IMakerFactory(self._config_path)
        for package in packages:
            # if we are an egg, we maybe will have python versions setted.
            maker_kwargs['python_versions'] = pyvers.get(package.name, None)
            # we install unless we are dealing with a meta
            if not package.name.startswith('meta-'):
                options = {}

                # installation prefix
                ipath = self.get_install_path(package)

                # get the maker right for the install method
                maker = mf(package.install_method)

                # let our underlying maker make some addtionnnal choices for the
                # build options.
                options = maker.get_options(self, package, **maker_kwargs)

                # set offline and debug mode
                options['offline'] = self._offline
                options['minibuild'] = package
                options['debug'] = self._debug
                options['verbose'] = self.verbose

                # finally, time to act.
                if not os.path.isdir(ipath):
                    os.makedirs(ipath)
                callback = getattr(maker, action, None)
                if callback:
                    if ((package.category == 'eggs')
                        and (action in ['install', 'reinstall'])):
                        if 'parts' in options:
                            real_parts = []
                            parts = options['parts']
                            for v in PYTHON_VERSIONS:
                                for part in parts:
                                    if part.endswith(v):
                                        reinstall = self.is_package_to_be_reinstalled(
                                            package
                                        )
                                        if (not self.is_package_marked(
                                            package,
                                            'install-%s' % v)
                                            or reinstall):
                                            real_parts.append(part)
                            options['parts'] = real_parts
                    callback(ipath, options)
                    if action in ['install', 'reinstall']:
                        self.record_minibuild(package)
                        onlyrecord = True
                        if package.category == 'eggs':
                            onlyrecord = False
                            parts = options.get('parts', [])
                            if len(parts)>0:
                                versions = []
                                for part in parts:
                                    for v in PYTHON_VERSIONS:
                                        if part.endswith(v):
                                            versions.append(v)
                                for v in versions:
                                    self.set_package_mark(package,
                                                      'install-%s' % (v),
                                                      'install-%s' % (v))
                            else:
                                onlyrecord = True
                        self.generate_env(package)
                        if onlyrecord:
                            self.set_package_mark(package, action, action)
                elif action == 'generate_env':
                    self.generate_env(package)
                else:
                    message = 'The action \'%s\' does not exists ' % action
                    message += 'in this \'%s\' component' \
                            % ( package.install_method)
                    raise ActionError(message)


    def _cut_jumped_packages(self, packages):
        """Remove jumped packages."""
        try:
            m = self._find_minibuild(self._jump)
            if m:
                names = [package.name for package in packages]
                i = names.index(m.name)
                packages = packages[i:]
        except Exception, e:
            pass
        return packages


    def pretend(self, packages):
        """Return a string indication what will be done on packages list"""
        log = StringIO()
        log.write('Action:\t%s\n\n' % self._action)
        if packages:
            self.logger.debug('Packages:')
            for p in packages:
                EMPTY_CELL = ' '
                actionsd = {
                    'fetch': (True==self.is_package_src_to_be_fetched(p)
                              and 'f' or EMPTY_CELL),
                    'updatecode': (True==self.is_package_src_to_be_updated(p)
                                    and 'F' or EMPTY_CELL),
                    'install': (True==self.is_package_to_be_installed(p)
                                and 'I' or ''),
                    'reinstall': (True==self.is_package_to_be_reinstalled(p)
                                  and 'R'or ''),
                    'delete': (True==self.is_package_to_be_deleted(p)
                                and 'D' or ''),
                    'upgrade': (True==self.is_package_to_be_upgraded(p)
                                and 'U' or EMPTY_CELL),
                    'update': (True==self.is_package_to_be_updated(p)
                                and 'u' or EMPTY_CELL),
                }
                actions = '%s' % (
                    '%(fetch)s%(updatecode)s'
                    '%(install)s%(reinstall)s%(delete)s'
                    '%(upgrade)s%(update)s' % actionsd
                )
                pyvers = ''
                if p.category == 'eggs':
                    versions, iversions = [], []
                    pm = self.pyvers
                    if p.name in pm:
                        versions = pm[p.name]
                    for version in versions:
                        reinstall = self.is_package_to_be_reinstalled(p)
                        if (not self.is_package_marked(p, 'install-%s' % version)
                            or reinstall):
                            iversions.append(version)
                    if len(iversions)>0:
                        pyvers = '(%s)' % (', '.join(iversions))
                revision = ''
                if self.is_package_to_be_upgraded(p):
                    revision = '[%s => %s]' % (self.get_installed_revision(p), p.revision)
                log.write('\t\t%s * %s %s %s\n' % (actions, p.name, revision, pyvers))
        log.write('\n')
        log.write('\t FLAGS * PACKAGE_NAME [OLD_REVISION => NEW_REVISION] (python versions)\n')
        log.write('\t f : fetch\n')
        log.write('\t F : update the code from repository\n')
        log.write('\t I : install the package\n')
        log.write('\t R : reinstall the package\n')
        log.write('\t D : delete the package\n')
        log.write('\t U : upgrade the package to the lastest revision if any\n')
        log.write('\t u : update the package (for example, re run buildout)\n')
        return log

    def main(self):
        """Main loop.
          Here executing the minimerge tasks:
              - calculate dependencies
              - for each dependencies:

                  - maybe fetch / update
                  - maybe install
                  - maybe delete
        """
        if self._action == 'sync':
            self._sync()
        else:
            packages = self._packages
            # compute dependencies
            self.logger.debug('Calculating dependencies.')
            if not self._nodeps:
                packages = self._compute_dependencies(self._packages)
            if self._nodeps:
                packages = self._find_minibuilds(self._packages)
            direct_dependencies = self._find_minibuilds(self._packages)

            if self._jump:
                # cut jumped dependencies.
                packages = self._cut_jumped_packages(packages)
                self.logger.debug('Shrinking packages away. _1/2_' )

            # cut pythons we do not need !
            # also get the parts to do in 'eggs' buildout
            pypackages, pyvers = self._select_pythons(packages[:])
            self.pyvers = pyvers
            #pypackages, _ = self._select_pythons(direct_dependencies)

            ## do not take python tree in account if we are in nodep mode
            if not self._nodeps:
                # fiter only python deptree
                pypackages = [p for p in pypackages 
                              if not p.name in [d.name for d in direct_dependencies]]

                # add dependency packages
                noecho = [pypackages.append(p)
                          for p in packages
                          if not p.name in [q.name for q in pypackages]]
                packages = pypackages

            # cut jumped dependencies again.
            if self._jump:
                self.logger.debug('Shrinking packages away. _2/2_')
                packages = self._cut_jumped_packages(packages)

            if self._only_dependencies:
                packages = [p for p in packages if not p.name in self._packages]

            packages = [p for p in packages
                        if (
                            self.is_package_to_be_installed(p)
                            or self.is_package_to_be_reinstalled(p)
                            or self.is_package_to_be_upgraded(p)
                            or self.is_package_to_be_updated(p)
                            or self.is_package_to_be_deleted(p)
                            or self._action == 'generate_env'
                           )
                       ]
            pretend = self.pretend(packages)
            self.logger.debug(pretend.getvalue())

            stop = False
            answer = ''
            valid_answers = ('y', '', 'yes')
            if self._ask:
                print
                print 'Continue ? (y|n)'
                answer = raw_input()

            if self._pretend \
               or not answer.lower() in valid_answers:
                self.logger.info('Running in pretend mode or'
                                 ' user choosed to abort')
                stop = True

            if not stop:
                if answer:
                    self.logger.info('User choosed to continue')


                # fetch first, or just in time
                if self._fetchfirst:
                    # fetch all first, build after
                    for package in packages:
                        if not package.name.startswith('meta-'):
                            # fetch if not offline
                            if not (self._offline or self._action == 'delete'):
                                self._fetch(package)
                    # if we do not want just to fetch, let's go ,
                    # (install|delete|reinstall) baby.
                    if not self._fetchonly:
                        if not package in self._binaries:
                            self._do_action(self._action, packages, pyvers)
                else:
                    # just in time fetch
                    for package in packages:
                        if not package.name.startswith('meta-'):
                            # fetch if not offline
                            if not (self._offline or self._action == 'delete'):
                                self._fetch(package)
                            # if we do not want just to fetch, let's go ,
                            if not self._fetchonly:
                                # (install|delete|reinstall|generate_env) baby.
                                if not package in self._binaries:
                                    self._do_action(self._action, [package], pyvers)

    def _select_pythons(self, packages, test=False):
        """Get pythons to build into dependencies.
        Handle multi site-packages is not that tricky:
            - We have to install python-major.minor only
              if we need it
            - We must build eggs site-packages only if
              we need them too.

        The idea i found is something like that:
            - We look in the packages to see if they want a
              particular python.

               * If 'meta-python' is set in a direct dependency and the
                 dependency is an egg: we grab all versions

               * If a particular 'python-MAJOR.minor' is set in
                 the dependencies: we grab this version for selection.

               * if 'meta-python' is set on a dependency, we will use:

                       - an already installed python if any
                       - the most recent one otherwise

            - Next, when we have selected pythons, we will:

                * put our select pythons and their dependencies
                  at the top of the dep tree
                * delete others python and their dependencies
                  from the dependency tree.
                * map eggs and selected version for later use.

        Return
            - tuple with the according packages without uneeded stuff
              and a dict for the eggs with just the needed parts.
                ([new, packages, list], {'packagename': (buildout, parts)}
        """
        # select wich version of python are really needed.


        pyversions = []
        selected_pyver = {}
        metas = []
        pythons = [('python-%s' % version, version) \
                   for version in PYTHON_VERSIONS]
        ALL = False

        # look if we have eggs in direct dependencies,
        # if so: just build all site-packages available.
        direct_dependencies = self._find_minibuilds(self._packages)
        for package in direct_dependencies:
            if package.name in [python[0]\
                                for python in pythons]:
                pyversions.append(
                    package.name.replace('python-', '')
                )
            if package.category == 'eggs' and self._all_python_versions:
                pyversions.extend(PYTHON_VERSIONS)
                ALL = True
                break

        if not ALL:
            for package in packages:
                # first look if we have some python-ver in direct dependencies
                # and select them
                for python, version in pythons:
                    if python in package.dependencies \
                       and not package.name == 'meta-python':
                        if version not in pyversions:
                            pyversions.append(version)
                # if this is a meta or and egg, record it for later use
                if 'meta-python' in package.dependencies\
                   or package.category == 'eggs':
                    metas.append(package)

            # if we got meta packages but no particular python versions
            # on the run, we need to select the righ(s) versions to install
            if not pyversions:
                if metas:
                    # look if we hav allready installed pythons and select
                    # the first 'more recent' and exists
                    mostrecentpy = pythons[:]
                    mostrecentpy.reverse()
                    for python, version in mostrecentpy:
                        if os.path.exists(
                            os.path.join(
                                self._prefix,
                                'dependencies',
                                python
                            )):
                            if version not in pyversions:
                                pyversions.append(version)
                            break

                    # if we havent got any python version, and no python is
                    # already installed, we will need to merge one.
                    # eggs must have meta-python in their dependencies, so if we
                    # are building an egg which is not on direct dependencies.
                    # We will select at least the most recent python version
                    # there.
                    if not pyversions:
                        pyversions.append(pythons[:].pop()[1])

                # do nothing if we have no meta in dependencies and no python
                # too. python is not always a dependency :)
                else:
                    pass

        # change our real depedency tree according to local pythons
        # if we got meta or particular python versions.
        # get the dependencies for each python
        selected_pys = ['python-%s' % version for version in pyversions]
        python_deptree = self._compute_dependencies(selected_pys)

        # before inserting our new python deptree we will need to:
        #  - cut prior python dependencies if we have any
        #  - set python versions to build against for eggs.
        py_pn = [package.name for package in python_deptree]
        dp = []
        for p in packages:
            dp.extend(
                [self.find_minibuild(m) for m in p.dependencies]
            )

        dp = dp + packages[:]
        for package in dp:
            # cut dependency if we need to cut it.
            # cut also not others python.
            if package.name in py_pn + [python[0] for python in pythons]:
                dp.pop(dp.index(package))
            if package.category == 'eggs':
                selected_pyver[package.name] = pyversions

        # insert our selected python(s) deptree at the top of our packages list
        python_deptree.extend(dp)

        # filter doublons
        selected_p = []
        noecho = [selected_p.append(p)
                  for p in python_deptree
                  if not p.name in [q.name for q in selected_p]]

        return selected_p, selected_pyver

    def _sync(self):
        """Sync or install our minilays."""
        # install our default minilays
        self.logger.info('Syncing minilays.')
        version = '.'.join( __version__.split('.')[:2])


        default_minilays = self.get_default_minilays()
        minimerge_section = self._config._sections.get('minimerge', {})
        urlbase = '%s.%s' % (CORE_MINILAYS_URLBASE, version)
        f = fetchers.IFetcherFactory(self._config_path)
        hg = f('static')

        # create default minilay dir in case
        if not os.path.isdir(os.path.join(self._prefix,'minilays')):
            os.makedirs(os.path.join(self._prefix,'minilays'))

        default_minilays_pathes_urls = [(os.path.join(
                                           self._prefix,
                                           'minilays',
                                           minilay),
                                           '/'.join(( '%s.%s' % (urlbase, minilay), 'tarball', 'master'))
                                       )\
            for minilay in default_minilays]
        for d, url in default_minilays_pathes_urls:
            self.logger.info('Syncing %s from %s [via %s]' % (d, url, hg.name))
            if not os.path.exists(d):
                hg.fetch(d, url)
            else:
                hg.update(d, url)

        # for others minilays, we just try to update them
        for minilay in [m
                        for m in self._minilays
                        if not os.path.basename(m.path) in default_minilays]:
            path = minilay.path
            type = None
            # querying scm factory for registered scms
            # and removing static
            scms = [key for key in f.products.keys() if key != 'static']
            scmfound = False
            for strscm in scms:
                if os.path.isdir(
                    os.path.join(
                        path,
                        '.%s' % strscm
                    )
                ):
                    scmfound = True
                    scm = f(strscm)
                    try:
                        self.logger.info('Syncing %s from %s [via %s]' % (path, scm.get_uri(path), strscm))
                        scm.update(dest=path, uri=scm.get_uri(path), verbose=self.verbose)
                    except Exception, e:
                        self.logger.info('Syncing %s FAILED : %s' % (path, e))
            if not scmfound:
                self.logger.info(
                    'The minilay found in %s appears '
                    'not to be versionned, is that normal? '
                    'Think to do it when your project is ready to distribute'% (
                        minilay.path
                    )
                )

        self.logger.info('Syncing done.')

    def _init_logging(self, verbose=False):
        """Initialize logging system."""
        # configure logging system$
        try:
            logging.config.fileConfig(self._config_path)
        except:
            # just a stdout handler
            h = logging.StreamHandler()
            logging.root.addHandler(h)
        if self.verbose:
            logging.root.setLevel(0)
        else:
            logging.root.setLevel(logging.INFO)

        self.logger = logging.getLogger('minitage.core')
        self.logger.debug('(Re)Initializing minitage logging system.')


    def getUpgrade(self):
        """Accessor."""
        return self._upgrade

    def getPrefix(self):
        """Accessor."""
        return self._prefix

    def get_install_path(self, package):
        """Get a minibuild install path location."""
        # installation prefix
        ip = '/ia/am/a/non/existing/path%s%s' % (random.randint(0,123456789),
                                             random.randint(0,123456789)
                                            )
        if not package.name.startswith('meta-'):
            ip = os.path.join(
                self._prefix,
                package.category,
                package.name
            )
        return ip


    def reinstall_packages(self, packages):
        update  = self._update
        upgrade = self._upgrade
        self._update  = True
        self._upgrade = True
        for package in packages:
            package = self.find_minibuild(package)
            self._fetch(package)
            self._do_action('install', [package])

    def get_default_minilays(self):
        return [s.strip() \
                for s in self._config._sections\
                .get('minimerge', {})\
                .get('default_minilays','')\
                .split('\n')]

    def generate_env(self, mb):
        try:
            self.logger.debug('.env will be regenerated for %s' % mb.name)
            top = [os.path.join(self._prefix, 'bin', 'paster'), 
                   'create', '-q',
                   '-t', 'minitage.instances.env',
                   '--no-interactive',
                   mb.name
                  ] 
            retcode = subprocess.call(top)
            self.logger.info('.env has been regenerated for %s' % mb.name)
        except:
            # minitage.paste is not installed anymore
            self.logger.warning('Not regenerating .envs for %s' % mb.path) 

    def reinstall_minilays(self):
        ms = self.get_default_minilays()
        msbp = os.path.join(
            self.backup_path, 'minilays',
            datetime.datetime.now().strftime('%Y-%m-%d')
        )
        if not os.path.exists(msbp):
            os.makedirs(msbp)
        for path in os.listdir(self.minilays_parent):
            mpath = os.path.join(
                self.minilays_parent,
                path
            )
            if path in ms:
                mbp = os.path.join(msbp, path)
                if not os.path.exists(mbp):
                    os.rename(mpath, mbp)
                if os.path.exists(mpath):
                    shutil.rmtree(mpath)
        self._sync()

    # api: do not break code
    _find_minibuilds = find_minibuilds
    _find_minibuild = find_minibuild
    _compute_dependencies = compute_dependencies

