# -*- coding: utf-8 -*-

u"""
============================
Unicode Case Folding Support
============================

This module generates a CASE_MAP dictionary which maps upper case characters to
lower case characters according to the Unicode 5.1 Specification:

    >>> CASE_MAP[u'B']
    u'b'

Note that some codepoints may lower case into multi-byte characters, e.g.

    >>> CASE_MAP[u'ß']
    u'ss'

"""

from os.path import abspath, dirname, exists, join as join_path
from sys import maxunicode
from plexnetenv import PLEXNET_LOCAL

# ------------------------------------------------------------------------------
# some konstants
# ------------------------------------------------------------------------------

CASE_MAP = {}

# ------------------------------------------------------------------------------
# utility funktions
# ------------------------------------------------------------------------------

def _generate_case_map():

    global CASE_MAP

    if CASE_MAP:
        return

    filepath = join_path(PLEXNET_LOCAL, 'share', 'unicode', 'case_folding.txt')

    if not exists(filepath):
        raise RuntimeError(
            "Couldn't find Unicode Case Folding data: %r" % filepath
            )

    if maxunicode == 0xffff:
        def _chr(s):
            return eval("u'\U" + ('0' * (8 - len(s))) + s + "'")
    else:
        def _chr(s):
            return unichr(int(s, 16))

    with open(filepath, 'r') as case_data:
        for line in case_data:
            if line.startswith('#') or (not line.strip()):
                continue
            ori, typ, dst, cmt = line.split('; ')
            if typ in ('C', 'F'):
                CASE_MAP[_chr(ori)] = u''.join(_chr(char) for char in dst.split(' '))

_generate_case_map()
