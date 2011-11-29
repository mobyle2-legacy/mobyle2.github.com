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
import logging


from minitage.core.makers  import interfaces
import minitage.core.core
import minitage.core.common

class BuildoutError(interfaces.IMakerError):
    """General Buildout Error."""

__logger__ = 'minitage.makers.buildout'

class BuildoutMaker(interfaces.IMaker):
    """Buildout Maker.
    """
    def __init__(self, config = None, verbose=False):
        """Init a buildout maker object.
        Arguments
            - config keys:

                - options: cli args for buildout
        """
        if not config:
            config = {}
        self.logger = logging.getLogger(__logger__)
        self.config = config
        self.buildout_config = 'buildout.cfg'
        interfaces.IMaker.__init__(self)

    def match(self, switch):
        """See interface."""
        if switch == 'buildout':
            return True
        return False

    def reinstall(self, directory, opts=None):
        """Rebuild a package.
        Warning this will erase .installed.cfg forcing buildout to rebuild.
        Problem is that underlying recipes must know how to handle the part
        directory to be already there.
        This will be fine for minitage recipes in there. But maybe that will
        need boiler plate for other recipes.
        Exceptions
            - ReinstallError
        Arguments
            - directory : directory where the packge is
            - opts : arguments for the maker
        """
        mypath = os.path.join(
            directory,
            '.installed.cfg'
        )
        if os.path.exists(mypath):
            os.remove(mypath)
        self.install(directory, opts)

    def install(self, directory, opts=None):
        """Make a package.
        Exceptions
            - MakeError
        Arguments
            - dir : directory where the packge is
            - opts : arguments for the maker
        """
        self.logger.info('Running buildout in %s (%s)' % (directory,
                                                          self.buildout_config))
        cwd = os.getcwd()
        os.chdir(directory)
        bcmd = os.path.normpath('./bin/buildout')
        if not opts:
            opts = {}
        try:
            argv = []
            if opts.get('verbose', False):
                self.logger.debug('Buildout is running in verbose mode!')
                argv.append('-vvvvvvv')
            installed_cfg = os.path.join(directory, '.installed.cfg')
            if not opts.get('upgrade', True)\
               and not os.path.exists(installed_cfg):
                argv.append('-N')
            if opts.get('upgrade', False):
                self.logger.debug('Buildout is running in newest mode!')
                argv.append('-n')
            if opts.get('offline', False):
                self.logger.debug('Buildout is running in offline mode!')
                argv.append('-o')
            if opts.get('debug', False):
                self.logger.debug('Buildout is running in debug mode!')
                argv.append('-D')
            parts = opts.get('parts', False)
            if isinstance(parts, str):
                parts = parts.split()

            minibuild = opts.get('minibuild', None)
            category = ''
            if minibuild: category = minibuild.category
            # Try to upgrade only if we need to
            # (we chech only when we have a .installed.cfg file
            if not opts.get('upgrade', True)\
               and os.path.exists(installed_cfg) and (not category=='eggs'):
                self.logger.info('Buildout will not run in %s'
                                  ' as there is a .installed.cfg file'
                                  ' indicating us that the software is already'
                                  ' installed but minimerge is running in'
                                  ' no-update mode. If you want to try'
                                  ' to update/rebuild it unconditionnaly,'
                                  ' please relaunch with -uUR.' % directory)
                return


            # running buildout in our internal way
            # always regenerating that buildout file
            #if not os.path.exists(
            #    os.path.join(
            #        directory,
            #        'bin',
            #        'buildout')):
            bootstrap_args = ''
            if os.path.exists('bootstrap.py'):
                # if this bootstrap.py supports distribute, just use it!
                content = open('bootstrap.py').read()
                if '--distribute' in content:
                    self.logger.warning('Using distribute !')
                    bootstrap_args += ' %s ' % '--distribute'
                bootstrap_args += ' -c %s ' % self.buildout_config
                minitage.core.common.Popen(
                    '%s bootstrap.py %s ' % (sys.executable, bootstrap_args,),
                    opts.get('verbose', False)
                )
            else:
                minitage.core.common.Popen(
                    'buildout bootstrap -c %s' % self.buildout_config,
                    opts.get('verbose', False)
                )
            if parts:
                for part in parts:
                    self.logger.info('Installing single part: %s' % part)
                    minitage.core.common.Popen(
                        '%s -c %s %s install %s ' % (
                            bcmd,
                            self.buildout_config,
                            ' '.join(argv),
                            part
                        ),
                        opts.get('verbose', False)
                    )
            else:
                self.logger.debug('Installing parts')
                minitage.core.common.Popen(
                    '%s -c %s  %s ' % (
                        bcmd,
                        self.buildout_config,
                        ' '.join(argv),
                    ),
                    opts.get('verbose', False)
                )
        except Exception, instance:
            os.chdir(cwd)
            raise BuildoutError('Buildout failed:\n\t%s' % instance)
        os.chdir(cwd)

    def get_options(self, minimerge, minibuild, **kwargs):
        """Get python options according to the minibuild and minimerge instance.
        For eggs buildouts, we need to know which versions of python we
        will build site-packages for
        For parts, we force to install only the 'part' buildout part.
        Arguments
            - we can force parts with settings 'buildout_parts' in minibuild
            - minimerge a minitage.core.Minimerge instance
            - minibuild a minitage.core.object.Minibuild instance
            - kwargs:

                - 'python_versions' : list of major.minor versions of
                  python to compile against.
        """
        options = {}
        parts = self.buildout_config = [a.strip() 
                                        for a in minibuild.minibuild_config._sections[
                                            'minibuild'].get('buildout_parts', '').split()] 
        if kwargs is None:
            kwargs = {}

        # if it s an egg, we must install just the needed
        # site-packages if selected
        if minibuild.category == 'eggs':
            vers = kwargs.get('python_versions', None)
            if not vers:
                vers = minitage.core.core.PYTHON_VERSIONS
            parts = ['site-packages-%s' % ver for ver in vers]

        options['parts'] = parts
        self.buildout_config = minibuild.minibuild_config._sections[
            'minibuild'].get('buildout_config',
                             'buildout.cfg')


        # prevent buildout from running if we have already installed stuff
        # and do not want to upgrade.
        options['upgrade'] = minimerge.getUpgrade()
        if minimerge.has_new_revision(minibuild):
            options['upgrade'] = True

        return options

# vim:set et sts=4 ts=4 tw=80:
