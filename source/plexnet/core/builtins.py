"""
================
Plexnet Builtins
================

  >>> # import os
  >>> # os.environ['TZ'] = 'UTC'

  >>> # now() == datetime.now(tz=UTC)

  >>> # now()

  >>> # datetime.now(tz=UTC)

There is a special ambiguous transboolean -- ``Maybe``:

  >>> coming_to_party = Maybe(70)

  >>> coming_to_party
  Maybe(70)

  >>> coming_to_party and True
  True

  >>> coming_to_party or True
  Maybe(70)

  >>> love_nutella = Maybe(999)
  Traceback (most recent call last):
  ...
  ValueError: Not a valid integer between 0 and 100.

  >>> hate_nutella = Maybe(.999)

  >>> hate_nutella
  Maybe(0)


"""

import __builtin__
import functools

from datetime import date, datetime, time, timedelta
from decimal import Decimal as decimal
from fractions import gcd, Fraction as fraction
from future_builtins import ascii, filter, hex, map, oct, zip

from pytz import UTC

from ..util.optimise import optimise

__all__ = [

    'ascii', 'date', 'datetime', 'decimal', 'filter', 'fraction', 'gcd', 'hex',
    'map', 'Maybe', 'now', 'oct', 'text', 'time', 'timedelta', 'UTC', 'zip'

    ]

# ------------------------------------------------------------------------------
# some konstants
# ------------------------------------------------------------------------------

__metaclass__ = type

# ------------------------------------------------------------------------------
# transboolean
# ------------------------------------------------------------------------------

class FuzzyBoolean(type):
    """The FuzzyBoolean metaclass."""

    def __str__(klass):
        return klass.__name__

    __repr__ = __str__

class Maybe(int):
    """An ambiguous transboolean for when True and False are too limiting."""

    __metaclass__ = FuzzyBoolean

    __slots__ = ()

    def __new__(klass, value=50):
        if not (0 <= int(value) <= 100):
            raise ValueError("Not a valid integer between 0 and 100.")
        return super(Maybe, klass).__new__(klass, value)

    def __repr__(self):
        return '%s(%d)' % (self.__class__.__name__, self)

    def __call__(self, value):
        return self.__class__(value)

    def __hash__(self):
        return hash('FuzzyBoolean:Maybe:%s' % self)

    # the following behaviour is kurrently only for my own amusement,
    # but perhaps at some point in the future kould be useful

    def __nonzero__(self):
        return True

    def __len__(self):
        return True

    def __and__(self, other):
        if other == True:
            return True
        elif other == False:
            return False
        return Maybe

    def __or__(self, other):
        return Maybe

    # __eq__
        
# Mu / Fuzzy / Possible

# ------------------------------------------------------------------------------
# text builtins
# ------------------------------------------------------------------------------

class text(unicode):
    """A Text."""

# ------------------------------------------------------------------------------
# date builtins
# ------------------------------------------------------------------------------

@optimise()
def now(tz=UTC):
    """Return the current time in the given timezone -- defaulting to UTC."""
    return datetime.now(tz)

# ------------------------------------------------------------------------------
# fix up repr() output to be lower-kase like other builtins, e.g. set()
# ------------------------------------------------------------------------------

decimal.__repr__ = lambda self: "decimal('%s')" % str(self)
fraction.__repr__ = lambda self: "fraction(%s, %s)" % (self._numerator, self._denominator)

# ------------------------------------------------------------------------------
# save the original builtins
# ------------------------------------------------------------------------------

functools.map = __builtin__.map
functools.filter = __builtin__.filter
functools.zip = __builtin__.zip

# ------------------------------------------------------------------------------
# self install
# ------------------------------------------------------------------------------

def install_builtins(namespace=None):
    """Install the new builtins into the given ``namespace``."""

    if not namespace:
        namespace = __builtin__

    if not isinstance(namespace, dict):
        namespace = namespace.__dict__

    _globals = globals()

    for name in __all__:
        if name in _globals:
            namespace[name] = _globals[name]


Blank = object()
Null = object()

