"""
Plexnet -- A Set of Open Web Standards.

.. class:: center
..

   ::

                    ___                                    __
                   /\_ \                                  /\ \__
              _____\//\ \      __   __  _   ______      __\ \ ,_\
             /\ '__`\\ \ \   /'__`\/\ \/'\/' '__ ,`\  /'__`\ \ \/
             \ \ \/\ \\_\ \_/\  __/\/>  </\ \ \ \ \ \/\  __/\ \ \_
              \ \ ,__//\____\ \____\/\_/\_\\ \_\ \ \_\ \____\\ \__\
               \ \ \/ \/____/\/____/\//\/_/ \/_/  \/_/\/____/ \/__/
                \ \_\                      
                 \/_/                      


This is an implementation of the Plexnet demonstrating its benefits in the here
and now. See the ``documentation`` directory for more info.

-- 
Enjoy, tav

"""

from __future__ import absolute_import

__copyright__ = (
    "Public Domain",
    "See documentation/LICENSE.txt for more info."
    )

__authors__ =  {
    0x01: ('tav', 'tav@espians.com'),
    0x02: ('sbp', 'sean@miscoranda.com'),
    0x03: ('oierw', 'mathew.ryden@gmail.com'),
    0x04: ('Killarny', 'killarny@gmail.com'),
    0x05: ('evangineer', 'mamading@gmail.com'),
    }

__maintainer__ = __authors__[1]

__version__ = (0, 1)
__release__ = '.'.join(map(str, __version__))

__moreinfo__ = ("http://www.plexnet.org", "plex:ocsi/plexnet")

# ------------------------------------------------------------------------------
# setup the ``settings`` module
# ------------------------------------------------------------------------------

from .util.modulesetup import setup_dummy_module

setup_dummy_module('settings', "A global registry").cache = {}

# ------------------------------------------------------------------------------
# set us up the plexnet!
# ------------------------------------------------------------------------------

def setup(debug=0):
    """Setup base infrastructure needed for a working Plexnet environment."""

    import settings
    settings.debug = debug

    from .util.secure import secure_python
    secure_python()
