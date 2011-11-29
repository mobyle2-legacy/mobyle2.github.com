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

import copy
import imp
import logging
import os
import re
import shutil
import sys
import tempfile
import time
try:
    from hashlib import md5 as mmd5
except Exception, e:
    from md5 import new as mmd5
import subprocess
import urlparse
from distutils.dir_util import copy_tree
try:
    from os import uname
except:
    from platform import uname



from minitage.core.common import get_from_cache, system, splitstrip, letter_re, remove_path
from minitage.core.unpackers.interfaces import IUnpackerFactory
from minitage.core.fetchers.interfaces import IFetcherFactory
from minitage.core import core

__logger__ = 'minitage.recipe'

RESPACER = re.compile('\s\s*', re.I|re.M|re.U|re.S).sub
ENDLINE = re.compile("\\n", re.S|re.U|re.I)
def norm_path(path):
    if path:
        if sys.platform.startswith('win'):
            if not ':' in path and path.startswith('\\'):
                path = os.path.join(os.getcwd()[:2], path)
            if letter_re.match(path):
                path = os.path.normpath(path)
    return path


def uniquify(l):
    result = []
    for i in l:
        if not i in result:
            result.append(i)
    return result

def divide_url(url):
    scmargs_sep = '|'
    url_parts = url.split(scmargs_sep)
    surl, type, revision, directory, scmargs = '', '', '', '', ''
    if url_parts:
        surl = url_parts[0].strip()
    if len(url_parts) > 1:
        type = url_parts[1].strip()
    if len(url_parts) > 2:
        revision = url_parts[2].strip()
    if len(url_parts) > 3:
        directory = url_parts[3].strip()
    if not(directory) and (surl) and ('//' in surl):
        directory = surl.replace('://', '/').replace('/', '.')
    if len(url_parts) > 4:
        scmargs = scmargs_sep.join(url_parts[4:]).strip()
    if 'file://' in url:
        directory = os.path.basename('')
    surl = surl and surl or ''
    type = type and type or 'static'
    revision = revision and revision or ''
    directory = directory and directory or ''
    scmargs = scmargs and scmargs or ''
    return surl, type, revision, directory, scmargs

def appendVar(var, values, separator='', before=False):
    oldvar = copy.deepcopy(var)
    tmp = separator.join([value for value in values if not value in var])
    if before:
        if not tmp:
            separator = ''
        var = "%s%s%s" % (oldvar, separator,  tmp)
    else:
        if not oldvar:
            separator = ''
        var = "%s%s%s" % (tmp, separator, oldvar)
    return var

def which(program, environ=None, key = 'PATH', split = ':'):
    if not environ:
        environ = os.environ
    PATH=environ.get(key, '').split(split)
    for entry in PATH:
        fp = os.path.abspath(os.path.join(entry, program))
        if os.path.exists(fp):
            return fp
        if (sys.platform.startwith('cyg') or sys.platform.startswith('win')) and os.path.exists(fp+'.exe'):
            return fp+'.exe'
    raise IOError('Program not fond: %s in %s ' % (program, PATH))


class MinitageCommonRecipe(object):
    """
    Downloads and installs a distutils Python distribution.
    """
    def appendPaths(self, s):
        if os.path.exists('/'.join((s, 'bin',))):
            self.libraries.append('/'.join((s, 'bin',)))
            self.path.append('/'.join((s, 'bin',)))
        if os.path.exists('/'.join((s, 'sbin',))):
            self.libraries.append('/'.join((s, 'sbin',)))
            self.path.append('/'.join((s, 'sbin',)))
        if os.path.exists('/'.join((s, 'include',))):
            self.includes.append('/'.join((s, 'include',)))
        if os.path.exists('/'.join((s, 'lib',))):
            self.libraries.append('/'.join((s, 'lib',)))
            self.rpath.append('/'.join((s, 'lib',)))
        if os.path.exists('/'.join((s, 'lib', 'pkgconfig',))):
            self.pkgconfigpath.append('/'.join((s, 'lib', 'pkgconfig',)))
        sp = os.path.join(s, self.site_packages)
        if os.path.exists(sp):
            self.pypath.append(sp)

    def __init__(self, buildout, name, options):
        """__init__.
        The code is voulantary not splitted
        because i want to use this object as an api for the other
        recipes.
        """

        self.logger = logging.getLogger(__logger__)
        self.buildout, self.name, self.options = buildout, name, options
        self.offline = buildout.offline
        self.install_from_cache = self.options.get('install-from-cache', None)

        self.paths_sep = ':'
        if sys.platform.startswith('win'):
            self.paths_sep = ';'

        # system variables
        self.uname = sys.platform.lower()
        self.os_release = self.options.get('os-release', self.uname)
        if 'freebsd' in self.uname:
            self.uname = 'freebsd'
        if 'linux' in self.uname:
            self.uname = 'linux'
        if self.uname.startswith('win') and self.uname != 'cygwin':
            self.uname = 'win'
        if 'cygwin' in self.uname:
             if os.uname()[2][:3] != '1.5':
                self.os_release = 'cygwin2'

        # overiding options with subrelease ones if any
        if self.os_release != self.uname:
            for o in self.options:
                if o.endswith('-cygwin2'):
                    key = o.replace(self.os_release, self.uname)
                    value = self.options[o].strip()
                    if value:
                        self.options[key] = value
                    else:
                        if key in self.options:
                            del self.options[key]

        # build directory
        self.build_dir = norm_path(
            self.options.get('build-dir-%s'%self.uname,
            self.options.get('build-dir', None))
        )
        # url from and scm type if any
        # the scm is one available in the 'fetchers' factory

        self.url = self.options.get('url-%s'%self.uname,
                                     self.options.get('url', None))
        self.urls_list = self.options.get('urls', '').strip().split('\n')
        self.urls_list.insert(0,self.url)
        # remove trailing /
        self.urls_list = [re.sub('/$', '', u) for u in self.urls_list if u]
        self.default_scm = self.options.get('scm', 'static')
        self.default_scm_revision = self.options.get('revision', '')
        self.default_scm_args = self.options.get('scm-args', '')

        # construct a dict in the form:
        # with that, it keeps compatibilty with older recipes.
        # { url {type:'', args: ''}}
        self.urls = {}
        for kurl in self.urls_list:
            # ignore double checkouted urls in all cases
            if not kurl in self.urls:
                url, scmtype, scmrevison, scmdirectory, scmargs = divide_url(kurl)
                if not scmargs:
                    scmargs = self.default_scm_args
                if not scmrevison:
                    scmrevison = self.default_scm_revision
                if not scmtype:
                    scmtype = self.default_scm
                self.urls[url] = {
                    'url' : url,
                    'type': scmtype,
                    'args': scmargs,
                    'revision': scmrevison,
                    'directory': norm_path(scmdirectory),
                }

        # If 'download-cache' has not been specified,
        # fallback to [buildout]['downloads']
        buildout['buildout'].setdefault(
            'download-cache',
            norm_path(
                buildout['buildout'].get(
                    'download-cache',
                    os.path.join(
                        buildout['buildout']['directory'],
                        'downloads'
                    )
                )
            )
        )
        # update with the desired env. options
        self.environ = {}
        if 'environment' in options:
            if not '=' in options["environment"]:
                lenv = buildout.get(options['environment'].strip(), {})
                for key in lenv:
                    self.environ[key] = os.environ[key] = lenv[key]
            else:
                 for line in options["environment"].split("\n"):
                     try:
                         lparts = line.split('=')
                         key = lparts[0]
                         value = '='.join(lparts[1:])
                         key, _, value = line.partition('=')
                         self.environ[key] = os.environ[key] = value
                     except Exception, e:
                         pass

        # maybe md5
        self.md5 = self.options.get('md5sum-%s' % self.uname, self.options.get('md5sum', None))

        # system variables
        self.cwd = os.getcwd()
        cfg = norm_path(
            os.path.abspath(
                os.path.join(self.buildout['buildout']['directory'], '..', '..',
                            'etc', 'minitage.cfg')
            )
        )
        if os.path.exists(cfg):
            # inside a project?
            self.minitage_directory = norm_path(
                os.path.abspath(
                    os.path.join(self.buildout['buildout']['directory'], '..', '..')
                )
            )
        else:
            # default to python prefix
            self.minitage_directory = norm_path(os.path.abspath(sys.prefix))

        # destination
        options['location'] = norm_path(
            os.path.abspath(
                options.get('location',
                    os.path.join(
                        buildout['buildout']['parts-directory'],
                        options.get('name', self.name)
                    )
                )
            )
        )
        self.prefix = self.options.get('prefix', options['location'])
        if self.uname == 'win':
            if letter_re.match(self.prefix):
                dg = letter_re.match(self.prefix).groupdict()
                letter = dg['letter']
                path = dg['path']
                self.prefix = '/%s/%s' % (letter, path.replace('\\', '/'))
                self.prefix = self.prefix.replace('//', '/')

        if options.get("shared", "false").lower() == "true":
            pass

        # if we are installing in minitage, try to get the
        # minibuild name and object there.
        self.str_minibuild = os.path.split(self.cwd)[1]
        self.minitage_section = {}

        # system/libraries dependencies
        self.minitage_dependencies = []
        # distutils python stuff
        self.minitage_eggs = []

        self._skip_flags = self.options.get('skip-flags', False)

        # compilation flags
        self.includes = splitstrip(self.options.get('includes-%s'%self.uname,
                                   self.options.get('includes', '')))

        self.cflags = RESPACER(
            ' ',
            self.options.get('cflags-%s'%self.uname,
                              self.options.get( 'cflags', '')).replace('\n', '')
        ).strip()
        self.ldflags = RESPACER(
            ' ',
            self.options.get('ldflags-%s'%self.uname,
                             self.options.get( 'ldflags', '')).replace('\n', '')
        ).strip()
        self.includes += [a
                          for a in splitstrip(
                              self.options.get('includes-dirs-%s'%self.uname,
                                             self.options.get('includes-dirs', ''))
                          )]
        self.libraries = [a
                          for a in splitstrip(
                              self.options.get('library-dirs-%s'%self.uname,
                              self.options.get('library-dirs', '')))]
        self.libraries_names = ' '
        for l in self.options.get('libraries-%s'%self.uname,self.options.get('libraries', '')).split():
            self.libraries_names += '-l%s ' % l
        self.rpath = [norm_path(a)
                      for a in splitstrip(self.options.get('rpath-%s'%self.uname,
                                          self.options.get('rpath', '')))]


        # separate archives in downloaddir/minitage
        self.download_cache = os.path.join(
            buildout['buildout']['directory'],
            norm_path(buildout['buildout'].get('download-cache')),
            'minitage'
        )

        # do we install cextension stuff
        self.build_ext = self.options.get('build-ext', '')

        # patches stuff
        self.patch_cmd = norm_path(
            self.options.get(
                'patch-binary',
                'patch'
            ).strip()
        )

        self.patch_options = ' '.join(
            self.options.get(
                'patch-options', '-Np0'
            ).split()
        )
        self.patches = [norm_path(a)
                        for a in self.options.get('patches', '').split()]
        if 'patch' in self.options:
            self.patches.append(
                norm_path(self.options.get('patch').strip())
            )
        # conditionnaly add OS specifics patches.
        self.patches.extend(
            [norm_path(a) for a in splitstrip(
                self.options.get(
                    '%s-patches' % (self.uname.lower()),
                    ''
                )
            )]
        )
        self.patches.extend(
            [norm_path(a) for a in splitstrip(
                self.options.get(
                    'patches-%s' % (self.uname.lower()),
                    ''
                )
            )]
        )
        if 'freebsd' in self.uname.lower():
            self.patches.extend(
                [norm_path(a) for a in splitstrip(
                    self.options.get(
                        'freebsd-patches',
                        ''
                    )
                )]
            )
        self.osxflavor = ''
        self.osx_target = self.options.get('osx-target', None)
        self.force_osx_target = self.options.get('force-osx-target', None)
        if 'darwin' in self.uname.lower():
            kv = uname()[2]
            if kv == '9.8.0':
                self.osxflavor = 'leopard'
            if kv.startswith('11.'):
                self.osxflavor = 'lion' 
            if kv.startswith('10.'):
                self.osxflavor = 'snowleopard'
            if self.osxflavor:
                self.patches.extend(
                    [norm_path(a) for a in splitstrip(
                        self.options.get(
                            '%s-patches' % self.osxflavor,
                            ''
                        )
                    )]
                )
            if self.osxflavor == 'snowleopard':
                self.osx_target = '10.6'
            if self.osxflavor == 'lion':
                self.osx_target = '10.7' 
            if self.osxflavor == 'leopard':
                self.osx_target = '10.5'
            if self.force_osx_target:
                if self.force_osx_target.strip() != 'true':
                    self.osx_target = self.force_osx_target.strip()

        # path we will put in env. at build time
        self.path = splitstrip(self.options.get('path-%s' % self.uname, self.options.get('path', '')))

        # pkgconfigpath
        self.pkgconfigpath = splitstrip(self.options.get('pkgconfigpath', ''))

        # python path
        self.pypath = [self.buildout['buildout']['directory'],
                       self.options['location']]
        self.pypath.extend(self.pypath)
        self.pypath.extend(
            [norm_path(a) for a in splitstrip(self.options.get('pythonpath', ''))]
        )

        # tmp dir
        self.tmp_directory = os.path.join(
            buildout['buildout'].get('directory'),
            '__minitage__%s__tmp' % name
        )

        if self.is_win():
            for attr in 'tmp_directory',:
                v = getattr(self, attr)
                if isinstance(v, str):
                    setattr(self, attr, os.path.normpath(v))

        # minitage specific
        # we will search for (priority order)
        # * [part : minitage-dependencies/minitage-eggs]
        # * a [minitage : deps/eggs]
        # * the minibuild dependencies key.
        # to get the needed dependencies and put their
        # CFLAGS / LDFLAGS / RPATH / PYTHONPATH / PKGCONFIGPATH
        # into the env.
        if 'minitage' in buildout:
            self.minitage_section = buildout['minitage']

        self.minitage_section['dependencies'] = '%s %s' % (
                self.options.get('minitage-dependencies', ' '),
                self.minitage_section.get('dependencies', ' '),
        )

        self.minitage_section['eggs'] = '%s %s' % (
                self.options.get('minitage-eggs', ' '),
                self.minitage_section.get('eggs', ' '),
        )

        # try to get dependencies from the minibuild
        #  * add them to deps if dependencies
        #  * add them to eggs if they are eggs
        # but be non bloquant in errors.
        self.minibuild = None
        self.minimerge = None
        minibuild_dependencies = []
        minibuild_eggs = []
        self.minitage_config = os.path.join(
            self.minitage_directory, 'etc', 'minimerge.cfg')
        try:
            self.minimerge = core.Minimerge({
                'nolog' : True,
                'config': self.minitage_config
                }
            )
        except:
            message = 'Problem when intiializing minimerge '\
                    'instance with %s config.'
            self.logger.debug(message % self.minitage_config)

        try:
            self.minibuild = self.minimerge._find_minibuild(
                self.str_minibuild
            )
        except:
            message = 'Problem looking for \'%s\' minibuild'
            self.logger.debug(message % self.str_minibuild)


        if self.minibuild:
            if self.minibuild.category == 'eggs':
                mpackages, pyvers = self.minimerge._select_pythons([self.minibuild])
                for p in mpackages:
                    if not p in self.minibuild.dependencies:
                        self.minibuild.dependencies.append(p.name)
            for dep in self.minibuild.dependencies:
                m = None
                try:
                    m = self.minimerge._find_minibuild(dep)
                except Exception, e:
                    message = 'Problem looking for \'%s\' minibuild'
                    self.logger.debug(message % self.str_minibuild)
                if m:
                    if m.category == 'eggs':
                        minibuild_eggs.append(dep)
                    if m.category == 'dependencies':
                        minibuild_dependencies.append(dep)

        self.minitage_dependencies.extend(
            [os.path.abspath(os.path.join(
                self.minitage_directory,
                'dependencies', s, 'parts', 'part'
            )) for s in splitstrip(
                self.minitage_section.get('dependencies', '')
            ) + minibuild_dependencies ]
        )

        # Defining the python interpreter used to install python stuff.
        # using the one defined in the key 'executable'
        # fallback to sys.executable or
        # python-2.4 if self.name = site-packages-2.4
        # python-2.5 if self.name = site-packages-2.5
        self.executable= None
        if 'executable' in options:
            for lsep in '.', '..':
                if lsep in options['executable']:
                    self.executable = norm_path(os.path.abspath(options.get('executable').strip()))
                else:
                    self.executable = norm_path(options.get('executable').strip())
        elif 'python' in options:
            self.executable = norm_path(self.buildout.get(
                options['python'].strip(),
                {}).get('executable', None))
        elif 'python' in self.buildout:
            self.executable = norm_path(self.buildout.get(
                self.buildout['buildout']['python'].strip(),
                {}).get('executable', None))
        if not self.executable:
            # if we are an python package
            # just get the right interpreter for us.
            # and add ourselves to the deps
            # to get the cflags/ldflags in env.
            for pyver in core.PYTHON_VERSIONS:
                if self.name == 'site-packages-%s' % pyver:
                    interpreter_path = os.path.join(
                        self.minitage_directory,
                        'dependencies', 'python-%s' % pyver, 'parts',
                        'part'
                    )
                    self.executable = os.path.join(
                        interpreter_path, 'bin', 'python'
                    )
                    self.minitage_dependencies.append(interpreter_path)
                    self.includes.append(
                        os.path.join(
                            interpreter_path,
                            'include',
                            'python%s' % pyver
                        )
                    )
        # If we have not python selected yet, default to the current one
        if not self.executable:
            self.executable = self.buildout.get(
                buildout.get('buildout', {}).get('python', '').strip(), {}
                ).get('executable', sys.executable)

        # if there is no '/' in the executable, just search for in the path
        if not self.executable.startswith('/'):
            self._set_path()
            try:
                self.executable = which(self.executable, split = self.paths_sep)
            except IOError, e:
                raise core.MinimergeError('Python executable '
                                 'was not found !!!\n\n%s' % e)

        # compiler binaries
        self.cc = self.options.get('cc-%s'%self.uname,  self.options.get('cc',  '')).strip()
        self.cpp = self.options.get('cpp-%s'%self.uname, self.options.get('cpp', '')).strip()
        self.cplusplus = self.options.get('cplusplus-%s'%self.uname,
                                          self.options.get('cplusplus', '')).strip()

        # support for mingw32 on cygwin + minitage
        self.mingw_prefix = None
        if sys.platform.startswith('cygwin') and 'mingw' in options:
            mingw = ''
            mingwmsgbase = '%s' % (
                    "\n\n"
                    "MingW compiler not found.\n"
                    "You can have one from http://tdragon.net/recentgcc/\n"
                    "Please install a mingw gcc4 installation in\n"
                )
            mingw_present = True
            if 'mingw-path' in options:
                mingw = options.get('minw-path')
            elif self.minimerge:
                mingw = os.path.join(self.minimerge._prefix, 'mingw')
            if not os.path.exists(mingw):
                msg = '%s' % (
                    "\n\n"
                    "%s\n"
                    "\t%s"
                    "\n\n"
                    "You can either set mingw-path to a valid mingw (gcc4) installation.\n"
                    "" % (mingwmsgbase, mingw)
                )
                raise Exception(msg)
            self.mingw_prefix = mingw = os.path.abspath(mingw)
            self.cc = os.path.join(mingw, 'bin', 'gcc')
            self.cpp = os.path.join(mingw,'bin', 'cpp')
            self.cplusplus = os.path.join(mingw,'bin', 'c++')
            mingw_bins = []
            add_msg = ''
            try:
                mingw_bins = [p.replace('.exe', '')
                              for p in os.listdir(os.path.join(mingw, 'bin'))]
            except Exception, e:
                add_msg += 'mingw prefix seems not to be valid, missing bin directory!'
            for path in self.cc, self.cpp, self.cplusplus:
                if not os.path.basename(path) in mingw_bins:
                    raise Exception("\n\n%s\n\t%s\n\n%s\n\n" % (
                                        mingwmsgbase,
                                        self.mingw_prefix,
                                        add_msg
                                    )
                    )

        # which python version are we using ?
        self.executable_version = os.popen(
            '%s -c "%s"' % (
                self.executable ,
                'import sys;print sys.version[:3]'
            )
        ).read().replace('\n', '')

        # where is the python installed, we need it to filter later
        # wrong site-packages picked up by setuptools envrionments scans
        try:
            self.executable_prefix = os.path.abspath(
                    subprocess.Popen(
                        [self.executable, '-c', 'import sys;print sys.prefix'],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        #close_fds=True
                    ).stdout.read().replace('\n', '')
                )
        except:
            # getting the path from the link, if we can:
            try:
                if not self.executable.endswith('/'):
                    executable_directory = self.executable.split('/')[:-1]
                    if executable_directory[-1] in ['bin', 'sbin']:
                        level = -1
                    else:
                        level = None
                    self.executable_prefix = '/'.join(executable_directory[:level])
                else:
                    raise core.MinimergeError('Your python executable seems to point to a directory!!!')
            except:
                raise

        self.executable_lib = os.path.join(
                        self.executable_prefix,
                        'lib', 'python%s' % self.executable_version)

        self.executable_site_packages = os.path.join(
                        self.executable_prefix,
                        'lib', 'python%s' % self.executable_version,
                        'site-packages')

        # site-packages defaults
        self.site_packages = 'site-packages-%s' % self.executable_version
        self.site_packages_path = self.options.get(
            'site-packages',
            os.path.join(
                self.buildout['buildout']['directory'],
                'parts',
                self.site_packages)
        )

        self.minitage_eggs.extend(
            [os.path.abspath(os.path.join(
                self.minitage_directory,
                'eggs', s, 'parts', self.site_packages,
            )) for s in splitstrip(
                self.minitage_section.get('eggs', '')
            ) + minibuild_eggs]
        )
        # sometime we install system libraries as eggs because they depend on
        # a particular python version !
        # There is there we suceed in getting their libraries/include into
        # enviroenmment by dealing with them along with classical
        # system dependencies.
        for s in self.minitage_eggs:
            if 'win' in self.uname:
                m = letter_re.match(s)
                if m:
                    dg = m.groupdict()
                    s = '/%s%s' % (dg['letter'], dg['path'])
                s = s.replace('\\', '/')
            self.appendPaths(s)
        for s in self.minitage_dependencies:
            if 'win' in self.uname:
                m = letter_re.match(s)
                if m:
                    dg = m.groupdict()
                    s = '/%s%s' % (dg['letter'], dg['path'])
                s = s.replace('\\', '/')
            self.appendPaths(s)

        for s in self.minitage_eggs \
                 + [self.site_packages_path] \
                 + [self.buildout['buildout']['eggs-directory']] :
            self.pypath.append(s)

        # avoid relative path in aboslute path, it breaks mingw compiler !
        # also filtering out double includes/such
        for col in ('rpath',
                    'libraries', 'includes',
                    'pypath', 'pkgconfigpath'):
            newcol = []
            for j in getattr(self, col):
                if j.startswith('/') and  ('..' in j):
                    j = os.path.abspath(j)
                if not j in newcol:
                    newcol.append(j)
            setattr(self, col, newcol)

        # cleaning if we have a prior compilation step.*
        if os.path.isdir(self.tmp_directory):
            self.logger.info(
                'Removing pre existing '
                'temporay directory: %s' % (
                    self.tmp_directory)
            )
            shutil.rmtree(self.tmp_directory)
        if self.build_dir:
            if os.path.isdir(self.build_dir):
                self.logger.info(
                    'Removing pre existing '
                    'build directory: %s' % (
                        self.build_dir)
                )
                shutil.rmtree(self.build_dir)

        self.inner_dir = self.options.get('inner-dir', None)
        if self.inner_dir:
            self.inner_dir = os.path.join(self.tmp_directory, self.inner_dir)

    def write_env(self):
        if 'debug' in self.options:
            fic = open(os.path.join(self.tmp_directory, 'build.env'), 'w')
            fic.write('\n')
            for key in [k for k in os.environ
                        if ((not '!' in k))] :
                fic.write('export %s="%s"\n' % (key,
                                                os.environ[key].replace('\\', '\\\\'))
                )
            fic.write('\n')

    def _download(self,
                  url=None,
                  destination=None,
                  scm=None,
                  revision=None,
                  scm_args=None,
                  cache=None,
                  md5 = None,
                  use_cache = True):
        """Download the archive.
        url: url to download
        destination: where to download (directory)
        scm: scm to use if any
        revision: revision to checkout if any
        cache: cache in a subdirectory, either  SCM/urldirectory or urlmd5sum/filename
        md5: file md5sum
        use_cache : if False, always redownload even if the file is there
        """
        self.logger.debug('Download archive from %s.'%url)

        if not url:
            url = self.url

        if not url:
            raise core.MinimergeError('URL was not set!')

        if not destination and (url in self.urls):
            d = self.urls[url]['directory']
            if d:
                if os.path.sep in d:
                    destination = os.path.abspath(d)
        if not destination:
            destination = self.download_cache

        if not scm:
            if url in self.urls:
                scm = self.urls[url]['type'].strip()
        if (not scm) or os.path.exists(url):
            scm = 'static'

        # we use a special function for static files as the generic static
        # fetcher do some magic for md5 uand unpacking and are unwanted there?
        if scm != 'static':
            if cache is None:
                cache = False
            # if we have a fetcher in minibuild dependencies, we make it come in
            # the PATH:
            self._set_path()
            opts = {}

            if not revision:
                # compatibility
                if not (url in self.urls):
                    revision = self.default_scm_revision
                else:
                    r = self.urls[url]['revision'].strip()
                    if r:
                        revision = r

            if not scm_args:
                # compatibility
                if not (url in self.urls):
                    scm_args = self.default_scm_args
                else:
                    a  = self.urls[url]['args'].strip()
                    if a:
                        scm_args = a

            if scm_args:
                opts['args'] = scm_args

            if revision:
                opts['revision'] = revision

            scm_dest = destination
            if cache:
                scm_dir = os.path.join(
                    destination, scm)
                if not os.path.isdir(scm_dir):
                    os.makedirs(scm_dir)
                subdir = url.replace('://', '/').replace('/', '.')
                scm_dest = os.path.join(scm_dir, subdir)

            # fetching now
            scm_dest = norm_path(scm_dest)
            if not self.offline:
                ff = IFetcherFactory(self.minitage_config)
                scm = ff(scm)
                if scm.name == 'Mercurial':
                    if not os.path.exists(scm_dest):
                        os.makedirs(scm_dest)
                verbose = False
                if self.logger.getEffectiveLevel() <= logging.DEBUG:
                    verbose = True
                scm.fetch_or_update(scm_dest, url, opts, verbose=verbose)
            else:
                if not os.path.exists(scm_dest):
                    message = 'Can\'t get a working copy from \'%s\''\
                              ' into \'%s\' when we are in offline mode'
                    raise core.MinimergeError(message % (url, scm_dest))
                else:
                    self.logger.info('We assumed that \'%s\' is the result'
                                     ' of a check out as'
                                     ' we are running in'
                                     ' offline mode.' % scm_dest
                                    )
            return scm_dest
        else:
            if cache:
                m = mmd5()
                m.update(url)
                url_md5sum = m.hexdigest()
                _, _, urlpath, _, fragment = urlparse.urlsplit(url)
                filename = urlpath.split('/')[-1]
                destination = os.path.join(destination, "%s_%s" % (filename, url_md5sum))
            if destination and not os.path.isdir(destination):
                os.makedirs(destination)
            logger = None
            if self.logger.getEffectiveLevel() <= logging.DEBUG:
                logger = self.logger
            return get_from_cache(
                url = url,
                download_cache = destination,
                logger = logger,
                file_md5 = md5,
                offline = self.offline,
                use_cache=use_cache
            )

    def _set_py_path(self, ws=None):
        """Set python path.
        Arguments:
            - ws : setuptools WorkingSet
        """
        self.logger.debug('Setting path')
        # setuptool ws maybe?
        if ws:
            self.pypath.extend(ws.entries)
        # filter out site-packages not relevant to our python installation
        remove_last_slash = re.compile('\/$').sub
        pypath = []
        for entry in [remove_last_slash('', e) for e in self.pypath]:
            sp = (self.executable_site_packages,
                  os.path.join('lib', 'python%s' % self.executable_version,
                  'site-packages')
            )
            lib = (self.executable_lib,
                   os.path.join('lib', 'python%s' % self.executable_version)
            )
            for path, atom in (sp, lib):
                add = True
                if entry.endswith(atom) and not path == entry:
                    add = False
            if add :
                pypath.append(entry)
        if getattr(self, 'extra_paths', []):
            pypath.extend(self.extra_paths)
        # uniquify the list
        pypath = uniquify(pypath)
        os.environ['PYTHONPATH'] = self.paths_sep.join(pypath)
        os.environ['MINITAGE_PYTHONPATH'] = os.environ['PYTHONPATH']


    def _set_path(self):
        """Set path."""
        self.logger.debug('Setting path')
        os.environ['PATH'] = appendVar(os.environ['PATH'],
                     uniquify(self.path)\
                     + [self.buildout['buildout']['directory'],
                        self.options['location']]\
                     , self.paths_sep)
        if 'cygwin' in self.uname:
            paths = []
            noecho = [paths.append(p)
                      for p in os.environ['PATH'].split(self.paths_sep)
                      if not p in paths]
            os.environ['PATH'] = self.paths_sep.join(paths)
        os.environ['MINITAGE_PATH'] = os.environ['PATH']

    def _set_pkgconfigpath(self):
        """Set PKG-CONFIG-PATH."""
        self.logger.debug('Setting pkgconfigpath')
        pkgp = os.environ.get('PKG_CONFIG_PATH', '').split(self.paths_sep)
        os.environ['PKG_CONFIG_PATH'] = self.paths_sep.join(
            uniquify(self.pkgconfigpath+pkgp)
        )
        os.environ['MINITAGE_PKG_CONFIG_PATH'] = os.environ['PKG_CONFIG_PATH']

    def _set_compilation_flags(self):
        """Set CFLAGS/LDFLAGS."""
        self.logger.debug('Setting compilation flags')

        # compiler binaries support
        if self.cpp:
            os.environ['CPP'] = self.cpp
        if self.cc:
            os.environ['CC'] = self.cc
        if self.cplusplus:
            os.environ['CPLUSPLUS'] = self.cplusplus

        # filter
        if 'win' in self.uname:
            os.environ['CFLAGS'] = os.environ.get('CFLAGS', '').replace('-fPIC', '')

        self_libdirs = [self.prefix+'/lib']
        if 'win' in self.uname:
            self_libdirs.append(self.prefix+'/bin')

        if self._skip_flags:
            self.logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            self.logger.warning('!!! Build variable settings has been disabled !!!')
            self.logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            return
        os.environ['CFLAGS']  = ' '.join(
            [os.environ.get('CFLAGS', ''), '  %s' % self.cflags]

        ).strip()

        os.environ['LDFLAGS']  = ' '.join(
            [os.environ.get('LDFLAGS', ''), '  %s' % self.ldflags]
        ).strip()

        if self.rpath:
            os.environ['LD_RUN_PATH'] = appendVar(
                os.environ.get('LD_RUN_PATH', ''),
                [s
                 for s in self.rpath
                 if s.strip()]
                + self_libdirs ,
                self.paths_sep
            )

        quote = ''
        if self.uname.startswith('win'):
            quote ='\''
        darwin_ldflags = ''
        if self.uname == 'darwin':
            # need to cut backward comatibility in the linker
            # to get the new rpath feature present
            # >= osx Leopard
            if not (self.osx_target == 'false'):
                os.environ['MACOSX_DEPLOYMENT_TARGET'] = self.osx_target
            darwin_ldflags += ' -mmacosx-version-min=%s'  % self.osx_target

        if self.libraries:
            os.environ['LDFLAGS'] = appendVar(
                os.environ.get('LDFLAGS',''),
                ['-L%s' % (s) \
                 for s in self.libraries + self_libdirs
                 if s.strip()]
                + [darwin_ldflags] ,
                ' '
            )
            os.environ['LD_LIBRARY_PATH'] = appendVar(
                os.environ.get('LD_LIBRARY_PATH', ''),
                [s
                 for s in self.rpath
                 if s.strip()]
                + self_libdirs ,
                self.paths_sep
            )
            # rpath is neither supported by  native windows or cygwin
            if not 'win' in self.uname:
                os.environ['LDFLAGS'] = appendVar(
                    os.environ.get('LDFLAGS',''),
                    ['-Wl,-rpath -Wl,%s%s%s' % (quote, s, quote) \
                     for s in self.libraries + self_libdirs
                     if s.strip()],
                    ' '
                )

            # system paths not always automatic under cygwin
            if self.uname == 'cygwin':
                os.environ['LDFLAGS'] = ' '.join(
                    [os.environ['LDFLAGS'], '-L/usr/lib -L/lib']
                )
        if self.libraries_names:
            os.environ['LDFLAGS'] = ' '.join([os.environ.get('LDFLAGS', ''), self.libraries_names]).strip()
        if self.minimerge:
            os.environ['CFLAGS']  = ' '.join([
                os.environ.get('CFLAGS', ' '),
                ' ',
                self.minimerge._config._sections.get('minitage.compiler', {}).get('cflags', ''),
                ' ']
            )
            os.environ['LDFLAGS']  = ' '.join([
                os.environ.get('LDFLAGS', ' '),
                ' ',
                self.minimerge._config._sections.get('minitage.compiler', {}).get('ldflags', ''),
                ' ']
            )
            os.environ['MAKEOPTS']  = ' '.join([
                os.environ.get('MAKEOPTS', ' '),
                ' ',
                self.minimerge._config._sections.get('minitage.compiler', {}).get('makeopts', ''),
                ' ']
            )


        if self.includes:
            os.environ['CFLAGS'] = appendVar(
                os.environ.get('CFLAGS', ''),
                ['-I%s%s%s' % (quote, s, quote) \
                 for s in self.includes\
                 if s.strip()]
                ,' '
            )
            os.environ['CPPFLAGS'] = appendVar(
                os.environ.get('CPPFLAGS', ''),
                ['-I%s%s%s' % (quote, s, quote) \
                 for s in self.includes\
                 if s.strip()]
                ,' '
            )
            os.environ['CXXFLAGS'] = appendVar(
                os.environ.get('CXXFLAGS', ''),
                ['-I%s%s%s' % (quote, s, quote) \
                 for s in self.includes\
                 if s.strip()]
                ,' '
            )

        # honour msvc
        if sys.platform.startswith('win'):
            os.environ['INCLUDE'] = appendVar(
                os.environ.get('INCLUDE', ''),
                ['%s' % s \
                 for s in self.includes\
                 if s.strip()]
                ,';'
            )
            os.environ['LIB'] = appendVar(
                os.environ.get('LIB', ''),
                ['%s' % s \
                 for s in self.libraries\
                 if s.strip()]
                ,';'
            )
            for key in ('INCLUDE', 'LIB'):
                os.environ[key] = RESPACER(' ', os.environ.get(key, '')).strip()

        # unpspacing and saving minitage values in environment
        for k in ('MAKEOPTS',
                  'CC', 'CPP', 'CPLUSPLUS',
                  'CFLAGS', 'LDFLAGS',
                  'INCLUDE', 'LIB',
                  'LD_LIBRARY_PATH', 'LD_RUN_PATH',
                  'CPPFLAGS', 'CXXFLAGS',
                  ):
            if k in os.environ:
                os.environ[k] = RESPACER(' ', os.environ.get(k, '')).strip()
                os.environ['MINITAGE_%s'%k.replace('+', 'PLUS')] = os.environ[k]

    def _unpack(self, fname, directory=None):
        """Unpack something"""
        if not directory:
            directory = self.tmp_directory
        self.logger.debug('Unpacking in %s.' % directory)
        if os.path.isdir(fname):
            if not os.path.exists(directory):
                os.makedirs(directory)
            copy_tree(fname, directory)
        else:
            unpack_f = IUnpackerFactory()
            u = unpack_f(fname)
            u.unpack(fname, norm_path(directory))

    def _patch(self, directory, patch_cmd=None,
               patch_options=None, patches =None, download_dir=None):
        """Aplying patches in pwd directory."""
        if not patch_cmd:
            patch_cmd = self.patch_cmd
        if not patch_options:
            patch_options = self.patch_options
        if not patches:
            patches = self.patches
        if patches:
            self.logger.info('Applying patches.')
            cwd = os.getcwd()
            os.chdir(directory)
            for patch in patches:
                patch = norm_path(patch)
                # check the md5 of the patch to see if it is the same.
                fpatch = self._download(patch,
                                        destination=norm_path(download_dir),
                                        md5=None,
                                        cache=True,
                                        use_cache = False,
                                       )
                ret = system(
                    '%s -t %s < %s' % (
                        patch_cmd,
                        patch_options,
                        fpatch),
                    self.logger
                )
            os.chdir(cwd)

    def update(self):
        pass

    def _call_hook(self, hook, destination=None):
        """
        This method is copied from z3c.recipe.runscript.
        See http://pypi.python.org/pypi/z3c.recipe.runscript for details.
        """
        cwd = os.getcwd()
        hooked = False
        if destination:
            os.chdir(destination)

        if hook in self.options \
           and len(self.options[hook].strip()) > 0:
            hooked = True
            self.logger.info('Executing %s' % hook)
            script = self.options[hook]
            filename, callable = script.split(':')
            filename = norm_path(os.path.abspath(filename))
            module = imp.load_source('script', filename)
            getattr(module, callable.strip())(
                self.options, self.buildout
            )

        if destination:
            os.chdir(cwd)
        return hooked


    def _system(self, cmd):
        """Running a command."""
        self.logger.info('Running %s' % cmd)
        ret = 0
        self.go_inner_dir()
        if sys.platform.startswith('win'):
            _, fic = tempfile.mkstemp()
            dfic = open(fic, 'w')
            dfic.write('#!/bin/bash\n')
            dfic.write('%s\n\n' % cmd.replace('\\','\\\\'))
            dfic.flush()
            dfic.close()
            ret = os.system('sh --login "%s"' % fic)
        else:
            p = subprocess.Popen(cmd, env=os.environ, shell=True)
            try:
                sts = os.waitpid(p.pid, 0)
                ret = sts [1]
            except Exception, e:
                ret = 1
            # ret = os.system(cmd)
        if ret:
            raise  core.MinimergeError('Command failed: %s' % cmd)

    def _get_compil_dir(self, directory, filter=True):
        """Get the compilation directory after creation.
        Basically, the first repository in the directory
        which is not the download cache if there are no
        files in the directory
        Arguments:
            - directory where we will compile.
        """
        self.logger.debug('Guessing compilation directory')
        self.go_inner_dir()
        contents = os.listdir(directory)
        # remove download dir
        if '.download' in contents:
            del contents[contents. index('.download')]
        top = directory
        if filter:
            f = [i
                 for i in os.listdir(directory)
                 if (not os.path.isdir(os.path.join(directory, i)))
                 and (not i.startswith('.'))
                 and (not i.startswith('PaxHeaders'))]
            d = [i
                 for i in os.listdir(directory)
                 if os.path.isdir(os.path.join(directory, i))
                 and (not i.startswith('.'))
                 and (not i.startswith('PaxHeaders'))]
            if len(f) < 2 and d:
                top = os.path.join(directory, d[0])
        return top

    def go_inner_dir(self):
        if self.inner_dir:
            os.chdir(self.inner_dir)

    def is_win(self):
        return (getattr(self, 'uname', 'none') == 'win')

# vim:set et sts=4 ts=4 tw=80:
