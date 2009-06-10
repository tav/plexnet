# For external projects that want a "svn:externals" link
# to greenlets, please use the following svn:externals:
#
#     greenlet http://codespeak.net/svn/greenlet/trunk/c
#
# This file is here to have such a case work transparently
# with auto-compilation of the .c file.  It requires the
# py lib, however.

import py as _py
_path = _py.path.local(__file__).dirpath().join('_greenlet.c')
_module = _path._getpymodule()
globals().update(_module.__dict__)
