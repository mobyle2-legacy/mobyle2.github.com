#!/usr/bin/env python
__docformat__ = 'restructuredtext en'

import sys
import os
import re
import shutil

from minitage.core.cli import do_read_options
from minitage.core import core
from minitage.core.common import first_run

def launch():
    try:
        prefix = os.path.abspath(sys.exec_prefix)
        config = os.path.join(prefix, 'etc', 'minimerge.cfg')
        firstrun = False
        if not os.path.isfile(config):
            firstrun = True
            first_run()
        options = do_read_options()
        options['first_run'] = firstrun
        minimerge = core.Minimerge(options)
        minimerge.main()
    except Exception, e:
        #raise
        sys.stderr.write('Minimerge executation failed:\n')
        sys.stderr.write('\t%s\n' % e)

# vim:set ft=python sts=4 ts=4 tw=80 et:
