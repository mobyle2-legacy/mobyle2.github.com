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
import shutil
import logging


from minitage.core import interfaces

class IMakerError(Exception):
    """General Maker Error."""


class MakeError(IMakerError):
    """Make runtime error."""


class DeleteError(IMakerError):
    """Delete runtime error."""


class ReinstallError(IMakerError):
    """Reinstall runtime error."""

__logger__ =  'minitage.core.makers.interfaces'

class IMakerFactory(interfaces.IFactory):
    """Factory for makers utilities."""

    def __init__(self, config=None):
        """
        Arguments:
            - config: a configuration file with a self.name section
                    containing all needed classes.
        """

        interfaces.IFactory.__init__(self, 'makers', config)
        self.registerDict(
            {
                'buildout': 'minitage.core.makers.buildout:BuildoutMaker',
            }
        )

    def __call__(self, switch):
        """Return a maker.
        Arguments:
            - switch: maker type
              Default ones:

                -buildout: buildout
        """
        for key in self.products:
            klass = self.products[key]
            instance = klass(self.sections.get(switch, {}))
            if instance.match(switch):
                return instance


class IMaker(interfaces.IProduct):
    """Interface for making a package from somewhere.
    Basics
         To register a new maker to the factory you ll have 2 choices:
             - Indicate something in a config.ini file and give it to the
               instance initialization.
               Example::
                   [makers]
                   type=mymodule.mysubmodule.MyMakerClass

             - register it manually with the .. function::register
               Example::
                   >>> klass = getattr(module,'superklass')
                   >>> factory.register('svn', klass)

    What a maker needs to be a maker
        Locally, the methods in the interfaces ;)
        Basically, it must implement
            - make, delete, reinstall, match
    """

    def delete(self, directory, opts=None):
        """Delete a package.
        Exceptions:
            - DeleteError
        Arguments:
            - dir : directory where the packge is
            - opts : arguments for the maker
        """
        logger = logging.getLogger(__logger__)
        logger.info('Uninstalling %s' % directory)
        if os.path.isdir(directory):
            try:
                shutil.rmtree(directory)
                logger.info('Uninstalled %s' % directory)
            except:
                raise DeleteError('Cannot remove \'%s\'' % directory)

    def reinstall(self, directory, opts):
        """Rebuild a package.
        Exceptions:
            - ReinstallError
        Arguments:
            - directory : directory where the packge is
            - opts : arguments for the maker
        """
        raise NotImplementedError('The method is not implemented')

    def install(self, directory, ops=None):
        """Make a package.
        Exceptions:
            - MakeError
        Arguments:
            - dir : directory where the packge is
            - opts : arguments for the maker
        """
        raise NotImplementedError('The method is not implemented')

    def match(self, switch):
        """Return true if the product match the switch."""
        raise NotImplementedError('The method is not implemented')


    def get_options(self, minimerge, minibuild, **kwargs):
        """Return a dict of needed options
        according to a minibuild and a minimerge instance and for the other
        packages to be built in the session."""
        raise NotImplementedError('The method is not implemented')

# vim:set et sts=4 ts=4 tw=80:
