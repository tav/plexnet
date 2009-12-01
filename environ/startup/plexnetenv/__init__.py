# Released into the Public Domain. See documentation/legal.txt for more info.
# Author: tav <tav@espians.com>

"""Setup the common environment needed by scripts."""

import sys

from os.path import dirname, abspath, join as join_path

STARTUP_DIRECTORY = dirname(dirname(abspath(__file__)))
PLEXNET_ROOT = dirname(dirname(STARTUP_DIRECTORY))
PLEXNET_LOCAL = join_path(PLEXNET_ROOT, 'environ', 'local')
PLEXNET_SOURCE = join_path(PLEXNET_ROOT, 'source')
THIRD_PARTY = join_path(PLEXNET_ROOT, 'third_party')
PYTHON_SITE_PACKAGES = join_path(PLEXNET_ROOT, 'third_party', 'python')
DEPOT_TOOLS = join_path(PLEXNET_ROOT, 'third_party', 'generic', 'depot_tools')

for path in [
    DEPOT_TOOLS, PYTHON_SITE_PACKAGES, PLEXNET_SOURCE
    ]:
    if path not in sys.path:
        sys.path.insert(0, path)
