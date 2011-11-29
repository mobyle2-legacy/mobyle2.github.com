# Copyright (C) 2009, Mathieu PASQUET <kiorky@cryptelium.net>
# -*- coding: utf-8 -*-
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

import copy
import distutils
import os
import urllib
import urllib2
import urlparse
import shutil
import sys
import re
import tarfile
import tempfile
import subprocess
import py_compile
import traceback
import logging
from pprint import pprint
from distutils.dir_util import copy_tree

import setuptools
from ConfigParser import NoOptionError
import iniparse as ConfigParser
import pkg_resources
from setuptools.command import easy_install
import zc.buildout.easy_install

from minitage.recipe.common import common
from minitage.core.fetchers.interfaces import IFetcherFactory
from minitage.core import core
from minitage.core.common import splitstrip, remove_path, letter_re

PATCH_MARKER = 'ZMinitagePatched'
BOOTSTRAP = "http://svn.zope.org/*checkout*/zc.buildout/trunk/bootstrap/bootstrap.py"

BOOTSTRAP_DISTRIBUTE_SCRIPT = """
import urllib2
ez = {}
exec urllib2.urlopen('http://python-distribute.org/distribute_setup.py'
                ).read() in ez
ez['use_setuptools'](to_dir='%(destination)s', download_delay=0, no_fake=True)
"""

if sys.platform.startswith('win'):
    PATCH_MARKER = 'zmpatch'
orig_versions_re = re.compile('-*%s.*' % PATCH_MARKER, re.U|re.S)
version_comment_remover_re = re.compile('^(?P<version>[^\#\s]+)\s*\#', re.U|re.S|re.M|re.X)

def get_orig_version(version):
    if not version: version = ''
    return orig_versions_re.sub('', version)

class IncompatibleVersionError(zc.buildout.easy_install.IncompatibleVersionError): pass
class DistributionDownloadError(Exception): pass

def get_requirement_version(requirement):
    patched_egg, version= False, None
    operators = ['=', '<', '<']
    for spec in requirement.specs:
        for item in spec:
            sitem = '%s' % item
            if sys.platform.startswith('win'):
                sitem = sitem.lower()
            if PATCH_MARKER in sitem:
                patched_egg = True
        if len(spec) >= 2:
            if spec[0] == '==':
                version = spec[1]
    return version, patched_egg

first_digit_re =  re.compile('^(\d).*', re.M|re.S|re.U)
def get_first_dist(where):
    dists = [a
             for a in setuptools.package_index.distros_for_filename(
                 where
             )
           ]
    if len (dists) > 1:
        sorted_dists = dists[:]
        sorted_dists = [d for d in sorted_dists if d.version]
        if len(sorted_dists) > 1:
            sorted_dists = [e
                            for e in sorted_dists
                            if first_digit_re.match(e.version)
                           ]
            if len(sorted_dists) == 1:
                dists = sorted_dists
    return dists[0]

def merge_extras(a, b):
    a.extras += b.extras
    a.extras = tuple(set(a.extras))
    return a

def merge_specs(a, b):
    a.specs += b.specs
    a.specs = list(set(a.specs))
    return a

def redo_pyc(egg, executable=sys.executable, environ=os.environ):
    #print "Location : %s" % egg
    logger = logging.getLogger('minitage.recipe PyCompiler')
    if not os.path.isdir(egg):
        return

    # group sort, and uniquify files to compile
    files = {}
    for dirpath, dirnames, filenames in os.walk(egg):
        ffilenames = [filename for filename in filenames if filename.endswith('.py')]
        if dirpath in files:
            files[dirpath] += ffilenames
        else:
            files[dirpath] = ffilenames

    tocompile = []
    for dirpath in files:
        for filename in tuple(set(files[dirpath])):
            filepath = os.path.join(dirpath, filename)
            # OK, it looks like we should try to compile.
            # Remove old files.
            for suffix in 'co':
                if os.path.exists(filepath+suffix):
                    os.remove(filepath+suffix)
            tocompile.append(filepath)

    try:
        # Compile under current optimization
        args = [zc.buildout.easy_install._safe_arg(sys.executable)]
        if sys.platform.startswith('win'):
            args = [sys.executable]
        args.extend(['-m', 'py_compile'])
        subprocess.Popen(args+tocompile, env=environ).wait()
        if __debug__:
        # Recompile under other optimization. :)
            args.insert(1, '-O')
            subprocess.Popen(args+tocompile, env=environ).wait()
    except py_compile.PyCompileError, error:
        logger.warning("Couldn't compile %s", filepath)

class EggPatchError(Exception):
    """."""

class EasyInstallError(core.MinimergeError):

    def __init__(self, *args, **kwargs):
        core.MinimergeError(self, *args)
        self.failed_dist = kwargs.get('dist', None)
        self.failed_specs = kwargs.get('specs', None)
        self.failed_working_set = kwargs.get('working_set', None)
        self.failed_prefix = kwargs.get('prefix', None)

def dependency_resolver_decorator(f):
    def callback(self, *args, **kwargs):
        ret = None
        try:
            ret = f(self, *args, **kwargs)
        #except IncompatibleVersionError, e:
        #    print e.args[2]
        #    raise e
        except pkg_resources.VersionConflict, e:
            idist, req = e.args
            if self.logger.getEffectiveLevel() <= logging.DEBUG:
                self.print_dependency_tree()
            print
            print '* Eggs depending on %s (requirement):' % req
            for i in self.dependency_tree.get(req, []):
                dist = self.dependency_tree[req][i]
                print "    * %s %s (%s)" % (dist.project_name, dist.version, self.get_dist_location(dist))
            #print "* Eggs depending on %s (already installed distribution):" % (dist.as_requirement())
            print "This conflicting installed distribution %s %s is installed in %s." % (
                idist.project_name, idist.version, self.get_dist_location(idist)
            )

            # by project_name
            selector = idist.project_name
            dreqs = self.dependency_tree.get(pkg_resources.Requirement.parse(selector), [])
            selector = idist.as_requirement()
            if idist.version and not (idist.version == '0.0'):
                # filter by version
                dreqs = self.dependency_tree.get(selector, [])
            for i in dreqs:
                dist = self.dependency_tree[selector][i]
                print "    * %s %s (%s)" % (dist.project_name, dist.version, self.get_dist_location(dist))
            print
            print
            raise e
        except EasyInstallError, e:
            dist = e.failed_dist
            specs = e.failed_specs
            if dist:
                print "Easy_install failed on some distribution:"
                if dist:
                    print "    - Failed dist: %s" %  dist.as_requirement()
            if len(specs) == 1:
                fd = get_first_dist(specs[0])
                if fd:
                    # print up to level6 dependencies
                    req = fd.as_requirement()
                    print "    - Failed specs: %s" %  fd.as_requirement()
                    reqs = self.print_requirement_for(req)
                    for r in reqs:
                        rreqs = self.print_requirement_for(r)
                        for rr in rreqs:
                            rrreqs = self.print_requirement_for(rr)
                            for rrr in rrreqs:
                                rrrreqs = self.print_requirement_for(rrr)
                                for rrrr in rrrreqs:
                                    rrrrreqs = self.print_requirement_for(rrrr)
                                    for rrrrr in rrrrreqs:
                                        rrrrreqs = self.print_requirement_for(rrrrr)
            raise e
        except Exception, e:
            self.logger.error(traceback.format_exc())
            raise e
        return ret
    return callback



class Recipe(common.MinitageCommonRecipe):
    """
    Downloads and installs a distutils Python distribution.
    """
    def platform_scan(self):
        """Atm, its only used on mac,
        if the targeted python platform is different from the buildout running
        process, we will take that into account and reload the Environements
        according to those values
        """
        if self.executable_platform:
            # reset the platform according to the targeted python
            self.inst._env.platform = self.executable_platform
            self.inst._index.platform = self.executable_platform
            # redo a proper distributions scan
            self.inst._env.scan(self.eggs_caches)
            self.inst._index.scan(self.eggs_caches)

    def print_requirement_for(self, req):
        reqs, rreqs = {}, []
        # not versionnned requirement
        altreq = pkg_resources.Requirement.parse(req.project_name)
        try:
            reqs = self.dependency_tree[req]
        except:
            try:
                reqs = self.dependency_tree[altreq]
            except:
                pass

        if isinstance(reqs, dict):
            reqs = reqs.values()
        for r in reqs:
            if isinstance(r, pkg_resources.Distribution):
                rreqs.append(r.as_requirement())
            else:
                rreqs.append(r)
        if rreqs:
            print "    - required by: "
            print "        - %s" % rreqs
        return rreqs

    def print_dependency_tree(self):
        if self.dependency_tree:
            print
            print "* Full dependencies mapping:"
            keys = self.dependency_tree.keys()
            def asort(a, b):
                if a.project_name > b.project_name:
                    return 1
                if a.project_name == b.project_name:
                    return 0
                if a.project_name <  b.project_name:
                    return -1
            keys.sort(asort)
            for key in keys:
                print "%s is required by:" % self._constrain_requirement(key)
                for i in self.dependency_tree[key]:
                    dist = self.dependency_tree[key][i]
                    print "  * %s %s (%s)" % (dist.project_name, dist.version, self.get_dist_location(dist))

    def get_bdist_ext_options(self, distname):
        build_ext_options = self.build_ext_options.copy()
        for be_option in ('define', 'undef', 'libraries', 'link-objects',
                          'debug', 'force', 'compiler', 'swig-cpp', 'swig-opts',
                          ):
            value = self.options.get('%s-%s' % (distname, be_option))
            if value is None:
                continue
            self.logger.debug('%s: Using bdist_ext option: %s = %s' % (distname, be_option, value))
            build_ext_options[be_option] = value

        bdistext = '%s-%s' % (distname, self.bdistext)
        for be_option in [o for o in self.options if o.startswith(bdistext)]:
            option = be_option.replace(bdistext, '')
            value = self.options.get(be_option)
            self.logger.debug('%s: Using bdist_ext option: %s = %s' % (distname, option, value))
            build_ext_options[option] = value
        return  build_ext_options

    def __init__(self, buildout, name, options):
        self.sav_environ = copy.deepcopy(os.environ)
        common.MinitageCommonRecipe.__init__(self,
                                    buildout, name, options)
        # override recipe default and download into a subdir
        # minitage-cache/eggs
        # separate archives in downloaddir/minitage
        self.lastlogs = []
        self.dependency_tree = {}
        options['bin-directory'] = buildout['buildout']['bin-directory']
        self.download_cache = os.path.abspath(
            os.path.join(self.download_cache, 'eggs')
        )

        build_ext_options = {}
        swig = options.get('swig')
        if swig:
            options['swig'] = build_ext_options['swig'] = os.path.join(
                buildout['buildout']['directory'],
                swig,
            )

        for be_option in ('define', 'undef', 'libraries', 'link-objects',
                          'debug', 'force', 'compiler', 'swig-cpp', 'swig-opts',
                          ):
            value = options.get(be_option)
            if value is None:
                continue
            self.logger.debug('Using bdist_ext option: %s = %s' % (be_option, value))
            build_ext_options[be_option] = value

        self.bdistext = 'bdistext-'
        for be_option in [o for o in self.options if o.startswith(self.bdistext)]:
            option = be_option.replace(self.bdistext, '')
            value = options.get(be_option)
            self.logger.debug('Using bdist_ext option: %s = %s' % (option, value))
            build_ext_options[option] = value
        self.build_ext_options = build_ext_options

        if not os.path.isdir(self.download_cache):
            os.makedirs(self.download_cache)

        self.extra_paths = [
            os.path.join(buildout['buildout']['directory'], p.strip())
            for p in options.get('extra-paths', '').split('\n')
            if p.strip()
            ]

        # cleanup bad comments in buildout !
        if 'versions' in self.buildout:
            for k in self.buildout['versions']:
                v = self.buildout['versions'][k].strip()
                m = version_comment_remover_re.match(v)
                if m:
                    self.buildout['versions'][k] = m.groupdict()['version']

        self.versions = buildout.get(
            buildout['buildout'].get('versions', '').strip(),
            {}
        )
        self.buildout_versions = buildout['buildout'].get('versions', '').strip()
        if not self.buildout_versions in buildout:
            self.buildout_versions = None
        # compatibility with zc.recipe.egg:
        relative_paths = options.get(
            'relative-paths',
            buildout['buildout'].get('relative-paths', 'false')
        )
        if relative_paths == 'true':
            options['buildout-directory'] = buildout['buildout']['directory']
            self._relative_paths = options['buildout-directory']
        else:
            self._relative_paths = ''
        # end compat

        # caches
        self.eggs_directory = buildout['buildout']['eggs-directory']
        self.eggs_caches = [
            buildout['buildout']['develop-eggs-directory'],
            buildout['buildout']['eggs-directory'],
        ]

        # add distutils or dirty packages too.
        self.eggs_caches.extend(
            self.minitage_eggs
        )

        # real eggs
        self.eggs = [i\
                     for i in self.options.get('eggs', '').split('\n')\
                     if i]

        self.eggs += [i\
                     for i in self.options.get('egg', '').split('\n')\
                     if i]
        if not self.eggs:
            eggs = [name]
        # findlinks for eggs
        self.install_previous_version = self.options.get('install-previous-version', '')
        self.find_links = splitstrip(self.options.get('find-links', ''))
        self.find_links += splitstrip(self.buildout['buildout'].get('find-links', ''))

        #index replacement
        self.index = self.options.get('index',
                                     self.buildout['buildout'].get('index', None)
                                     )

        # zip flag for eggs
        self.zip_safe = False
        if self.options.get('zip-safe', 'true'):
            self.zip_safe = True

        # sharing env with Installer for performance optimization
        #self._env = pkg_resources.Environment(
        #    self.eggs_caches,
        #    python=self.executable_version
        #)

        # monkey patch zc.buildout loggging
        self.logger.setLevel(
            zc.buildout.easy_install.logger.getEffectiveLevel()
        )
        zc.buildout.easy_install.logger = self.logger

        # get an instance of the zc.buildout egg installer
        # to search in the cache if we dont have dist yet
        # and etc.
        if self.offline:
            self.index = 'file://%s' % self.eggs_caches[0]
            self.find_links = []
            self.options['allow-hosts'] = 'None'
            self.buildout['buildout']['allow-hosts'] = 'None'
            self.buildout._allow_hosts = ('None',)


        # on darwin, you can easily have a supported platform different from
        # the one you ran buildout with
        # example -> macosx-flat -> macosx-i386
        # to avoid mismatch and recusions bugs, we will test both
        # we also need in this case to patch tthe Installer object for its
        # environment to know the targeted envionment
        self.executable_platform = None

        zc.buildout.easy_install.Installer._download_cache = self.download_cache
        zc.buildout.easy_install.Installer._always_unzip = True
        if not os.path.isdir(self.executable_prefix):
             message = 'Python seems not to find its prefix : %s' % self.executable_prefix
             self.logger.warning(message)
        else:
            self.inst = zc.buildout.easy_install.Installer(
                dest=None,
                index=self.index,
                links=self.find_links,
                executable=self.executable,
                always_unzip=self.zip_safe,
                versions=self.buildout.get('versions', {}),
                path=self.eggs_caches,
                newest = self.buildout.newest,
                allow_hosts=self.options.get('allow-hosts',
                                             self.buildout.get('allow-hosts', {})
                                             ),
            )

            self.platform_scan()

            # FORCING NEWEST MODE !!! see Installer code...
            self.inst._newest = self.buildout.newest
            self._dest= os.path.abspath(
                self.buildout['buildout']['eggs-directory']
            )

            # intiatiate environement cache
            self.scan()
            self.already_installed_dependencies = {}

            # distribute/setuptools support.
            # add them to sys.path tfor python find them at run time if they
            # are in the cache and not in the site-packages.
            self.HAS_DISTRIBUTE = False
            self.HAS_SETUPTOOLS = False
            self.has_distribute()
            if not self.HAS_DISTRIBUTE:
                self.has_setuptools()
            if not self.HAS_DISTRIBUTE and not self.HAS_SETUPTOOLS:
                self.install_distribute()

    def install_distribute(self):
        self.logger.debug('Installing distribute for the targeted python')
        tfile = tempfile.mkstemp()[1]
        ppath = os.environ.get('PYTHONPATH', '')
        os.environ['PYTHONPATH'] = ''
        open(tfile, 'w').write(
            BOOTSTRAP_DISTRIBUTE_SCRIPT% {'destination':
                                          self.eggs_directory}
        )
        ret = subprocess.Popen([self.executable, tfile]).wait()
        os.environ['PYTHONPATH'] = ppath
        if not ret == 0:
            raise Exception('Cannot install distribute!')
        self.has_distribute()

    def has_distribute(self):
        """Check if distribute is present for our targeted python."""
        if not self.HAS_DISTRIBUTE:
            try:
                self.scan()
                dist, avail = self.inst._satisfied(
                    pkg_resources.Requirement.parse('distribute')
                )
                if dist:
                    self.HAS_DISTRIBUTE = True
                    self.extra_paths.append(dist.location)
                    self.logger.debug('Using distribute!')
            except:
                self.logger.warning('You are using the old setuptools, maybe you '
                                    'should upgrade to distribute.')
        return self.HAS_DISTRIBUTE

    def has_setuptools(self):
        """Check if setuptools is present for our targeted python."""
        if not self.HAS_SETUPTOOLS:
            try:
                dist, avail = self.inst._satisfied(
                    pkg_resources.Requirement.parse('setuptools')
                )
                if dist:
                    self.HAS_SETUPTOOLS = True
                    self.extra_paths.append(dist.location)
                    self.logger.debug('Using setuptools!')
            except:
                self.logger.warning('You should either install distribute or'
                                    ' setuptools inside your python.')
        return self.HAS_SETUPTOOLS


    def update(self):
        """update."""
        self.install()

    @dependency_resolver_decorator
    def install(self):
        """installs an egg
        """
        try:
            reqs, working_set = self.working_set()
        except Exception, e:
            self.logger.error('Installation error.')
            self.logger.error('Message was:\n\t%s' % e)
        return []

    @dependency_resolver_decorator
    def working_set(self, extras=None, working_set=None, dest=None):
        """real recipe method but renamed for convenience as
        we do not return a path tuple but a workingset
        """
        if not os.path.isdir(self.executable_prefix):
             message = 'Python seems not to find its prefix : %s' % self.executable_prefix
             self.logger.warning(message)
        if self.uname == 'darwin':
            osx_platform = pkg_resources.get_supported_platform()
            sget_supported_patform = '%s' % (
                'from pkg_resources import get_supported_platform;'
                'print get_supported_platform()'
            )
            self._set_compilation_flags()
            env = copy.deepcopy(os.environ)
            p = subprocess.Popen(
                [self.executable, '-c',
                 sget_supported_patform],
                env = env,
                stdout = subprocess.PIPE,
                stdin = subprocess.PIPE,
            )
            p.wait()
            sp = p.stdout.read().replace('\n', '')
            if sp != osx_platform:
                self.executable_platform = sp 

        self.logger.info('Installing python egg(s).')
        # rescan, there may be develop eggs newly installed after init
        self.scan()
        requirements = None
        if not extras:
            extras = []
        elif isinstance(extras, tuple):
            extras = list(extras)

        if not dest:
            dest = self._dest

        for i, r in enumerate(copy.deepcopy(extras)):
            if not isinstance(r, pkg_resources.Requirement):
                extras[i] = pkg_resources.Requirement.parse(r)

        # initialise working directories
        if not os.path.exists(self.tmp_directory):
            os.makedirs(self.tmp_directory)
        # get the source distribution url for the eggs
        # if we have urls
        # downloading each, scanning its stuff and giving it to easy install
        requirements, working_set = self.install_static_distributions(working_set,
                                                                      requirements=requirements,
                                                                      dest=dest)
        # install static distributions dependencies as well
        if requirements:
            extras.extend(requirements)
        # installing classical requirements
        if self.eggs or extras:
            drequirements, working_set = self._install_requirements(
                self.eggs + extras,
                dest,
                working_set=working_set)

            requirements.extend(drequirements)
        # cleaning stuff
        if os.path.isdir(self.tmp_directory):
            shutil.rmtree(self.tmp_directory)

        if not dest in self.eggs_caches:
            self.eggs_caches.append(dest)

        # old code, keeping atm
        #env = pkg_resources.Environment(self.eggs_caches,
        #                                python=self.executable_version)

        if self.lastlogs:
            self.logger.info('-------------------------------------------------------')
            for log in self.lastlogs:
                self.logger.info(log)
            self.logger.info('-------------------------------------------------------')
        return ['%s' % r for r in requirements], working_set

    @dependency_resolver_decorator
    def install_static_distributions(self,
                                     working_set=None,
                                     urls=None,
                                     requirements=None,
                                     dest=None):
        """Install distribution distribued somewhere as archives."""
        if not working_set:
            working_set = pkg_resources.WorkingSet([])
        if not requirements:
            requirements = []
        if not dest:
            dest = self._dest
        # downloading
        if not urls:
            urls = self.urls
        dists = []
        for i, url in enumerate(urls):
            fname = self._download(url=url, cache=True)
            bfname = os.path.basename(fname)
            # if it is a repo, making a local copy
            # and scan its distro
            if os.path.isdir(fname):
                self._call_hook('%s-post-download-hook'%bfname, fname)
                tmp = os.path.join(self.tmp_directory, os.path.basename(fname))
                f = IFetcherFactory(self.minitage_config)
                for fetcher in f.products:
                    dot = getattr(f.products[fetcher](),
                                  'metadata_directory', None)
                    if dot:
                        if os.path.exists(os.path.join(fname, dot)):
                            shutil.copytree(fname, tmp)
                            break
                # go inside dist and scan for setup.py
                self.options['compile-directory'] = tmp
                if os.path.isdir(tmp):
                    self._call_hook('%s-post-checkout-hook'%bfname, tmp)
                # build the egg distribution in there.
                self._sanitizeenv(working_set)
                # recursivly easy installing dependencies
                ez = easy_install.easy_install(distutils.core.Distribution())
                oldcwd = os.getcwd()
                # generating metadata for source distributions
                #
                _, _, _, directory, _ = common.divide_url(url)
                if not directory:
                    directory = self.urls.get(url, {}).get('directory', '')
                if directory:
                    if not os.path.exists(directory):
                        directory = ''
                sdist_files = []
                try:
                    os.chdir(tmp)
                    if directory:
                        self.logger.debug('Going into subdir: %s' % directory)
                        os.chdir(directory)
                    sdist_args = '-q'
                    if not os.path.isfile('setup.py'):
                        raise Exception('Invalid distribution in %s'
                                        ' . No setup.py.' % tmp)
                    sdist_post_args = '2>&1 >> /dev/null'
                    if self.logger.getEffectiveLevel() <= logging.DEBUG:
                        sdist_args, sdist_post_args = '', ''

                    ret = os.system('%s setup.py %s sdist %s' % (sys.executable, sdist_args, sdist_post_args))
                    sdist_files = [os.path.join(tmp, 'dist', a) for a in os.listdir('dist')]
                except Exception, e:
                    self.logger.error('sdist in %s failed' % os.getcwd())
                    raise
                os.chdir(oldcwd)
                # repackage the checkout as a dist.
                if sdist_files:
                    nd = get_first_dist(sdist_files[0])
                    tempdir = tempfile.mkdtemp()
                    ttar = os.path.join(
                        tempdir, '%s-%s.%s' % (nd.project_name,
                                              nd.version,
                                              'tar.gz'
                                             )
                    )
                    tar = tarfile.open(ttar, mode='w:gz')
                    root = tmp
                    if directory:
                        root = os.path.join(root, directory)
                    tar.add(root, nd.project_name)
                    tar.close()
                    dist = get_first_dist(ttar)
                    req = dist.as_requirement()
                    self.append(req, dist, dists)
            else:
                # scan for the distribution archive infos.
                dist = get_first_dist(fname)
                req = dist.as_requirement()
                self.append(req, dist, dists)

            # sort duplicates
            paths = []
            toinstall = []
            for dist in dists:
                if not self.get_dist_location(dist) in [self.get_dist_location(d)\
                                         for d in toinstall]:
                    toinstall.append(dist)

            for dist in toinstall:
                requirement = None
                if dist.version:
                    requirement = pkg_resources.Requirement.parse(
                        '%s == %s' % (dist.project_name, dist.version)
                    )
                else:
                    requirement = pkg_resources.Requirement.parse(
                        dist.project_name
                    )
                # force env rescanning if egg was not there at init.
                self.scan([dest])
                sdist, savail = None, None
                try:
                    sdist, savail, _ = self._satisfied(requirement, working_set)
                except zc.buildout.easy_install.MissingDistribution:
                    pass
                except zc.buildout.easy_install.IncompatibleVersionError, e:
                    # case of already installed patched dists:
                    if PATCH_MARKER in "%s" % e:
                        # finding the version arguments
                        version = '0'
                        for arg in e.args:
                            if PATCH_MARKER in arg:
                                version = arg
                        requirement = pkg_resources.Requirement.parse(
                                        '%s == %s' % (dist.project_name, version)
                                        )
                        try:
                            # version already pinned in the buildout, with the
                            # patched bits, but the egg isnt already installed
                            # in the egg cache
                            sdist, savail, _ = self._satisfied(requirement, working_set)
                        except zc.buildout.easy_install.MissingDistribution:
                            pass
                    else:
                        raise
                if sdist:
                    msg = 'If you want to rebuild, please do \'rm -rf %s\''
                    self.logger.debug(msg % self.get_dist_location(sdist))
                    sdist.activate()
                    # for buildout to use it !
                    working_set.add(sdist)
                    requirements.append(sdist.as_requirement())
                    self._pin_version(sdist.project_name, sdist.version)
                    self.versions[sdist.project_name] = sdist.version
                    self.add_dist(sdist)
                    self.logger.info(
                        'Activated %s %s (%s).' % (
                            dist.project_name,
                            dist.version,
                            self.get_dist_location(sdist)
                        )
                    )
                else:
                    if not self.already_installed_dependencies:
                        self.already_installed_dependencies = {}
                    for r in requirements:
                        self.already_installed_dependencies[r.project_name] = r
                    installed_dist = self._install_distribution(dist, dest, working_set)
                    installed_dist.activate()
                    # for buildout to use it !
                    working_set.add(installed_dist)
                    requirements.append(installed_dist.as_requirement())
                    self._pin_version(installed_dist.project_name, installed_dist.version)
                    self.versions[installed_dist.project_name] = installed_dist.version
                    self.add_dist(installed_dist)
                    # be sure to have the really installed dist requiremen'ts bits
                    self.already_installed_dependencies[installed_dist.project_name] = installed_dist.as_requirement()
        return requirements, working_set

    def scan(self, scanpaths=None):
        if not scanpaths:
            scanpaths = self.eggs_caches
        self.inst._env.scan(scanpaths)


    def make_env(self, search_path=None, platform=None, python=None):
        """Make a pkg_resources Environment instance while
        honnouring the following attributes

            - self.executable_platform
            - self.executable_version

        """
        args = []
        kwargs = {}
        args.append(search_path)
        if platform:
            kwargs['platform'] = platform
        elif self.executable_platform:
            # honour self.executable_platform if any
            kwargs['platform'] = self.executable_platform

        if python:
            kwargs['python'] = python
        elif self.executable_version:
            # honour self.executable_version if any
            kwargs['python'] = self.executable_version
        env = pkg_resources.Environment(
            *args, **kwargs
        )
        return env

    def _search_sdists(self, requirement, working_set, multiple=True):
        sreq = '%s' % requirement
        env = self.make_env([self.download_cache])
        avail, sdists = None, []
        dist = None
        results = []
        # try to scan source distribtions
        for file in os.listdir(self.download_cache):
            path = os.path.join(self.download_cache, file)
            if os.path.isfile(path):
                dists = [d
                         for d in setuptools.package_index.distros_for_url(path)]
                if len(dists) > 1:
                    dists = [ d for d in dists if d.version]
                sdists.extend(dists)
        for distro in sdists:
            env.add(distro)
        # last try, testing sources (very useful for offline mode
        # or when your egg is not indexed)
        # if we have a patched egg, searching for the egg first, then for the sdist that can build it
        avail = env.best_match(requirement, working_set)
        if not avail and PATCH_MARKER in sreq:
            requirement = pkg_resources.Requirement.parse(orig_versions_re.sub('', sreq))
            avail = env.best_match(requirement, working_set)
        if avail:
            if avail.precedence  == pkg_resources.SOURCE_DIST:
                results.append(avail)
        if (not results) or multiple:
            # maybe we can get one on the available indexes !
            # if we have a patched egg, searching for the egg first, then for the sdist that can build it
            try:
                availables = self.inst._index[requirement.key]
                matching_sdists = [sdist
                                   for sdist in availables
                                   if sdist.precedence == pkg_resources.SOURCE_DIST
                                   and (sdist in requirement)]
                def md5sort(x):
                    p = urlparse.urlparse(self.get_dist_location(x))
                    # tuple in python2.4
                    if not isinstance(p, tuple):
                        p = tuple(p)
                    if 'md5=' in p[-1]:
                        return 0
                    return 1
                sorted_dict, keys = {}, []
                # order dists from last version with preferrence for md5 urls
                def version_compare(x, y):
                   if pkg_resources.parse_version(x)  > pkg_resources.parse_version(y):
                      return -1
                   elif pkg_resources.parse_version(x) == pkg_resources.parse_version(y):
                      return 0
                   else:
                      return 1
                if matching_sdists:
                    for sdist in matching_sdists:
                        key = '%s' % sdist.version
                        sorted_dict.setdefault(key, [])
                        sorted_dict[key].append(sdist)
                    keys = sorted_dict.keys()
                    for key in sorted_dict:
                        sorted_dict[key].sort(key=md5sort)
                    keys.sort(version_compare)
                    if not multiple:
                        availables = [matching_sdists[0]]
                    noecho = [results.extend(sorted_dict[key]) for key in keys]
            except Exception, e:
                pass
            if not results:
                raise zc.buildout.easy_install.MissingDistribution(
                    requirement, working_set
                )
        if results:
            for avail in results:
                msg = 'We found a source distribution for \'%s\' in \'%s\'.'
                self.logger.info(msg % (requirement, self.get_dist_location(avail)))
        return results

    def _search_sdist(self, requirement, working_set, multiple=False):
        res = self._search_sdists(requirement, working_set, multiple=False)
        if res:
            return res[0]

    def _satisfied(self, requirement, working_set):
        # be sure to honnour versions restrictions
        requirement = self._constrain_requirement(requirement)
        # if we are in online mode, trying to get the latest version available
        candidate = None
        # first try with what we have in binary form
        try:
            dist, avail = self.inst._satisfied(requirement)
        except zc.buildout.easy_install.MissingDistribution:
            # force env rescanning if egg was not there at init.
            self.scan([self._dest])
            dist, avail = self.inst._satisfied(requirement)
        search_new = self.buildout.newest
        if dist:
            if dist.precedence == pkg_resources.DEVELOP_DIST:
                search_new = False
        # do not search newer when we already have '==' in requirement :)
        # neweer thab ==1.0 ==> 1.0 and searching is just a no-op!
        if '==' in '%s' % requirement:
            search_new = False
        if search_new:
            candidate = self.inst._obtain(requirement)
        if candidate:
            if avail:
                if candidate.version > avail.version:
                    avail = candidate
            if dist:
                if candidate.version > dist.version:
                    avail = candidate
                    dist = None
        if not dist:
            if avail is None:
                # try to found a sdist, but do not stop there,
                # this art can call other ones
                try:
                    avail = self._search_sdist(requirement, working_set)
                except zc.buildout.easy_install.MissingDistribution:
                    # just mark the dist as missing.
                    avail = None

        # there we have dist or avail setted, weither the egg is alredy installed
        # both can be null is nothing is installed or downloaded right now.
        # In this case, we just have the requirement available
        v, patched_egg = get_requirement_version(requirement)
        patches = []
        # Try to get the possibles patch for the project if this is the relevant
        # v can be wrong atm,if the requirement is not yet pinned to the patched
        # version !!!

        v, _, _, patches, patched_bits = self._get_dist_patches(requirement.project_name, v)

        # leads to bugs in buildout behaviour if we read things we didnt have to ;'(
        # if this is a minitage patched egg, there is a chance that the
        # part which build the egg was not built yet.
        # We will try to find and run it!
        #if (not patches) and patched_egg:
        #    for spart in self.buildout:
        #        part = self.buildout[spart]
        #        if 'recipe' in part:
        #            for option in part:
        #                if option.startswith(requirement.project_name) \
        #                and ('patch' in option):
        #                    v, _, _, patches, _ = self._get_dist_patches(
        #                        requirement.project_name,
        #                        v,
        #                        part)
        #                    # we found the part with the set of patches  :D
        #                    if patches:
        #                        self.logger.info(
        #                            "Althought [%s] doesn't provide "
        #                            "appropriate patches for %s, we found "
        #                            "[%s] which provide them, "
        #                            "running it!" %(
        #                                self.name, requirement, part.name
        #                            )
        #                        )
        #                        self.buildout._install(part.name)
        #                        break

        if len(patches):
            sv = '%s' % v
            if sys.platform.startswith('win'):
                sv = sv.lower()
            if PATCH_MARKER in sv:
                self.inst._versions[requirement.project_name] = sv
            # forge the patched requirement reporesentation
            # if we cant determine the version from the requirement, it was not
            # already patched, we must have a distribution or an available
            # source distribution to get the version from
            # Note that from the distribution, it canbe alraedy patched ;)
            if not get_orig_version(v):
                for project in dist, avail:
                    if project:
                        sproject_version = project.version
                        if sys.platform.startswith('win'):
                            sproject_version = sproject_version.lower()
                        if PATCH_MARKER in sproject_version:
                            v = sproject_version
                        else:
                            v = "%s-%s" % (sproject_version, patched_bits)
                            break
            requirement = pkg_resources.Requirement.parse(
                "%s==%s" % (
                    requirement.project_name, v
                )
            )
            # only install sdist !
            sdist = avail
            if avail:
                if avail.precedence != pkg_resources.SOURCE_DIST:
                    sdist = None
            # Do we have a compiled distribution of the egg yet?
            dist, pavail = self.inst._satisfied(requirement)
            if dist:
                v = dist.version
                avail = None
            # now, in the 2 cases: we ran another part or the part itself.
            # But in all cases, we have feeded our patches list !
            # But we may not have installed yet the egg!
            elif sdist is None:
                # do we come from elsewhere, in the contrary,
                # We are in the case where install the egg
                try:
                    avail = self._search_sdist(requirement,
                                               working_set)
                except zc.buildout.easy_install.MissingDistribution, e:
                    # if this is a minitage patched egg, there is a chance that the
                    # part which build the egg was not built yet.
                    # in this case, we try to find the egg without the patched
                    # version bits.
                    # The other case is when you have already fixed the
                    # version on the buildout, but you dont have already the
                    # egg, its just to be cool with users as we know how to
                    # do this egg, anyhow :)
                    version, patched_egg = get_requirement_version(requirement)
                    if patched_egg:
                        try:
                            requirement = pkg_resources.Requirement.parse(
                                    "%s==%s" % (
                                        requirement.project_name, get_orig_version(v)
                                    )
                                )
                        except Exception, e:
                            # egg without fixed version needing patch
                            # we remove the patch bit appended to version
                            if version.startswith(PATCH_MARKER) or not version:
                                requirement = pkg_resources.Requirement.parse(
                                    requirement.project_name
                                )
                            else:
                                raise
                        avail = self._search_sdist(requirement, working_set)
                        requirement = pkg_resources.Requirement.parse('%s==%s' % (requirement.project_name, v))
        # Mark buildout, recipes and installers to use our specific egg!
        # Even, if we have already installed, in case user or something else
        # removed it!
        if v and patches:
            self._pin_version(requirement.project_name, v)
        # We may have not found the distribution
        if (not dist) and (not avail):
            raise zc.buildout.easy_install.MissingDistribution(
                requirement, working_set)
        return dist, avail, requirement

    def _pin_version(self, name, version):
        sysargv = sys.argv[:]
        fconfig = 'buildout.cfg'
        # determine which buildout config has been run
        while sysargv:
            try:
                arg = sysargv.pop(0)
                if re.match('-.*c', arg):
                    fconfig = sysargv.pop()
                    break
            except IndexError:
                fconfig = 'buildout.cfg'
        cfg = os.path.join(self.buildout._buildout_dir, fconfig)
        # patch runtime objects to fix version
        if self.buildout_versions:
            self.buildout[self.buildout_versions][name] = version
        self.versions[name] = version
        self.inst._versions[name] = version
        requirement = pkg_resources.Requirement.parse( '%s==%s' % (name, version))
        if not os.path.exists(cfg):
            self.logger.error(
                'It seems you are not using buildout.cfg'
                ' as configuration file, as we have no'
                ' mean to determine the bIuldout config file at runtime,\n'
                'you ll have to fix the version your self by adding : \n'
                '[buildout]\n'
                'extends = customversions.cfg')
            cfg = os.path.join(self.buildout._buildout_dir, 'customversions.cfg')

        versions_part = self.buildout.get('buildout', {}).get('versions', 'versions')
        config = ConfigParser.ConfigParser()
        try:
            self.logger.debug('Pinning custom egg version in buildout, trying to write the configuration')
            config.read(cfg)
            if not config.has_section('buildout'):
                config.add_section('buildout')
            config.set('buildout', 'versions', versions_part)
            if not config.has_section(versions_part):
                config.add_section(versions_part)
            existing_version = None
            try:
                existing_version = config.get(versions_part, name).strip()
            except NoOptionError:
                pass
            # only if version changed
            if existing_version != version:
                config.set(versions_part, requirement.project_name, version)
                backup_base = os.path.join(self.buildout._buildout_dir,
                                      '%s.before.fixed_version.bak' % fconfig)
                #index = 0
                backup = backup_base
                #while os.path.exists(backup):
                #    index += 1
                #    backup = '%s.%s' % (backup_base, index)
                self.logger.debug('CREATING buildout backup in %s' % backup)
                shutil.copy2(cfg, backup)
                config.write(open(cfg, 'w'))
            else:
                self.logger.debug('Version already pinned, nothing has been wroten.')
        except Exception, e:
            self.logger.error('Cant pin the specific versions for %s\n%s' % (requirement, e))

    def _constrain(self, requirements, fromdist=None):
        constrained_requirements = {}
        for requirement in requirements:
            if not isinstance(requirement, pkg_resources.Requirement):
                requirement = pkg_resources.Requirement.parse(requirement)
            sreq = '%s' % requirement
            try:
                # buildout fixed version is more important than setup.py fixed ones!
                if re.search('.*(==|>=|<=).*', sreq):
                    vmapping = dict([(a.lower(),a) for a in self.versions])
                    if requirement.project_name.lower() in vmapping:
                        oldreq = requirement
                        requirement = self.inst._constrain(
                            pkg_resources.Requirement.parse(
                                vmapping.get(
                                    requirement.project_name.lower()
                                )
                            )
                        )
                        requirement.extras = oldreq.extras
                constrained_req = self.inst._constrain(requirement)
            except zc.buildout.easy_install.IncompatibleVersionError, e:
               if fromdist:
                   msg = '\n\n'
                   msg += '-' * 80 + '\n'
                   msg += '!!! Installing buildout fixed version even if packagers pin something else in their setup.py by hand !!!\n'
                   msg += 'Buildout fixed version "%s==%s" is not consistent with the requirement "%s".\n%s' % (
                       requirement.project_name,
                       e.args[1],
                       requirement,
                       'Required by %s-%s (%s)\n' % (fromdist.project_name, fromdist.version, self.get_dist_location(fromdist))
                   )
                   msg += '-' * 80 + '\n'
                   if not msg in self.lastlogs:
                       self.lastlogs.append(msg)
                   constrained_req = self.inst._constrain(pkg_resources.Requirement.parse(requirement.project_name))
               elif requirement.project_name in self.versions:
                   msg = '\n\n'
                   msg += '-' * 80 + '\n'
                   msg += '!!! Installing buildout fixed version even if packagers pin something else in their setup.py by hand !!!\n'
                   msg += 'Buildout fixed version "%s==%s" is not consistent with the requirement "%s".\n' % (
                       requirement.project_name,
                       e.args[1],
                       requirement,
                   )
                   msg += '-' * 80 + '\n'
                   if not msg in self.lastlogs:
                       self.lastlogs.append(msg)
                   constrained_req = self.inst._constrain(pkg_resources.Requirement.parse(requirement.project_name))
               else:
                   raise e
            r = constrained_requirements.get(requirement.project_name,
                                             constrained_req)
            # constrain doesnt conserve extras :::
            r = merge_extras(r, requirement)
            # if an egg has precised some version stuff not controlled by
            # our version.cfg, let it do it !
            if not r.specs:
                r = merge_specs(r, requirement)
            constrained_requirements[r.project_name] = r
            # construct the patch version bits
            _, _, _, patches, patch_bits = self._get_dist_patches(requirement.project_name, None)
            if len(patches):
                # only construct if we have fixed versions:
                rstr = '%s' % r
                if '==' in rstr and not PATCH_MARKER in rstr:
                    for i, s in enumerate(r.specs):
                        vpatch, version = False, ''
                        if s[0] == '==':
                            if s[1]:
                                if not PATCH_MARKER in s[1]:
                                    version = '%s-%s' % (s[1], patch_bits)
                                    vpatch = True
                        if vpatch:
                            r.specs[i] = ('==', version)
        return constrained_requirements.values()

    def _constrain_requirement(self, requirement, fromdist=None):
        return self._constrain([requirement], fromdist)[0]

    def filter_already_installed_requirents(self, requirements):
        items = []
        constrained_requirements = self._constrain(requirements)
        installed_requirements = self.already_installed_dependencies.values()
        if self.already_installed_dependencies:
            for requirement in constrained_requirements:
                similary_req = self.already_installed_dependencies.get(requirement.project_name, None)
                found = True
                if not similary_req:
                    found = False
                else:
                    if requirement.extras and (similary_req.extras != requirement.extras):
                        found = False
                        requirement = merge_extras(requirement, similary_req)
                    # if an egg has precised some version stuff not controlled by
                    # our version.cfg, let it do it !
                    if requirement.specs and (not similary_req.specs):
                        found = False
                if not found:
                    items.append(requirement)
                    # something new on an already installed item, mark it to be
                    # reinstalled
                    if similary_req:
                        del self.already_installed_dependencies[requirement.project_name]
        else:
            items = constrained_requirements
        return items

    def feed_dependency_tree(self, requirements, dist):
        for mreq in requirements:
            req = self._constrain_requirement(mreq, fromdist=dist)
            identifier = (dist.project_name, dist.version)
            if not req in self.dependency_tree:
                self.dependency_tree[req] = {}
            self.dependency_tree[req][identifier] = dist

    def ensure_dependencies_there(self,
                                  dest,
                                  working_set,
                                  first_call, dists):
        """Ensure all distributionss have their dependencies in the working set.
        Also ensure all eggs are at rights versions pointed out by buildout.
        @param dest the final egg cache path
        @param working_set the current working set
        @param already_installed_dependencies Requirements
                                              of already installed dependencies
        @param first_call instaernally parameter to show debug messages avoiding
                          dirts caused by recursivity

        """
        deps_reqs = []
        for dist in dists:
            r = self._constrain_requirement(dist.as_requirement(), fromdist=dist)
            self.already_installed_dependencies.setdefault(r.project_name, r)
            deps_reqs.extend(dist.requires())
            self.feed_dependency_tree(dist.requires(), dist)
        if deps_reqs:
            ideps_reqs = self.filter_already_installed_requirents( deps_reqs)
            d_rs, working_set = self._install_requirements(ideps_reqs, dest, working_set, first_call = False)

        if first_call:
            self.logger.debug('All egg dependencies seem to be installed!')
        return working_set

    def add_dist(self, dist):
        # mark the distribution as installed
        self.maybe_get_patched_requirement(dist)
        self.inst._env.add(dist)

    def _install_requirements(self, reqs, dest,
                              working_set=None,
                              first_call=True):
        """Get urls of neccessary eggs to
        achieve a requirement.
        """
        if not self.already_installed_dependencies:
            self.already_installed_dependencies = {}

        # initialise working directories
        if not os.path.exists(self.tmp_directory):
            os.makedirs(self.tmp_directory)
        if working_set is None:
            working_set = pkg_resources.WorkingSet([])
        else:
            working_set = working_set

        requirements = self.filter_already_installed_requirents(reqs)
        if self.HAS_DISTRIBUTE:
            distribute_req = self._constrain_requirement(
                pkg_resources.Requirement.parse('distribute')
            )
            for i, r in enumerate(requirements[:]):
                if r.project_name == 'setuptools':
                    self.logger.warning(
                        'Replaced setuptools requirment by %s.' % distribute_req
                    )
                    requirements[i] = distribute_req

        # Maybe an existing dist is already the best dist that satisfies the
        # requirement
        if requirements:
            dists = []
            #self.logger.debug('Trying to install %s' % requirements)
            for requirement in requirements:
                similary_req = self.already_installed_dependencies.get(requirement.project_name, None)
                if similary_req:
                    requirers = self.dependency_tree.get(similary_req, None)
                    msg = "'%s' is already installed." % (requirement)
                    if ('%s'%requirement) != ('%s'%similary_req) and not (similary_req in requirement):
                        msg = "'%s' is already installed as '%s'." % (requirement, similary_req)
                    if requirers and self.logger.getEffectiveLevel() <= logging.DEBUG:
                        msg += ' Requirers: %s' % (', '.join(['%s'%self.dependency_tree[similary_req][d] for d in requirers]))
                    self.logger.debug(msg)
                    continue
                #try:
                dist, avail, maybe_patched_requirement = self._satisfied(requirement, working_set)

                #except Exception, e:
                #    raise

                # switch setuptools to distribute if any
                if (avail is not None) and self.HAS_DISTRIBUTE:
                    if avail.project_name == 'setuptools':
                        distribute = self._constrain_requirement(
                            pkg_resources.Requirement.parse('distribute')
                        )
                        try:
                            dist, avail = self.inst._satisfied(distribute)
                        except:
                            pass

                # installing extras if required
                if dist is None:
                    fdist = None
                    try:
                        # if we come from a patched distribution, i have already
                        # searched the sdist which fits with the requirement.
                        # We will force to download it
                        force_location = False
                        if PATCH_MARKER in '%s' % maybe_patched_requirement:
                            force_location = True
                        fdist = self._get_dist(avail, working_set, force_location=force_location)
                    except Exception, e:
                        # try to find the same distribution on other links,
                        if avail:
                            requirement = pkg_resources.Requirement.parse(
                                '%s==%s'%(avail.project_name, avail.version)
                            )
                        # eg when the download_url returns 404 or error
                        sdist, sdists = None, self._search_sdists(requirement, working_set)
                        while sdists:
                            try:
                                sdist = sdists.pop(0)
                            except IndexError:
                                break
                            if sdist:
                                try:
                                    fdist = self._get_dist(sdist, working_set)
                                    self.lastlogs.append(
                                        'Source distribution %s == %s from %s was installed '
                                        'but it was not the first seen on the indexes '
                                        'matching the requirement although it was the first valid.' % (
                                            fdist.project_name,
                                            fdist.version,
                                            self.get_dist_location(fdist)
                                        )
                                    )
                                    #self.lastlogs.append('Additional error was : %s' % e)
                                except Exception, e:
                                    self.logger.error(
                                        '%s can\'t be downloaded'
                                        ' from %s.'%(sdist,
                                                     sdist.location))
                                    self.logger.error('Encountered Exception:'
                                                      ' %s: %s'%(e.__class__,e))

                                if fdist:
                                    break
                    if not fdist:
                        raise DistributionDownloadError(
                            'A distribution'
                            ' matching \'%s\' can\'t be'
                            ' downloaded.' %
                            (requirement)
                        )
                    try:
                        dist = self._install_distribution(fdist, dest, working_set)
                    except EggPatchError, e:
                        raise
                    except SystemError, e:
                        raise
                    except Exception, e:
                        #raise
                        # try to install the same distribution on other links,
                        # eg when the download_url returns 404 or error
                        freq = pkg_resources.Requirement.parse(
                            '%s==%s' % (fdist.project_name, fdist.version)
                        )
                        if self.install_previous_version:
                            freq = requirement
                        sdist, sdists = None, self._search_sdists(freq, working_set)
                        while sdists:
                            try:
                                sdist = sdists.pop(0)
                            except IndexError:
                                break
                            if sdist:
                                # try to see if the fallback distribution was
                                # not installed bvfore.
                                dist, avail = self.inst._satisfied(
                                    pkg_resources.Requirement.parse(
                                        '%s==%s' % (
                                            sdist.project_name,
                                            sdist.version
                                        )
                                    )
                                )
                                if not dist:
                                    try:
                                        fdist = self._get_dist(sdist, working_set)
                                    except:
                                        pass
                                    if fdist:
                                        try:
                                            dist = self._install_distribution(fdist, dest, working_set)
                                        except Exception, e:
                                            self.lastlogs.append(
                                                'Distribution %s == %s from %s'
                                                ' is invalid. (%s)' % (
                                                    fdist.project_name,
                                                    fdist.version,
                                                    self.get_dist_location(fdist),
                                                    e
                                                )
                                            )
                                # either the distribution was already there or
                                # was just installed, stop the loop and
                                # advertise user of the fallback.
                                if dist:
                                    sdists = []
                                    self.lastlogs.append(
                                        'Distribution %s == %s from %s was installed '
                                        'but it was not the first seen on the indexes '
                                        'matching the requirement although it was the first valid' % (
                                            dist.project_name,
                                            dist.version,
                                            self.get_dist_location(dist)
                                        )
                                    )
                                    self.lastlogs.append('Additional error was : %s' % e)

                        if not dist:
                            raise

                    # advertise environements of our new dist
                    self.add_dist(dist)

                # honouring extra requirements
                if requirement.extras:
                    _, working_set = self._install_requirements(dist.requires(requirement.extras), dest, working_set, first_call=False)
                    self.feed_dependency_tree(dist.requires(requirement.extras), dist)
                self.append(requirement, dist, dists)

            for dist in dists:
                # remove similar dists found in sys.path if we have ones, to
                # avoid conflict errors
                similar_dist = working_set.find(pkg_resources.Requirement.parse(dist.project_name))
                if similar_dist and (similar_dist != dist):
                    if self.get_dist_location(similar_dist) in working_set.entries:
                        working_set.entries.remove(self.get_dist_location(similar_dist))
                    if self.get_dist_location(similar_dist) in working_set.entry_keys:
                        del working_set.entry_keys[self.get_dist_location(similar_dist)]
                    if similar_dist.project_name in working_set.by_key:
                        del working_set.by_key[similar_dist.project_name]

                working_set.add(dist)
                self.feed_dependency_tree(dist.requires(), dist)
                # Check whether we picked a version and, if we did, report it:
                if not (
                    dist.precedence == pkg_resources.DEVELOP_DIST
                    or
                    (len(requirement.specs) == 1
                     and
                     requirement.specs[0][0] == '==')
                    ):
                    self.logger.debug('Picked: %s = %s',
                                      dist.project_name,
                                      dist.version)
                    if not self.inst._allow_picked_versions:
                        # if picked and we have a specific version, just do not
                        # fail
                        do_not_fail = False
                        if isinstance(dist.version, basestring):
                            if dist.version == self.versions.get(dist.project_name, ''):
                                do_not_fail = True
                        if not do_not_fail:
                            raise zc.buildout.UserError(
                                'Picked: %s = %s' % (dist.project_name,
                                                     dist.version))
            working_set = self.ensure_dependencies_there(dest, working_set, first_call, dists)

        return self.already_installed_dependencies.values(), working_set

    def maybe_get_patched_requirement(self, dist):
        # mark the distribution as installed
        v, _, _, patches, _ = self._get_dist_patches(dist.project_name, dist.version)
        r = pkg_resources.Requirement.parse('%s' % (dist.project_name))
        if v:
            r = pkg_resources.Requirement.parse('%s==%s' % (dist.project_name, v))
        if len(patches)>0:
            self.inst._versions[r.project_name] = v
            self.versions[r.project_name] = v
        else:
            # if we did not find patches for this distribution, only constrain
            # it.
            dist_as_req = r
            if not v:
                dist_as_req = r
            r = self._constrain_requirement(dist_as_req, fromdist=dist)
        return r

    def _install_distribution(self, dist, dest, working_set=None):
        """Install a setuptool distribution
        into the eggs cache."""
        patched, repackaged = False, False
        if not self.already_installed_dependencies:
            self.already_installed_dependencies = {}
        # where we put the builded  eggs
        tmp = os.path.join(self.tmp_directory, 'eggs')


        if not os.path.isdir(tmp):
            os.makedirs(tmp)
        # maybe extract time
        location = self.get_dist_location(dist)
        if not location.endswith('.egg'):
            location = tempfile.mkdtemp()
            self._unpack(self.get_dist_location(dist), location)
            location = self._get_compil_dir(location)
            # setup build_ext
            setup_cfg = os.path.join(location, 'setup.cfg')
            if not os.path.exists(setup_cfg):
                f = open(setup_cfg, 'w')
                f.close()
            beo = self.get_bdist_ext_options(dist.project_name)
            if beo:
                repackaged = True
                setuptools.command.setopt.edit_config(
                    setup_cfg,
                    dict(build_ext=beo)
                )
        sub_prefix = self.options.get(
            '%s-build-dir' % ( dist.project_name.lower()),
            None
        )
        if sub_prefix:
            location = os.path.join(location, sub_prefix)

        self.options['compile-directory'] = location


        if not location.endswith('.egg'):
            # maybe patch time
            patched, dist = self._patch(location, dist)
            #maybe we have a hook
            hooked = self._call_hook(
                '%s-pre-setup-hook' % (dist.project_name.lower()),
                location
            )
            if not hooked:
                hooked = self._call_hook(
                    '%s-pre-setup-hook' % (dist.project_name),
                    location
                )
            if patched or hooked:
                patched = True

        # recursivly easy installing dependencies
        ez = easy_install.easy_install(distutils.core.Distribution())
        if os.path.isdir(location):
            oldcwd = os.getcwd()
            # generating metadata for source distributions
            try:
                os.chdir(location)
                ez.run_setup('', '', ['egg_info', '-e', '.'])
            except:
                os.chdir(oldcwd)

        # getting dependencies
        requires = []
        reqs_lists = [a.requires()
                      for a in pkg_resources.find_distributions(location)]

        # installing them
        for i, reqs_list in enumerate(reqs_lists):
            # do not constrain there, it will be done in the recursive install
            # call
            requires.extend(reqs_list)

        # compile time
        dist_location = self.get_dist_location(dist)
        ttar = '/not/existing/file/muhahahahaha'
        if not (dist.precedence in (pkg_resources.EGG_DIST,
                                    pkg_resources.BINARY_DIST,
                                    pkg_resources.DEVELOP_DIST)):
            if patched or repackaged:
                ttar = os.path.join(
                    tempfile.mkdtemp(), '%s-%s.%s' % (dist.project_name,
                                                      dist.version,
                                                      'tar.gz'
                                                     )
                )
                tar = tarfile.open(ttar, mode='w:gz')
                tar.add(location, os.path.basename(location))
                tar.close()
                dist_location = ttar

        # delete our require getter hackery mecanism because
        # it can pertubate the setuptools namespace handling
        if os.path.isdir(location):
            os.chdir(location)
            for f in os.listdir('.'):
                if f.endswith('.egg-info') and os.path.isdir(f):
                    shutil.rmtree(f)
            os.chdir(oldcwd)

        # mark the current distribution as installed to avoid circular calls
        if not dist.project_name in self.already_installed_dependencies:
            self.feed_dependency_tree(requires, dist)
            self.already_installed_dependencies[dist.project_name] = self.maybe_get_patched_requirement(dist)

        # recusivly install dist requirements before finnishing to install it.
        if requires and not self.options.get('ez-nodependencies'):
            _, working_set = self._install_requirements(requires, dest, working_set, first_call = False)



        # install code ( calling ez and etc.)
        self._run_easy_install(tmp, ['%s' % dist_location], working_set=working_set)
        if os.path.exists(ttar):
            os.remove(ttar)
        dists = []
        env = self.make_env([tmp])
        for project in env:
            dists.extend(env[project])

        if not dists:
            raise zc.buildout.UserError("Couldn't install: %s" % dist)

        if len(dists) > 1:
            self.logger.warn("Installing %s\n"
                        "caused multiple distributions to be installed:\n"
                        "%s\n",
                        dist, '\n'.join(map(str, dists)))
        else:
            d = dists[0]
            if d.project_name != dist.project_name:
                self.logger.warn("Installing %s\n"
                            "Caused installation of a distribution:\n"
                            "%s\n"
                            "with a different project name.",
                            dist, d)
            if d.version != dist.version:
                self.logger.warn("Installing %s\n"
                            "Caused installation of a distribution:\n"
                            "%s\n"
                            "with a different version.",
                            dist, d)

        ## check if cache container is there.
        if not os.path.isdir(dest):
            os.makedirs(dest)
        # install eggs in the destination
        result = []
        for d in dists:
            newloc = os.path.join(
                dest,
                os.path.basename(self.get_dist_location(d))
            )
            # dont forget to skip zipped eggs, normally we dont have ones, but
            # in case

            norm_d_name = d.project_name
            if sys.platform.startswith('win'):
                if d.project_name:
                    norm_d_name = d.project_name.lower()
            norm_dist_name = dist.project_name
            if sys.platform.startswith('win'):
                if dist.project_name:
                    norm_dist_name = dist.project_name.lower()
            if (
                ( norm_d_name == norm_dist_name)
                and (patched)
                and (not os.path.isfile(self.get_dist_location(d)))
               ):
                # just rename the egg to match the patched name if any
                # and also remove python version bits
                without_pyver_re = re.compile("(.*)-py\d+.\d+.*$", re.M|re.S)
                d_egg_name =    without_pyver_re.sub("\\1", d.egg_name())
                dist_egg_name = without_pyver_re.sub("\\1", dist.egg_name())
                newloc = newloc.replace(d_egg_name, dist_egg_name)
                pkginfo = os.path.join(d._provider.egg_info, 'PKG-INFO')
                pkginfo_contents = open(pkginfo, 'rU').readlines()
                version_pkginfo_re = re.compile('^(V|v)ersion: .*', re.M|re.U)
                patched_content = []
                for line in pkginfo_contents:
                    if version_pkginfo_re.match(line):
                        line = version_pkginfo_re.sub('Version: %s' % dist.version,
                                                      line)
                    patched_content.append(line)
                open(pkginfo, 'w').write(''.join(patched_content))
                d = d.clone(**{'version': dist.version})
            if self.uname.startswith('win'):
                newloc = os.path.normpath(newloc)
            if os.path.exists(newloc):
                if os.path.isdir(newloc):
                    shutil.rmtree(newloc)
                else:
                    os.remove(newloc)
            try:
                os.rename(self.get_dist_location(d), newloc)
            except OSError, e:
                # better to delete / copy
                remove_path(newloc)
                if os.path.isdir(self.get_dist_location(d)):
                    shutil.copytree(self.get_dist_location(d), newloc)
                else:
                    shutil.copy2(self.get_dist_location(d), newloc)
                remove_path(self.get_dist_location(d))

            # regenerate pyc's in this directory
            if os.path.isdir(newloc):
                try:
                    redo_pyc(os.path.abspath(newloc), executable = self.executable)
                except Exception, e:
                    self.logger.error('Can\'t compile pyc files in %s.' % newloc)
            nd = pkg_resources.Distribution.from_filename(
                newloc, metadata=pkg_resources.PathMetadata(
                    newloc, os.path.join(newloc, 'EGG-INFO')
                )
            )
            result.append(nd)
        if os.path.isdir(self.get_dist_location(nd)):
            self._call_hook(
                '%s-post-setup-hook' % (d.project_name.lower()),
                newloc
            )

            self._call_hook(
                '%s-post-setup-hook' % (d.project_name),
                newloc
            )
        if not dest in self.eggs_caches:
            self.eggs_caches += [dest]
        rdist = None
        if result:
            renv = self.make_env([dest])
            rdist = result[0]
        if (not rdist):
            self.scan()
            rdist = self.inst._env.best_match(dist.as_requirement(), working_set)
        # temporary marking the default requirement as a distribution requirer
        # if the resulting distribution does not match the initial distribution project_name or version
        # we will just add it to the dep tree to have it for debug purpose in case of troubles
        if (rdist.project_name != dist.project_name) or (rdist.version != dist.version):
            self.logger.debug(
                'Resulting distribution (%s-%s) does not match the initial source '
                'distribution identifiers (%s-%s)' % (
                    rdist.project_name, rdist.version,
                    dist.project_name, dist.version
                )
            )
        #if not dist.version and rdist.version:
        #    dist = rdist
        # be sure that the installed distribution is not conflicting with its filename.
        self.already_installed_dependencies[dist.project_name] = self.maybe_get_patched_requirement(rdist)
        self.logger.info("Installed %s %s (%s)." % (rdist.project_name, rdist.version, self.get_dist_location(rdist)))
        return rdist

    def _run_easy_install(self, prefix, specs, caches=None, working_set=None, dist=None):
        """Install a python egg using easy_install."""
        if not caches:
            caches = []

        ez_args = '-mU'
        # compatiblity thing: we test ez-dependencies to be there
        # new version of  the recipe implies dependencies installed prior to the
        # final ez install call via the require dance
        ez_args += 'N'

        ez_args += 'xd'

        args = ('-c', zc.buildout.easy_install._easy_install_cmd, ez_args,
                zc.buildout.easy_install._safe_arg(prefix))
        if sys.platform.startswith('win'):
            ez_main_cmd = zc.buildout.easy_install._easy_install_cmd
            if zc.buildout.easy_install._easy_install_cmd.startswith('"'):
                ez_main_cmd = zc.buildout.easy_install._easy_install_cmd[1:-1]
            args = ('-c', ez_main_cmd, ez_args, prefix)

        if self.zip_safe:
            args += ('-Z', )
        else:
            args += ('-z', )
        if self.logger.getEffectiveLevel() <= logging.DEBUG:
            args += ('-v', )
        else:
            args += ('-q', )

        if self.offline:
            args+= ('-H None', )

        for dir in caches + self.eggs_caches:
            args += ('-f %s' % os.path.normpath(dir),)

        self._sanitizeenv(working_set)

        cwd = os.getcwd()
        for spec in specs:
            largs = args + ('%s' % spec, )

            # installing from a path, cd inside
            if spec.startswith('/') and os.path.isdir(spec):
                os.chdir(spec)

            # ugly fix to avoid python namespaces conflicts
            if os.path.isdir('setuptools'):
                os.chdir('/')

            self.logger.debug('Running easy_install: \n%s "%s"\n',
                             self.executable,
                             '" "'.join(largs))

            try:
                sys.stdout.flush() # We want any pending output first
                lenv =  dict(os.environ)
                if sys.platform.startswith('win'):
                    lenv['SystemRoot'] = os.environ.get('SystemRoot', 'c:\\windows\\')
                exit_code = subprocess.Popen([self.executable]+list(largs), env = lenv).wait()
                if exit_code > 0:
                    raise core.MinimergeError('easy install '
                                              'failed !')
            except Exception, e:
                raise EasyInstallError(
                    'PythonPackage via easy_install '
                    'Install failed !\n%s' % e,
                    **{'specs': specs,
                       'dist': dist,
                       'working_set': working_set,
                       'prefix': prefix,
                      }
                )

        os.chdir(cwd)

    def _get_dist(self, avail, working_set, force_location=True):
        """Get a distribution."""

        requirement = pkg_resources.Requirement.parse(
            '%s == %s' % (avail.project_name, avail.version)
        )

        self.logger.debug('Trying to get '
                                 'distribution for \'%s\'' % (
                                     avail.project_name
                                 )
                                )

        # We may overwrite distributions, so clear importer
        # cache.
        sys.path_importer_cache.clear()
        # if the dist begin with an url, we try to dnowload it.
        # if available location is a path, add it too to find links
        link = self.get_dist_location(avail)
        if link.startswith('/'):
            if not os.path.isdir(link):
                link = os.path.dirname(link)
            self.inst._index.add_find_links([link])
        source = self.get_dist_location(self.inst._index.obtain(requirement))
        if force_location:
            source = self.get_dist_location(avail)
        # download to cache/FIRSTLETTER/Archive
        filename = self._download(
            url=source,
            destination=self.download_cache,
        )
        dist = avail.clone(location=filename)

        if dist is None:
            raise zc.buildout.UserError(
                "Couln't download distribution %s." % avail)

        for key in self.sav_environ:
            os.environ[key] = self.sav_environ[key]

        return dist

    def _get_dist_patches(self, name, aversion = None, options=None):
        """Get the patches for a distribution.
        returns a tuple
        patched_version_str, patch_cmd, patch_options, patches_list
        """
        version = aversion
        if not version:
            version = self.versions.get(name, '')
            # we got a fixed version
            if version:
                aversion = version

        # remove the minitage patch computation as we are rebuilding it!
        version = get_orig_version(version)
        if not options:
            options = self.options
        # patch for eggs are based on the project_name
        patch_cmd = options.get(
            '%s-patch-binary' % name,
            'patch'
        ).strip()

        patch_options = ' '.join(
            options.get(
                '%s-patch-options' % name, '-Np0'
            ).split()
        )
        patches = options.get(
            '%s-patches' % name,
            '').split()
        # conditionnaly add OS specifics patches.
        patches.extend(
            splitstrip(
                options.get(
                    '%s-%s-patches' % (name,
                                       self.uname.lower()),
                    ''
                )
            )
        )
        # specific version
        patches.extend(
            splitstrip(
                options.get(
                    '%s-%s-patches' % (name, version),
                    ''
                )
            )
        )
        patches.extend(
            splitstrip(
                options.get(
                    '%s--%s-%s-patches' % (name, version,
                                       self.uname.lower()),
                    ''
                )
            )
        )

        additionnal = ''
        if len(patches):
            # this will make this distribution, the newer one!for this release
            # number
            additionnal = PATCH_MARKER
            separator = 'IAMATEXTSEPARATORSTRING'
            for patch in patches:
                patch = patch.replace('.patch', '')
                patch = patch.replace('.diff', '')
                patch_name = os.path.basename(patch)
                # throw any unfriendly setuptools version name away :)
                for s in ('.', '_', '-', '(',
                          ')', '#', '*', '+', '~', '&', '?', ','
                          ';', ':', '!', '§', '$', '=', '@', '^'
                          '\\', '|'):
                    patch_name = patch_name.replace(s, separator)
                forged_name = ''
                for part in patch_name.split(separator):
                    fname=part
                    if len(part)>1:
                        fname = '%s%s' % (part[0].upper(), part[1:])
                    forged_name += fname
                additionnal = '%s-%s' % (additionnal, forged_name)
            if version:
                version += "-%s" % additionnal
            else:
                version = additionnal
        # if we call the function without version bit and we did not find a
        # version slug inside the [versions], just reset the version to None
        if not aversion:
            version = ''
        # windows breaks the case sensitivity, forcing lower
        if sys.platform.startswith('win'):
            version = version.lower()
            additionnal = additionnal.lower()
        return version, patch_cmd, patch_options, patches, additionnal

    def _patch(self, location, dist):

        version, patch_cmd, patch_options, patches, additionnal = self._get_dist_patches(dist.project_name, dist.version)
        # not patched ?
        if len(patches):
            try:
                common. MinitageCommonRecipe._patch(
                    self,
                    location,
                    patch_cmd = patch_cmd,
                    patch_options = patch_options,
                    patches = patches,
                    download_dir = os.path.join(self.download_cache,
                                                'patches',
                                                dist.project_name,
                                                dist.version)
                )
                dist = dist.clone(**{'version': version})
            except Exception, e:
                raise EggPatchError('%s' % e)
        return bool(len(patches)), dist

    def _sanitizeenv(self, ws):
        """Get the env.in the right way to compile.
        Only the pypath may vary at each iteration, we zap the rest."""
        # get the working set into the env.
        self._set_py_path(ws)
        # use the common nice functions to
        # make our environement convenient to
        # build packages with dependencies
        self._set_path()
        self._set_pkgconfigpath()
        self._set_compilation_flags()
        self.write_env()

    def get_dist_location(self, dist):
        """ Wrapper to get trhe current driver letter on windows."""
        if self.uname.startswith('win'):
            if not ':' in dist.location and dist.location.startswith('\\'):
                dist.location = os.path.join(
                        os.getcwd()[:2],
                        dist.location
                )

            if letter_re.match(dist.location):
                dist.location = os.path.normpath(dist.location)

        return dist.location


    def append(self, requirement, dist, dists):
        """Goal is to centralize dists insertion thus to be monkey pached in extensions
        """
        dists.append(dist)
        return dists


# vim:set et sts=4 ts=4 tw=80:
