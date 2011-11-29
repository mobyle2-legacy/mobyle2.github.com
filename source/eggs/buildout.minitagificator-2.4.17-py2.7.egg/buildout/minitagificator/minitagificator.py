#!/usr/bin/env python


# Copyright (C) 2009, Mathieu PASQUET <mpa@makina-corpus.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

__docformat__ = 'restructuredtext en'

import sys
from copy import copy
import os
import logging

import pkg_resources

from zc.buildout.easy_install import Installer

from minitage.recipe.egg.egg import Recipe as Egg
from minitage.recipe.common import common
from minitage.recipe.scripts.scripts import Recipe as Script
from minitage.recipe.cmmi.cmmi import Recipe as Cmmi
from minitage.recipe.scripts.scripts import parse_entry_point

__log__ = logging.getLogger('buildout.minitagificator')

def activate(ws):
    for entry in ws.entries:
        if not entry in sys.path:
            sys.path.append(entry)


class Script(Script):

    for_patchs = True

def monkey_patch_recipes(buildout):
    # try to patch zc.recipe.egg
    # and be kind on API Changes
    __log__.info('Minitaging some recipes')

    try:
        import zc.recipe.egg
        if getattr(zc.recipe.egg, 'Egg', None):
            __log__.debug('Patched zc.recipe.egg.Egg')
            zc.recipe.egg.Egg = Script
        else:
          __log__.debug('!!!! Can\'t patch zc.recipe.egg.Egg')
        if getattr(zc.recipe.egg, 'Eggs', None):
            __log__.debug('Patched zc.recipe.egg.Eggs')
            zc.recipe.egg.Eggs = Egg
        else:
          __log__.debug('!!!! Can\'t patch zc.recipe.egg.Eggs')
        if getattr(zc.recipe.egg, 'Scripts', None):
            __log__.debug('Patched zc.recipe.egg.Scripts')
            zc.recipe.egg.Scripts = Script
        else:
            __log__.debug('!!!! Can\'t patch zc.recipe.egg.Scripts')
    except Exception, e:
        __log__.debug('!!!! Can\'t patch zc.recipe.egg.(Scripts|Eggs): %s' % e)
    try:
        import zc.recipe.egg.custom
        if getattr(zc.recipe.egg.custom, 'Custom', None):
            __log__.debug('Patched zc.recipe.egg.custom')
            zc.recipe.egg.custom.Custom = Egg
        else:
            __log__.debug('!!!! Can\'t patch zc.recipe.egg.custom.Custom!!!')
    except:
        __log__.debug('!!!! Can\'t patch zc.recipe.egg.custom.Custom.')
    try:
        import zc.recipe.cmmi
        if getattr(zc.recipe.cmmi, 'Recipe', None):
            __log__.debug('Patched zc.recipe.cmmi')
            zc.recipe.cmmi.Recipe = Cmmi
        else:
            __log__.debug('!!!! Can\'t patch zc.recipe.cmmi')
    except Exception, e:
        __log__.debug('!!!! Can\'t patch zc.recipe.cmmi')


def monkey_patch_buildout_installer(buildout):
    __log__.info('Minitaging Buildout Installer')
    dexecutable = buildout['buildout']['executable']
    def install(specs, dest,
                links=(), index=None,
                executable=dexecutable, always_unzip=None,
                path=None, working_set=None, newest=True, versions=None,
                use_dependency_links=None, allow_hosts=('*',),
                include_site_packages=None, allowed_eggs_from_site_packages=None,
                prefer_final=None):
        if not '/' in executable:
            executable = common.which(executable)

        if not working_set:
            working_set = pkg_resources.WorkingSet([])

        for i, spec in enumerate(specs[:]):
            if 'setuptools' in spec:
                try:
                    # do we have distribute out there
                    working_set.require('distribute')
                    if isinstance(specs[i], str):
                        specs[i] = specs[i].replace('setuptools', 'distribute')
                    __log__.info('We are using distribute')
                except:
                    __log__.info('We are not using distribute')
        opts = copy(buildout['buildout'])
        opts['executable'] = executable
        opts['buildoutscripts'] = 'true'
        r = Egg(buildout, 'foo', opts)
        r.eggs = specs
        r._dest = dest
        if not r._dest:
            r._dest = buildout['buildout']['eggs-directory']
        if links:
            r.find_links = links
        if index:
            r.index = index
        if always_unzip:
            r.zip_safe = not always_unzip
        caches = r.eggs_caches[:]
        if path:
            if not isinstance(path, str):
                caches.extend([ os.path.abspath(p) for p in path])
            else:
                caches.append(os.path.abspath(path))
        caches = common.uniquify(caches)
        for cache in caches:
            if not (cache in r.eggs_caches):
                r.eggs_caches.append(cache)
        if not versions:
            versions = buildout.get('versions', {})
        ## which python version are we using ?
        #r.executable_version = os.popen(
        #    '%s -c "%s"' % (
        #        executable,
        #        'import sys;print sys.version[:3]'
        #    )
        #).read().replace('\n', '')
        if buildout.offline:
            allow_hosts = 'None'
        try:
            r.inst = easy_install.Installer(
                dest=None,
                index=r.index,
                links=r.find_links,
                executable=r.executable,
                always_unzip=r.zip_safe,
                newest = newest,
                versions = versions,
                use_dependency_links = use_dependency_links,
                path=r.eggs_caches,
                allow_hosts=allow_hosts,
                include_site_packages=None,
                allowed_eggs_from_site_packages=None,
                prefer_final=None,
            )
        except:
            # buildout < 1.5.0
            r.inst = easy_install.Installer(
                dest=None,
                index=r.index,
                links=r.find_links,
                executable=r.executable,
                always_unzip=r.zip_safe,
                newest = newest,
                versions = versions,
                use_dependency_links = use_dependency_links,
                path=r.eggs_caches,
                allow_hosts=allow_hosts,
            )
        r.platform_scan()
        reqs, working_set = r.working_set(working_set=working_set)
        return working_set
    from zc.buildout import easy_install
    easy_install.install = install

def monkey_patch_buildout_options(buildout):
    __log__.info('Minitaging Buildout Options')
    from zc.buildout.buildout import Options, _buildout_default_options
    from zc.buildout.buildout import _install_and_load, _recipe

    def _initialize(self, *args, **kwargs):
        """On intialization, install our recipe instead"""
        Options._old_initialize(self, *args, **kwargs)
        recipe = self.get('recipe')
        if not recipe:
            return
        name = self.name
        reqs, entry = _recipe(self._data)
        mappings = {
            ('zc.recipe.egg', 'default'): ('minitage.recipe.scripts', 'default'),
            ('zc.recipe.egg', 'script'): ('minitage.recipe.scripts', 'default'),
            ('zc.recipe.egg', 'scripts'): ('minitage.recipe.scripts', 'default'),
            ('zc.recipe.egg', 'Custom'): ('minitage.recipe.scripts', 'default'),
            ('zc.recipe.egg', 'Eggs'): ('minitage.recipe.egg', 'default'),
            ('zc.recipe.egg', 'eggs'): ('minitage.recipe.egg', 'default'),
            ('zc.recipe.cmmi', 'default'): ('minitage.recipe.cmmi', 'default'),
        }
        reqsa, entrya = mappings.get((reqs, entry), (None, None))
        if reqsa:
            recipe_class = _install_and_load(reqsa, 'zc.buildout', entrya, self.buildout)
            self.recipe = recipe_class(buildout, name, self)
            self.recipe.logger.info(
                "Replaced %s with %s" % ((reqs, entry), (reqsa, entrya))
            )
    Options._old_initialize = Options._initialize
    Options._initialize = _initialize

    def _call(self, f):
        """On call, verify that our recipes are used"""
        initialization = True
        monkey_patch_recipes(buildout)
        Options._buildout = buildout
        return Options._old_call(self, f)
    Options._old_call = Options._call
    Options._call = _call

def monkey_patch_buildout_scripts(buildout):
    __log__.info('Minitaging Buildout scripts')
    def scripts(reqs,
                working_set,
                executable,
                dest,
                scripts=None,
                extra_paths=(),
                arguments='',
                interpreter='',
                initialization='',
                relative_paths=False,
               ):
        if not '/' in executable:
            executable = common.which(executable)
        if not scripts:
            scripts = []
        if (not relative_paths) or (relative_paths == 'false'):
            relative_paths = 'false'
        else:
            relative_paths = 'true'
        if not interpreter:
            interpreter = ''
        options = {}
        options['generate_all_scripts'] = True
        options['eggs'] = ''
        options['entry-points'] = ''
        options['executable'] = executable
        if '\n'.join(scripts).strip():
            options['scripts'] = '\n'.join(scripts)
            options['generate_all_scripts'] = False
        options['extra-paths'] = '\n'.join(extra_paths)
        options['arguments'] = arguments
        options['interpreter'] = interpreter
        options['initialization'] = initialization
        options['relative-paths'] = relative_paths
        for req in reqs:
            if isinstance(req, str):
                if parse_entry_point(req):
                    options['entry-points'] += '%s\n' % req
                else:
                    # append it to eggs to be generated
                    try:
                        #if it is really an egg
                        req = pkg_resources.Requirement.parse(req)
                        # append it to eggs
                        options['eggs'] += '\n%s' % req
                    except Exception, e:
                        #other wise, just add the dist to the scripts for later use
                        options['scripts'] += '\n%s' % req
            elif isinstance(req, tuple):
                options['entry-points'] += '%s=%s:%s' % req
        r = Script(buildout, 'foo', options)
        if dest and options.get('bin-directory', False):
            if dest == options['bin-directory']:
                dest = buildout['buildout'].get('eggs-directory', 'eggs')

        r._dest = dest
        res = r.install(working_set=working_set)
        return res
    from zc.buildout import easy_install
    easy_install.scripts = scripts

def set_minitage_env(buildout):
    options = {}
    r = Script(buildout, 'foo', options)
    r._set_compilation_flags()
    r._set_path()
    r._set_py_path()
    r._set_pkgconfigpath()

def enable_dumping_picked_versions_req(old_working_set):
    def working_set(self, extras=None, working_set=None, dest=None):
        reqs, iws = old_working_set(self,
                                   extras = extras,
                                   working_set = working_set,
                                   dest = dest)
        ws = list(iws)
        ws.sort()
        from buildout.dumppickedversions import required_by
        for req in self.dependency_tree:
            req_ = str(req.project_name)
            for mid in self.dependency_tree[req]:
                dist = self.dependency_tree[req][mid]
                dist_ = str(dist)
                if (req_ in required_by
                    and dist_ not in required_by[req_]):
                        required_by[req_].append(dist_)
                else:
                    required_by[req_] = [dist_]
        return reqs, iws
    return working_set

def enable_dumping_picked_versions(old_append):
    def append(self, requirement, dist, dists):
        dists = old_append(self, requirement, dist, dists)
        if not (dist.precedence == pkg_resources.DEVELOP_DIST
                or (len(requirement.specs) == 1
                    and requirement.specs[0][0] == '==')
               ):
            Installer.__picked_versions[dist.project_name] = dist.version
            return dist
    return append

def monkey_patch_buildout_dumppickedversion(buildout):
    if 'buildout.dumppickedversions' in buildout['buildout']['extensions']:
        if not getattr(Egg, 'append', None):
            msg = 'Please update to minitage.recipe.egg>=1.88 to use with buildout.dumppickedversions.\n'
            import minitage.recipe.egg
            msg += 'Its current location is %s.\n' % (os.path.dirname(minitage.recipe.egg.__file__))
            msg += 'Either fix your buildout version of minitage.recipe.egg or delete this egg.\n'
            __log__.error(msg)
            raise Exception(msg)
        Egg.append = enable_dumping_picked_versions(Egg.append)
        Egg.working_set = enable_dumping_picked_versions_req(Egg.working_set)

def install(buildout=None):
    # pre-initialize me, the hacky way !
    monkey_patch_buildout_dumppickedversion(buildout)
    monkey_patch_buildout_installer(buildout)
    monkey_patch_buildout_scripts(buildout)
    monkey_patch_buildout_options(buildout)
    monkey_patch_recipes(buildout)
    if 'minitage-globalenv' in buildout['buildout']:
        set_minitage_env(buildout)

# vim:set et sts=4 ts=4 tw=80:

