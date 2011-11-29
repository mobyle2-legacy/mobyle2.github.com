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

import ConfigParser
import os

class InterfaceError(Exception):
    """eneral Interface Error."""


class InvalidConfigForFactoryError(InterfaceError):
    """Invalid config file Error."""

class InvalidComponentClassPathError(InterfaceError):
    """Component class path was not found."""


class InvalidComponentClassError(InterfaceError):
    """Component Class is not valid."""

class IFactory(object):
    """Interface implementing the design pattern 'factory'.
    Basics
        To register a new fetcher to the factory you ll have 2 choices:
            - Indicate something in a config.ini file and give it to the
              instance initialization.
              Example::
                    [fetchers]
                    type=mymodule.mysubmodule.MyFetcherClass

            - register it manually with the .. function::register
              Example::
                >>> factory.register('svn', 'module.fetchcher.NiceSvnFetcher')

    Attributes
    - products : dictionary:
        { src_type : IFetcher instance}

    """

    def __init__(self, name, config=None):
        """
        Arguments:
            - config: a configuration file with a self.name section
                    containing all needed classes.
        """
        self.name = 'minitage.%s' % name
        self.config = ConfigParser.ConfigParser()
        self.section = {}
        self.sections = {}
        self.products = {}
        if config:
            try:
                if isinstance(config, str):
                    if os.path.exists(config):
                        self.config.read(config)
                        self.sections = self.config._sections
                    else:
                        self.sections = {self.name: {}}
                else:
                    self.sections = config
                for section in self.sections:
                    if '__name__' in self.sections[section]:
                        del self.sections[section]['__name__']
                self.section = self.sections[self.name]
            except KeyError, e:
                message = 'You must provide a [%s] section with '\
                        ' appropriate content for this factory.\n'
                raise InvalidConfigForFactoryError(message % (self.name))

        # for each class in the config File, try to instantiate and register
        # the type/plugin in the factory dict.
        self.registerDict(self.section)

    def registerDict(self, d):
        """For each item/class in the dict:
        Try to instantiate and register.
        Arguments:
            - dict : dictionnary {item:class}
        Exceptions:
            - InvalidComponentClassPathError
        """
        # the type/plugin in the factory dict.
        #
        for key in d:
            try:
                smodule, sklass = d[key].strip().split(':')
                module = __import__(smodule, None, None, [''])
                klass = getattr(module, sklass)
            except Exception:
                message = 'Invalid Component: \'%s/%s\'' % (key, d[key])
                raise InvalidComponentClassPathError(message)
            self.register(key, klass)

    def register(self, ltype, klass):
        """Register a product with its factory.
        Arguments
            - type: type to register
            - klass: klass the factory must intanciate
        """
        # little check that we have instance
        if not  isinstance(klass, str):
            self.products[ltype] = klass
        else:
            message = 'Invalid Component: \'%s/%s\' ' % (ltype, klass)
            message += 'does not point to a valid class.'
            raise InvalidComponentClassError()

    def __call__(self, switch):
        """Possibly instanciate and return a product.
        Implementation Exameple::
            for key in self.products:
                 klass = self.products[key]
                 instance = klass(self.sections.get(switch, {}))
                 if instance.match(switch):
                     return instance
        """
        raise NotImplementedError('The method is not implemented')

class IProduct(object):
    """factory result"""

    def match(self, switch):
        """Select the product if match.
        Arguments:
            - switch: parameter which will be used to know if the component can
            handle the request.
        Return:
            - boolean: wheither the product can be used.
        """
        raise NotImplementedError('The method is not implemented')

# vim:set et sts=4 ts=4 tw=80:
