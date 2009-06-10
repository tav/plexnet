# This file has been placed into the Public Domain by:
#
#   tav <tav@espians.com>
#
# See documentation/license.txt for more info.

"""A standalone target for the Naaga interpreter."""

import pypypath
import pypy_startup
pypy_startup.patch()

from pypy.translator.goal.targetpypystandalone import *
