"""
==================================================
Constructs to Support Capability-style Programming
==================================================

This module provides a basic framework to support capability-style programming
within Python. Capabilities are just object references which cannot be faked and
security is made available due to objects not having references that they do not
need to have.

Security can easily be achieved in Python thanks to closures. And objects can be
attained through the use of nested functions.

Python's class-based objects can easily be mimicked thanks to the use of the
provided ``Namespace``:

    >>> def Point(x, y):
    ...
    ...     __doc__ = 'A Point object.'
    ...     __type__ = 'Point'
    ...
    ...     def __str__():
    ...         return '%s(%s, %s)' % (__type__, x, y)
    ...
    ...     __repr__ = __str__
    ...
    ...     def getX():
    ...         return x
    ...
    ...     def getY():
    ...         return y
    ...
    ...     def __add__(other):
    ...         return Point(x + other.getX(), y + other.getY())
    ...
    ...     def __call__():
    ...         print('woo!')
    ...
    ...     return Namespace()

    >>> x = Point(1, 2)

    >>> x
    Point(1, 2)

    >>> x.getX()
    1

    >>> x.getY()
    2

    >>> y = Point(3, 4)

    >>> x + y
    Point(4, 6)

"""

from sys import _getframe as get_frame
from types import FunctionType

from ..util.optimise import _make_constants

__all__ = ['Namespace', 'copy_namespace', 'is_namespace', 'This']

# ------------------------------------------------------------------------------
# sekure namespase
# ------------------------------------------------------------------------------

class NamespaceContext(type):
    """A Namespace Context metaclass."""

    def __call__(klass, __getter):
        for name, obj in __getter:
            setattr(klass, name, obj)
        return type.__call__(klass, __getter)

    def __str__(klass):
        return 'NamespaceContext%s' % (tuple(klass.__dict__.keys()),)

def copy_namespace(namespace):
    """Return a secure copy of the given ``namespace``."""

    if namespace.__class__.__metaclass__ != NamespaceContext:
        raise TypeError("You can only copy a Namespace object.")

    class NamespaceObject(tuple):

        __metaclass__ = NamespaceContext
        __slots__ = ()

        def __new__(klass, __getter):
            return tuple.__new__(klass, __getter)

    # @/@ should we .copy() all dict/set instances?
    return NamespaceObject(tuple(tuple.__iter__(namespace)))

def is_namespace(object):
    """Return whether a given object is a valid NamespaceObject."""

    return object.__class__.__metaclass__ is NamespaceContext

def _Namespace():

    __private_data = {}

    def Namespace(*args, **kwargs):
        """Return a Namespace from the current scope or the given arguments."""

        class NamespaceObject(tuple):

            __metaclass__ = NamespaceContext
            __slots__ = ()

            def __new__(klass, __getter):
                return tuple.__new__(klass, __getter)

        ns_items = []; populate = ns_items.append

        if args or kwargs:

            frame = None

            for arg in args:
                kwargs[arg.__name__] = arg

            for name, obj in kwargs.iteritems():
                if isinstance(obj, FunctionType):
                    populate((name, staticmethod(obj)))
                else:
                    populate((name, obj))

        else:

            frame = get_frame(1)

            for name, obj in frame.f_locals.iteritems():
                if isinstance(obj, FunctionType):
                    if not (name.startswith('_') and not name.startswith('__')):
                        populate((name, staticmethod(obj)))
                elif name.startswith('__') and name.endswith('__'):
                    populate((name, obj))

        del frame, args, kwargs

        # @/@ what should we do with __doc__ and __name__ ??

        return NamespaceObject(ns_items)

    return Namespace

Namespace = _make_constants(_Namespace())

del _Namespace

class This(object):
    """A simple namespace for use as `this`` within closures."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

from _capbase import Namespace
