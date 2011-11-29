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

import os
import ConfigParser
import shutil
import re

from minitage.core import collections
from minitage.core.common  import newline
from iniparse import ConfigParser as WritableConfigParser

try:
    from os import uname
except:
    from platform import uname

class MinibuildException(Exception):
    """General Minibuild Error."""


class InvalidConfigFileError(MinibuildException):
    """InvalidConfigFileError."""


class NoMinibuildSectionError(MinibuildException):
    """No minibuild section was found in the minibuild."""


class MissingFetchMethodError(MinibuildException):
    """There is no fetch method in the minibuild."""


class MissingCategoryError(MinibuildException):
    """There is no category in the minibuild."""


class InvalidCategoryError(MinibuildException):
    """The category specified is invalid."""


class InvalidFetchMethodError(MinibuildException):
    """The fetch method is invalid."""


class InvalidInstallMethodError(MinibuildException):
    """The install method is invalid."""


class EmptyMinibuildError(MinibuildException):
    """The minibuild is empty."""


class InvalidMinibuildNameError(MinibuildException):
    """The minibuild was not well named."""

class MinilayException(Exception):
    """General Minilay Error."""

class InvalidMinilayPath(MinilayException):
    """The minilay path is invalid."""



""" valid categories to install into"""
VALID_CATEGORIES = ['meta', 'instances', 'eggs', 'dependencies', 'zope', 'django', 'tg', 'misc']
""" valud install methods to use"""
VALID_INSTALL_METHODS = ['buildout']
"""valid fetch methods to use:
 - hg: mercurial
 - svn: subversion"""
VALID_FETCH_METHODS = ['svn', 'hg', 'static', 'cvs', 'bzr', 'darcs', 'git' , 'monotone']
UNAME = uname()[0].lower()
if 'cygwin' in UNAME:
    UNAME = 'cygwin'
if UNAME.startswith('win'):
    UNAME = 'win'

# minibuilds name checkers
# python sfx
p_sfx = '(py(2\.4|2\.5))'
# versions _pre1234, _beta1234, _alpha1234, _rc1234, _pre1234
v_sfx = '((pre|p|beta|alpha|rc)\d*)'
# _tagNAME or _branchNAME for scm tags
s_sfx = '((tag|branch)([A-Z]|\d)(\.|[A-Z]|\d)*)'
# _rHEAD or _rTIP or _r1234 -> scm revision
n_sfx = '(r(HEAD|TIP|\d+))'
# major-minor
mn_sfx = '((-\d+((\.\d+)*([a-z]?))*)?)'
# complete sufix
sufix = '((%s(_(%s|%s|%s|%s))*)*)' % (mn_sfx, p_sfx, n_sfx, s_sfx, v_sfx)
# packagename : aZ1-az123
m_sfx = '(^([a-zA-Z]|\d)+((-|\.)([a-zA-Z]|\d)+)*)'
# assemble prefixes
versioned_rxp = '^(%s%s)$' % (m_sfx, sufix)
packageversion_re = re.compile(versioned_rxp)

def check_minibuild_name(name):
    """Check if a minibuild is well named.
    Exceptions:
        - InvalidMinibuildNameError if self.name is not a valid minibuild filename.
    """
    if packageversion_re.match(name):
        return True
    return False

def mfilter(f):
    ret = False
    for pref in ('.', 'readme'):
        if f.lower().startswith(pref):
            ret = True
    for suf in ('.svn', '.sav', 'ignore'):
        if f.endswith(suf):
            ret = True
    return ret

class Minilay(collections.LazyLoadedDict):
    """Minilays are list of minibuilds.
    they have a special loaded attribute to lazy load them.
    They store minibuilds in a dictionnary:
        -  self[minibuildName][instance] : minibuild instance
        -  self[minibuildName][error] : exception instance if any
    Arguments
        - path: path to the minilay
    """

    def __init__(self, path=None, minitage_config=None, *kw, **kwargs):
        collections.LazyLoadedDict.__init__(self, *kw, **kwargs)
        self.path = path
        self.minitage_config = minitage_config

        if not os.path.isdir(self.path):
            message = 'This is an invalid directory: \'%s\'' % self.path
            raise InvalidMinilayPath(message)

    def load(self, item=None):
        """Walk the minilay and load everything
        wich seems to be a minibuild inside."""
        if not self.loaded and not item in self.items:
            minibuilds = []
            # 0 is valid
            if item is not None:
                minibuild = os.path.join(self.path, item)
                if os.path.isfile(minibuild) and not mfilter(minibuild):
                    minibuilds.append(item)
            else:
                minibuilds = [a
                              for a in os.listdir(self.path)
                              if not mfilter(a)]
                self.loaded = True
            for minibuild in minibuilds:
                if ((minibuild not in self.items)
                    and (not mfilter(minibuild))):
                    mb_path = os.path.join(self.path, minibuild)
                    if os.path.isfile(mb_path):
                        self[minibuild] = Minibuild(
                            path = mb_path,
                            minitage_config = self.minitage_config
                        )
                        self.items.append(minibuild)

class Minibuild(object):
    """Minibuild object.
    Contains all package metadata including
     - dependenciess
     - url
     - fetch method
     - fetch method options
     - project 's url
     - project 's description
     - install method
    A minibuild has a state
     - False: not ;loaded
     - True:  loaded
    It will read those options in the minibuild section
      - src_uri : url to fetch from
      - src_type : how to fetch (valid methods are 'svn' and 'hg', and 'git',
      and 'bzr')
      - src_opts : arguments for the fetch method (import, -rxxx) be aware you
        also must include the check out argument if you using SCM fetch method there.
        like co or export. This argument is also not filtered out, take care !
      - dependencies : which minibuilds we are relying to as prior dependencies
      - url : project's homepage
      - description : a short description
      - install_method : how to install (valid methods are 'buildout')
      """

    def __init__(self, path, minitage_config = None, *kw, **kwargs):
        """
        Arguments
            path: path to the minibuild file. This minibuild file is pytthon
              configparser like object with a minibuild section which will
              define all the metadate:
        Misc
            Thus we can lazy load minibuilds and save performance.
        """
        self.path = path
        self.name = self.path.split(os.path.sep).pop()
        self.state = None
        self.dependencies = None
        self.raw_dependencies = None
        self.description = None
        self.install_method = None
        self.src_type = None
        self.src_opts = None
        self.src_md5 = None
        self.src_uri = None
        self.url = None
        self.revision = None
        self.category = None
        self.minitage_config = minitage_config
        self.minibuild_config = None
        self.loaded = None
        self.section = None

    def __getattribute__(self, attr):
        """Lazyload stuff."""
        lazyloaded = ['config', 'url', 'revision', 'category', 'src_md5',
                      'raw_dependencies',
                      'dependencies', 'description','src_opts',
                      'src_type', 'install_method', 'src_type']
        if attr in lazyloaded and not self.loaded:
            self.loaded = True
            self.load()
            # case we are always there, setting as loaded
        return object.__getattribute__(self, attr)

    def load(self):
        """Try to load a minibuild.
        Exceptions
            - MinibuildException
        """
        if not check_minibuild_name(self.name):
            message = 'Invalid minibuild name : \'%s\'' % self.name
            raise InvalidMinibuildNameError(message)

        try:
            config = ConfigParser.ConfigParser()
            config.read(self.path)
        except Exception,e:
            message = 'The minibuild file format is invalid: %s'
            raise InvalidConfigFileError(message % self.path)

        if not config.has_section('minibuild'):
            message = 'The minibuild %s has no section [minibuild]'
            raise NoMinibuildSectionError(message % self.path)

        # just read the interresting section in the minibuild ;)
        section = config._sections['minibuild']

        # our dependencies, can be empty
        self.dependencies = section.get('dependencies','').strip().split()
        self.raw_dependencies = section.get('dependencies','').strip().split()
        # specific os dependencies
        os_dependencies = section.get('dependencies-%s' % UNAME, None)
        if os_dependencies:
            self.dependencies = [d
                                 for d in os_dependencies.strip().split()
                                 if d not in self.dependencies
                                ] + self.dependencies
        # os overrides
        os_over = section.get('dependencies-%s-replace' % UNAME, '').strip().split()
        if os_over:
            self.dependencies = os_over

        # our install method, can be empty
        try:
            self.revision = int(section.get('revision','0').strip() )
        except:
            self.revision = 0

        # our install method, can be empty
        self.install_method = section.get('install_method','').strip()
        im_re = re.compile('^([a-zA-Z0-9]+)$')
        im_bypass = section.get('install-method-bypass', False)
        if self.install_method  \
           and not self.install_method in VALID_INSTALL_METHODS:
            if not (im_bypass
                    and im_re.match(self.install_method)):
                message = 'The \'%s\' install method is invalid for %s'
                raise InvalidInstallMethodError(
                    message % (
                        self.install_method, self.path
                    )
                )

        # src_uri is where we will fetch from
        self.src_uri = section.get('src_uri','').strip()
        if self.src_uri:
            # src_type is only important if we have src_uri
            # we just need a src_type is src_uri was specified
            self.src_type = section.get('src_type','').strip()
            if self.src_uri and not self.src_type:
                message = 'You must specify how to fetch your package '
                message += 'into \'%s\' minibuild'
                raise MissingFetchMethodError(message % self.path)
            # src_opts is only important if we have src_uri
            self.src_opts = section.get('src_opts','').strip()
            # src_md5 is only important if we have src_uri
            self.src_md5 = section.get('src_md5','').strip()
            # chech that we got a valid src_type if any
            if not self.src_type in VALID_FETCH_METHODS:
               raise InvalidFetchMethodError(
                   'The \'%s\' src_type is invalid in \'%s\''
                                          % (self.src_type, self.path))
            # if we have a src_uri, we re not a meta package, so we must install
            # somehow, somewhere, so we need a category to install into
            self.category = section.get('category')
            if not self.category:
                message = 'You must specify a category for the \'%s\' minibuild'
                raise MissingCategoryError(message % self.path)
            # check we got a valid category to install into
            # (we wan pass a flag to bypass it)
            # desactivating partially categories check. Let the user do what he
            # want
            categ_re = re.compile('^([a-zA-Z0-9]+)$')
            categ_bypass = section.get('category-bypass', False)
            #if not self.category in VALID_CATEGORIES:
            if not (categ_bypass or categ_re.match(self.category)):
                message = 'the minibuild \'%s\' has an invalid category: %s.\n'
                #message += '\tvalid ones are: %s'
                raise InvalidCategoryError(message % (
                    self.path,
                    self.category,
                #    VALID_CATEGORIES
                        )
                )

        # misc metadata, optionnal
        self.url = section.get('url','').strip()
        self.description = section.get('description','').strip()

        # but in any case, we must at least have dependencies
        # or a install method
        if not self.install_method and not self.dependencies:
            message = 'There is no install method neither dependencies '
            message += 'for a meta minibuild in \'%s\''
            raise EmptyMinibuildError( message % self.path)

        self.parse_vars()
        self.minibuild_config = config

        return self

    def write(self,
              path=None,
              dependencies = None,
              src_uri = None,
              description = None,
              install_method = None,
              src_type = None,
              url = None,
              revision = None,
              category = None,
              src_opts = None,
              src_md5 = None,
             ):
        """Store/Update the minibuild config
        """
        to_write = {
            'dependencies': dependencies,
            'src_uri': src_uri,
            'description': description,
            'install_method': install_method,
            'src_type': src_type,
            'url': url,
            'revision': revision,
            'category': category,
            'src_opts': src_opts,
            'src_md5': src_md5,
        }

        # open config
        if not path:
            path = self.path
        shutil.copy2(path, path+'.sav')
        wconfig = WritableConfigParser()
        wconfig.read(path)

        for metadata in to_write:
            if self.name == 'libxml2-2.7':
                if metadata == 'src_uri':
                    import pdb;pdb.set_trace()  ## Breakpoint ##

            value = to_write[metadata]
            if isinstance(value, list):
                if len(value) < 1:
                    value = None
                else:
                    value =  ' '.join(value)
            if value is not None:
                wconfig.set('minibuild' , metadata, value)

        # write back cofig
        fic = open(path, 'w')
        wconfig.write(fic)
        fic.flush()
        fic.close()
        newline(path)

        # reload minibuild
        self.load()

    def parse_vars(self):
        variables = getattr(self.minitage_config, '_sections', {}).get(
            'minitage.variables', {}
        )
        # allow 2 pass variables
        # to construct variables with variables inside.
        for i in (1,2):
            for key in self.__dict__:
                var = re.compile('\$\{([^}]*)\}', re.M)
                item = self.__dict__[key]
                if item:
                    if '${' in str(item):
                        for pattern in var.findall(item):
                            if pattern in variables:
                                setattr(
                                    self,
                                    key,
                                    getattr(self, key).replace(
                                        '${%s}' % pattern,
                                        variables[pattern]
                                    )
                                )

# vim:set et sts=4 ts=4 tw=80:
