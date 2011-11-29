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
import optparse

from minitage.core import core


usage = """
%(arg)s [Options] minibuildn  \t\t\t: Installs  package(s)
%(arg)s [Options] -j m  a b m ... n  \t\t: Installs  package(s) from 'm' to 'n'
%(arg)s [Options] -rm minibuild ... minibuildn  \t: Uninstall package(s)
%(arg)s [Options] -uU minibuild ... minibuildn  \t: Update/Upgrade package(s)
%(arg)s [Options] -RuU minibuild ... minibuildn  \t: Update/Upgrade/rebuild package(s)


IMPORTANT NODE: buildout is running by default in non newest mode, see -u option!
""" % {'arg': sys.argv[0]}


def do_read_options():
    """Parse the command line thought arguments
       and throws CliError if any error.
    Returns
        - `options` : the options to give to minimerge
            They are cli parsed but action [string] is added to the oject.
            action can be one of these :

                - install
                - delete
                - reinstall
        - `args` [list] : cli left args, in fact these are the packages to deal with.
    """

    default_action = 'install'
    path = sys.exec_prefix

    offline_help = 'Build offline, do not try to connect outside.'
    debug_help = 'Run in debug mode'
    jump_help = 'Squizze prior dependencies to the '\
                'minibuild specified in that option'
    fetchonly_help = 'Fetch the packages but do not build yet'
    fetchfirst_help = 'Fetch the packages first before building them'
    delete_help = 'Remove selected packages'
    reinstall_help = 'Unconditionnaly rebuild/reinstall packages'
    install_help = 'Installs packages (default action)'
    nodeps_help = 'Squizzes all dependencies'
    config_help = 'Alternate config file. By default it\'s searched in '\
                  '%s/etc/minimerge.cfg.' % sys.exec_prefix
    pretend_help = 'Do nothing, show what will be done'
    update_help = 'Update packages from where they come '\
            'prior to compilation step automaticly'
    ask_help = 'Do nothing, show what will be done and ask to continue'
    only_dependencies_help = 'Do actions onto dependencies, do not build the given packages'
    all_python_versions_help = 'Build python bindings for all python packages present in minitage'
    upgrade_help = 'Will try to rebuild already installed sofware. if '\
            'you need to be sure that all will be rebuilt (for buildout, it runs it in new mode whereas by default, buildout is running in non newest mode, activate '\
            'also the -R flag. If you want minimerge to update '\
            'the packages from where they come, please activate '\
            'also the -U flag.'

    actions = [
        optparse.make_option('-s', '--sync',
                             action='store_true', dest='sync',
                             help = nodeps_help),
        optparse.make_option('-i', '--install',
                             action='store_true', dest='install',
                             help = install_help),
        optparse.make_option('-U', '--update',
                             action='store_true', dest='update',
                             help = update_help),
        optparse.make_option('-u', '--upgrade',
                             action='store_true', dest='upgrade',
                             help = upgrade_help),
        optparse.make_option('-R', '--reinstall',
                             action='store_true', dest='reinstall',
                             help = reinstall_help),
        optparse.make_option('-E', '--generate-env',
                             action='store_true', dest='generate_env',
                             help =  '(re)generate instance .env shell file'), 
        optparse.make_option('--rm',
                             action='store_true', dest='delete',
                             help = delete_help),
    ]
    modifiers = [
        optparse.make_option('-N', '--nodeps',
                             action='store_true', dest='nodeps',
                             help = nodeps_help),
        optparse.make_option('-j', '--jump',
                             action='store', dest='jump',
                             help = jump_help),
        optparse.make_option('-F', '--fetchonly',
                             action='store_true', dest='fetchonly',
                             help = fetchonly_help),
        optparse.make_option('-f', '--fetchfirst',
                             action='store_true', dest='fetchfirst',
                             help = fetchfirst_help),
        optparse.make_option('-k', '--use-binaries',
                             action='store_true', dest='binary',
                             help = 'Search and install binaries instead of classicly compile.'),
        optparse.make_option('-o', '--offline',
                             action='store_true', dest='offline',
                             help = offline_help),
    ]
    flags = [
        optparse.make_option('-p', '--pretend',
                             action='store_true', dest='pretend',
                             help = pretend_help),
        optparse.make_option('--only-dependencies',
                             action='store_true', dest='only_dependencies',
                             help = only_dependencies_help), 
        optparse.make_option('--all-python-versionss',
                             action='store_true', dest='all_python_versions',
                             help = all_python_versions_help),  
        optparse.make_option('-a', '--ask',
                             action='store_true', dest='ask',
                             help = ask_help),
        optparse.make_option('--skip-self-upgrade',
                             action='store_true', dest='skip_self_upgrade',
                             help = 'Do not do minitage self upgrades.'),
        optparse.make_option('--reinstall-minilays',
                             action='store_true', dest='reinstall_minilays',
                             help = 'Re download minilays.'),
        optparse.make_option('-v', '--verbose',
                             action='store_true', dest='verbose',
                             help = 'Be verbose.'),
        optparse.make_option('-c', '--config',
                             action='store', dest='config',
                             help = config_help),
        optparse.make_option('-d', '--debug',
                             action='store_true', dest='debug',
                             help = debug_help),
    ]
    parser = optparse.OptionParser(version=core.__version__, usage=usage)
    flags_group = optparse.OptionGroup(parser, 'Flags')
    modifiers_group = optparse.OptionGroup(parser, 'Modifiers')
    actions_group = optparse.OptionGroup(parser, 'Actions')
    [[group.add_option(o) for o in opts]
     for group, opts in [(actions_group, actions),
                         (modifiers_group, modifiers),
                         (flags_group, flags)]
    ]
    [parser.add_option_group(group) for group in [actions_group, modifiers_group, flags_group]]
    (options, args) = parser.parse_args()

    if (options.reinstall and options.delete) or\
       (options.fetchonly and options.offline) or \
       (options.jump and options.nodeps):
        raise core.ConflictModesError('You are using conflicting modes')

    if (not args and len(sys.argv) > 1) and not (options.sync or options.reinstall_minilays):
        message = 'You must precise which packages you want to deal with'
        raise core.NoPackagesError(message)

    if len(sys.argv) == 1:
        print 'minimerge v%s' % parser.version
        parser.print_usage()
        print '\'%s --help\' for more inforamtion on usage.' % sys.argv[0]

    actionsCount = 0
    for action in [options.reinstall, options.install, options.delete]:
        if action:
            actionsCount += 1
    if actionsCount > 1:
        message = 'You must precise only one action at a time'
        raise core.TooMuchActionsError(message)

    if options.delete:
        options.action = 'delete'
    elif options.reinstall:
        options.action = 'reinstall'
    elif options.sync:
        options.action = 'sync'
    elif options.install:
        options.action = 'install'
    elif options.generate_env:
        options.action = 'generate_env' 
    else:
        options.action = default_action

    if not options.config:
        for file in ['%s/etc/minimerge.cfg' % path, '~/.minimerge.cfg']:
            file = os.path.expanduser(file)
            if os.path.isfile(file):
                options.config = file
                break

    # be sure to be with full path object.
    if not options.config:
        message = 'The configuration file specified does not exist'
        raise core.InvalidConfigFileError(message)
    if not os.path.isfile(options.config):
        message = 'The configuration file specified does not exist'
        raise core.InvalidConfigFileError(message)
    options.config = os.path.expanduser(options.config)

    minimerge_options = {
        'action': options.action,
        'ask': options.ask,
        'config': options.config,
        'debug': options.debug,
        'fetchfirst': options.fetchfirst,
        'fetchonly': options.fetchonly,
        'jump': options.jump,
        'nodeps': options.nodeps,
        'offline': options.offline,
        'packages': args,
        'path': path,
        'pretend': options.pretend,
        'update': options.update,
        'upgrade': options.upgrade,
        'verbose': options.verbose,
        'only_dependencies': options.only_dependencies,
        'all_python_versions': options.all_python_versions,
        'reinstall_minilays': options.reinstall_minilays,
        'binary': options.binary,
        'skip_self_upgrade': options.skip_self_upgrade,
    }
    return minimerge_options

