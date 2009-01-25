r"""
=========================
Secure Python Interpreter
=========================

Python is capable of supporting secure capability-style programming through the
use of closures. However, Python's introspective qualities -- which is one of
its strengths -- leaks references to variables closed over by closures through
certain attributes of builtin types.

As a simple example, consider the following:

  >>> from hashlib import sha1

  >>> def create_hasher(secret):
  ...      def get_digest(value):
  ...          return sha1(secret + value).hexdigest()
  ...      return get_digest

  >>> get_digest = create_hasher(secret='nutella')

The ``get_digest`` function could now be passed to untrusted code and ideally
the untrusted code would not be able to use Python's introspective capabilities
to discover the value of ``secret``.

Unfortunately, this is easily accessible:

  >>> if sys.version_info >= (2, 6):
  ...     get_digest.__closure__[0].cell_contents
  ... else:
  ...     get_digest.func_closure[0].cell_contents
  'nutella'

The ``secure_python`` function in this module fixes this by removing certain
attributes from some of Python's builtin types:

  >>> def functiontype_hasattr(attr):
  ...     if sys.version_info >= (2, 6):
  ...         return hasattr(FunctionType, FUNCTION_PY26_ATTRS[attr])
  ...     return hasattr(FunctionType, attr)

  >>> functiontype_hasattr('func_code')
  True
  >>> functiontype_hasattr('func_closure')
  True
  >>> functiontype_hasattr('func_globals')
  True
  >>> hasattr(type, '__subclasses__')
  True
  >>> hasattr(GeneratorType, 'gi_code')
  True

After ``secure_python`` is run, these attributes are no longer directly
accessible:

  >>> secure_python()

  >>> functiontype_hasattr('func_code')
  False
  >>> functiontype_hasattr('func_closure')
  False
  >>> functiontype_hasattr('func_globals')
  False
  >>> hasattr(type, '__subclasses__')
  False
  >>> hasattr(GeneratorType, 'gi_code')
  False
  >>> hasattr(GeneratorType, 'gi_frame')
  False

You can now safely pass along closures to untrusted code -- secure in the
knowledge that it won't be able to access closed over *private* variables:

  >>> if sys.version_info >= (2, 6):
  ...     get_digest.__closure__[0].cell_contents
  ... else:
  ...     get_digest.func_closure[0].cell_contents
  Traceback (most recent call last):
  ...
  AttributeError: 'function' object has no attribute '...closure...'

However, accessing the various removed attributes of FunctionType is still
useful for trusted code. To cater for this, specific getters are added to the
``sys`` module:

* sys.get_func_closure
* sys.get_func_code
* sys.get_func_globals

So you can still access *private* data in trusted code, e.g.

  >>> sys.get_func_closure(get_digest)[0].cell_contents
  'nutella'

  >>> sys.get_func_globals(get_digest) == globals()
  True

  >>> from types import CodeType
  >>> isinstance(sys.get_func_code(get_digest), CodeType)
  True

  >>> class DictSubClass(dict):
  ...     pass

  >>> DictSubClass in sys.get_subclasses(dict)
  True

This makes the reasonable assumption that *trusted* code will be able to import
the ``sys`` module and untrusted code will not have access to ``sys``.

The ``secure_python`` function automatically patches various functions within
the standard library which access attributes like ``func_code``:

  >>> def _test_function(x, y=3):
  ...     x += 1
  ...     return x + y

  >>> import dis
  >>> dis.dis(_test_function) # careful with the whitespace in the test
    2           0 LOAD_FAST                0 (x)
                3 LOAD_CONST               1 (1)
                6 INPLACE_ADD         
                7 STORE_FAST               0 (x)
  <BLANKLINE>
    3          10 LOAD_FAST                0 (x)
               13 LOAD_FAST                1 (y)
               16 BINARY_ADD          
               17 RETURN_VALUE        

  >>> import inspect

  >>> inspect.getargspec(_test_function) ==  (['x', 'y'], None, None, (3,))
  True

  >>> def _test_generator():
  ...     while 1:
  ...         yield None
  
  >>> if sys.version_info >= (2, 6):
  ...     inspect.isgeneratorfunction(_test_generator)
  ... else:
  ...     True
  True

  >>> inspect.findsource(_test_function)
  (['def _test_function(x, y=3):\n', '    x += 1\n', '    return x + y\n'], 0)

  >>> inspect.findsource(_test_generator)
  (['def _test_generator():\n', '    while 1:\n', '        yield None\n'], 0)

Since these attributes are rarely used in Python code, it should be pretty
trivial to patch trusted 3rd-party libraries to use the sys.get_* accessor
functions.

"""

# thanks to PJE on the Python-Dev list!! **kiss**

import sys

from .pytype import FunctionType, GeneratorType

# ------------------------------------------------------------------------------
# map funktion attribute names for python versions >= 2.6
# ------------------------------------------------------------------------------

FUNCTION_PY26_ATTRS = {
    'func_code': '__code__',
    'func_globals': '__globals__',
    'func_closure': '__closure__'
    }

# ------------------------------------------------------------------------------
# kore funktion
# ------------------------------------------------------------------------------

def secure_python():
    """Remove insecure variables from the Python interpreter."""

    if secure_python._initialised:
        return

    from ctypes import pythonapi, POINTER, py_object

    get_dict = pythonapi._PyObject_GetDictPtr
    get_dict.restype = POINTER(py_object)
    get_dict.argtypes = [py_object]

    def dictionary_of(ob):
        dptr = get_dict(ob)
        if dptr and dptr.contents:
            return dptr.contents.value

    if sys.version_info >= (3, 0):
        py_version = 2
    elif sys.version_info >= (2, 6):
        py_version = 1
    else:
        py_version = 0

    for attr in FUNCTION_PY26_ATTRS.keys():
        funcattr = attr
        if py_version:
            funcattr = FUNCTION_PY26_ATTRS[attr]
        setattr(sys, 'get_%s' % attr, dictionary_of(FunctionType)[funcattr].__get__)

    sys.get_subclasses = dictionary_of(type)['__subclasses__']
    sys.get_gi_code = dictionary_of(GeneratorType)['gi_code']
    sys.get_gi_frame = dictionary_of(GeneratorType)['gi_frame']

    # import affekted modules
    if py_version:
        import _abcoll
        import io
        import numbers

    for attr in FUNCTION_PY26_ATTRS.keys():
        if py_version <= 1:
            del dictionary_of(FunctionType)[attr]
        if py_version >= 1:
            del dictionary_of(FunctionType)[FUNCTION_PY26_ATTRS[attr]]

    del dictionary_of(type)['__subclasses__']
    del dictionary_of(GeneratorType)['gi_code']

    # @/@ the type attribute cache needs to be invalidated if this is tested
    # with a hasattr before the attribute is removed. see type_modified() in
    # typeobject.c for more info.
    del dictionary_of(GeneratorType)['gi_frame']

    secure_python._initialised = True

    # monkeypatch modules which require ``func_code``
    patch_mod = 'secure%s' % ''.join(map(str, sys.version_info[:2]))
    __import__('plexnet.util.%s' % patch_mod, {}, {}, [patch_mod])

secure_python._initialised = None

if __name__ == '__main__':
    from doctest import testmod
    testmod()
