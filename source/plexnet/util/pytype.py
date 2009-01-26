"""
============
Python Types
============

Base types of Python builtins -- for use with ``type`` and ``isinstance``.

-------------
Introspection
-------------

Python offers a host of useful introspective capabilities. And one of the most
useful features is its dynamic typing and type querying:

  >>> a_list = ['a', 'list']

  >>> type(a_list)
  <type 'list'>

  >>> type(a_list) is list
  True

  >>> isinstance(a_list, list)
  True

  >>> isinstance(a_list, tuple)
  False

  >>> isinstance(a_list, SequenceType)
  True

  >>> def message_generator(message):
  ...     for char in message:
  ...         yield char

  >>> hello_generator = message_generator('hello world')

  >>> isinstance(hello_generator, GeneratorType)
  True

------
Typing
------

But unlike many other language users, Pythonistas aren't always so picky about
their typing. In fact, one of the revered traditions is that of ``Duck Typing``
-- if it walks like a duck and quacks like a duck, then it is assumed to be a
duck.

Thus it becomes more a matter of interface and protocol than object type. E.g.
dictionaries are a mapping since they support keys(), __getitem__() and a bunch
of other operations, and not because they are derived from a particular BaseDict
type.

Unlike within certain languages these interfaces are gentlemanly agreements and
not explicitly enforced.

And perhaps the most commonly used protocol in modern Python code is that of the
``iterator``. Introduced in PEP 234, these iterators have so far proven to be a
very useful programming construct. And according to the PEP:

    1. An object can be iterated over with ``for`` if it implements
       __iter__() or __getitem__().

    2. An object can function as an iterator if it implements next().

    Container-like objects usually support protocol 1. Iterators are
    currently required to support both protocols. The semantics of
    iteration come only from protocol 2; protocol 1 is present to make
    iterators behave like sequences; in particular so that code
    receiving an iterator can use a for-loop over the iterator.

These requirements have been encapsulated in the ``is_an_iterator`` function:

  >>> is_an_iterator(a_list)
  True

  >>> is_an_iterator(iter(a_list))
  True

  >>> is_an_iterator(hello_generator)
  True

-------------------
Integer Unification
-------------------

It is also worth bearing in mind that following PEP 237, we now have ``int`` and
``long`` integer unification. Of sorts.

The type distinction will remain till Python 3.0:

  >>> from sys import maxint

  >>> isinstance(maxint, int)
  True

  >>> isinstance(maxint, long)
  False

However, ints are now automatically converted into a ``long`` instead of raising
an OverflowError when the typical 32-bit or 64-bit limit of the underlying C
integer is reached.

This can lead to the paradoxical behaviour of the ``int`` constructor returning
a long:

  >>> max_plus_one = int(maxint + 1)

  >>> isinstance(max_plus_one, int)
  False

  >>> isinstance(max_plus_one, long)
  True

As useful as it is, this dynamic typing can prove occasionally problematic if
one should forget about it.

And thus ``baseinteger``. It mirrors ``basestring``, and can be used within
``isinstance`` checks:

  >> isinstance(max_plus_one, baseinteger)
  True

  >>> isinstance(maxint, baseinteger)
  True

-------------
Bulitin Types
-------------

Since the advent of class/type unification in Python 2.2, many of the builtin
types have been exposed directly, e.g. ``str``, ``int``, &c. and thus there is
no need to duplicate them here.

-------------------
Functions & Methods
-------------------

Both bound and unbound methods are in reality the exact same.

They simply have different representations depending on whether the ``im_self``
field is set.

  @/@ ehm, classic class work like this?

  a_classic_class.__dict__['a_method'] <--- <function>
  a_classic_class.a_method.im_func <--- <function>
  a_classic_class.a_method.im_self <--- None
  a_classic_class().a_method.im_self <--- <the-instance>

"""

import socket
import sys

from types import FunctionType # needed for secure.py patching
from weakref import ProxyTypes, ReferenceType

#pimp('builtin/fuzzylogic', 'Maybe')
#pimp('builtin/weakref', 'weakpointer', 'saferef')

# ------------------------------------------------------------------------------
# built-in types
# ------------------------------------------------------------------------------

NoneType = type(None)

# 'str'
# 'unicode'
# 'basestring'

# 'bool'

#BooleanType = (bool, Maybe)
BooleanType = bool

# 'tuple'
# 'list'
# 'dict'
# 'set'
# 'frozenset'

SequenceType = (list, tuple, set, frozenset)

# 'int'
# 'long'
# 'float'
# 'complex' -- may not be compiled
# 'decimal'

if sys.version_info >= (3, 0):
    baseinteger = int
    NumericType = int
else:
    baseinteger = (int, long) # mirroring ``basestring``
    NumericType = (int, long, float, complex)

# 'file'

# 'slice'
# 'xrange'

EllipsisType = type(Ellipsis)

# 'buffer'

# ------------------------------------------------------------------------------
# what be modules made of?
# ------------------------------------------------------------------------------

ModuleType = type(sys)

# ------------------------------------------------------------------------------
# them types that relate to klasses -- relating to kisses be niser though
# ------------------------------------------------------------------------------

# object
# type

class a_classic_class:
    def a_method(self):
        pass

ClassicClassType = type(a_classic_class) # classobj
ClassType = (type, ClassicClassType)

InstanceType = type(a_classic_class())

# ------------------------------------------------------------------------------
# and our kallables?
# ------------------------------------------------------------------------------

def a_function():
    pass

FunctionType = type(a_function)
LambdaType = type(lambda: None) # same as FunctionType

if sys.version_info >= (3, 0):
    CodeType = type(a_function.__code__)
else:
    CodeType = type(a_function.func_code)

UnboundMethodType = type(a_classic_class.a_method) # instancemethod
MethodType = type(a_classic_class().a_method) # the same instancemethod

BuiltinFunctionType = type(len)
BuiltinMethodType = type([].append)
BuiltinMethodWrapperType = type(len.__call__)

def a_generator():
    yield "something"

GeneratorType = type(a_generator())

# ------------------------------------------------------------------------------
# let's play with mr. sok -- sok me off darling
# ------------------------------------------------------------------------------

SocketType = socket.SocketType

# ------------------------------------------------------------------------------
# let's weakref it babeh!
# ------------------------------------------------------------------------------

#WeakrefType = (ReferenceType, saferef, weakpointer)
WeakrefType = ReferenceType

DictProxyType = type(type.__dict__)

# ------------------------------------------------------------------------------
# the other types in python heaven
# ------------------------------------------------------------------------------

NotImplementedType = type(NotImplemented)

# ------------------------------------------------------------------------------
# but for them ekseptions
# ------------------------------------------------------------------------------

# Exception

try:
    raise TypeError
except TypeError:
    try:
        tb = sys.exc_info()[2]
        TracebackType = type(tb)
        FrameType = type(tb.tb_frame)
    except AttributeError:
        # in restricted environments, exc_info returns (None, None, None).
        # then, tb.tb_frame gives an attribute error
        pass
    tb = None; del tb

# ------------------------------------------------------------------------------
# duk typing -- if it walks and quaks like a duk is it a duk?
# ------------------------------------------------------------------------------

def is_an_iterator(obj):
    """Return whether an object supports the iterator protocol."""

    return (
        hasattr(obj, 'next') and hasattr(obj, '__iter__')
        or hasattr(obj, '__getitem__')
        )

# ------------------------------------------------------------------------------
# kleanups -- making pimp/import ``*`` safe
# ------------------------------------------------------------------------------

del a_classic_class, a_function, a_generator

del socket, sys
