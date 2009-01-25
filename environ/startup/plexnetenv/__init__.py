"""Setup the common environment needed by scripts."""

import sys

from os.path import dirname, abspath, join as join_path

STARTUP_DIRECTORY = dirname(dirname(abspath(__file__)))
PLEXNET_ROOT = dirname(dirname(STARTUP_DIRECTORY))
PLEXNET_LOCAL = join_path(PLEXNET_ROOT, 'environ', 'local')
PLEXNET_SOURCE = join_path(PLEXNET_ROOT, 'source')
THIRD_PARTY = join_path(PLEXNET_ROOT, 'third_party')
PYTHON_SITE_PACKAGES = join_path(PLEXNET_ROOT, 'third_party', 'python')

if PYTHON_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, PYTHON_SITE_PACKAGES)

if PLEXNET_SOURCE not in sys.path:
    sys.path.insert(0, PLEXNET_SOURCE)
