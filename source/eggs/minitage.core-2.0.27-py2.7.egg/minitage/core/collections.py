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

class LazyLoadedList(list):
    """Just in time objects loading"""

    def __init__(self, *kw, **kwargs):
        list.__init__(self)
        self.loaded = False

    def isLoaded(self):
        """returns True is the minilay has been loaded"""
        return self.loaded

    def load(self):
        """method for lazyloading a list"""
        if not self.isLoaded():
            # do load processing there
            self.loaded = True

    def __getitem__(self, indice):
        """lazy loading items"""
        if not self.isLoaded():
            self.load()
        return list.__getitem__(self, indice)

    def __getslice__(self, start=None, stop=None):
        """lazy loading items"""
        if not self.isLoaded():
            self.load()
        return list.__getslice__(self, start, stop)

    def __contains__(self, item):
        """lazy loading items"""
        if not self.isLoaded():
            self.load()
        return list.__contains__(self, item)

    def index(self, item):
        """lazy loading items"""
        if not self.isLoaded():
            self.load()
        return list.index(self, item)

class LazyLoadedDict(dict):
    """Just in time objects loading"""

    def __init__(self):
        """returns True is the minilay has been loaded"""
        dict.__init__(self)
        self.items = []
        self.loaded = False

    def load(self, item = None):
        """method for lazyloading a list"""
        # do load processing there
        # 3 = 1 + 1
        # marking as loaded
        # 0 is valid
        if item is not None:
            self.items.append(item)
            self.loaded = True

    def __getitem__(self, item):
        """lazy loading items"""
        if not item in self.items:
            self.load(item)
        return dict.__getitem__(self, item)

    def __contains__(self, item):
        """lazy loading items"""
        if not item in self.items:
            self.load(item)
        return dict.__contains__(self, item)

