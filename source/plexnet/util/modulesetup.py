"""
==================================================
Support Infrastructure for Handling Python Modules
==================================================

Python modules are a very useful feature. But sometimes, they can be a real pain
to handle. This module makes them a breeze.

Like with most objects, lookups in a module raise an ``AttributeError`` if an
attribute has never been set before, e.g.

  >>> module = ModuleType('normal_module')

  >>> print module.foo
  Traceback (most recent call last):
  ...
  AttributeError: 'module' object has no attribute 'foo'

A ``DefaultModuleType`` type is provided that always returns a value of ``None``
instead of raising an AttributeError for any attributes which have not been set:

  >>> module2 = DefaultModuleType('default_module')

  >>> print module2.foo
  None

A helper constructor called ``setup_dummy_module`` is provided which creates and
sets such a module within ``sys.modules``:

  >>> nutella = setup_dummy_module('nutella', docstring='Chocolate Goodness!')

  >>> print nutella.is_available
  None

  # Ring the alarm!!

  >>> nutella.is_available = True

  >>> print nutella.is_available
  True

  # Phew!!

The module can then be imported from other modules as if it were a real module.
Let's delete the variable from the local namespace to see if this works:

  >>> del nutella

  >>> nutella
  Traceback (most recent call last):
  ...
  NameError: name 'nutella' is not defined

  >>> import nutella

As we can see, it imported successfully, and even has the state that we had set
before:

  >>> print nutella.is_available
  True

By default, a similar module called ``settings`` is setup as a place to store
shared global values without polluting other namespaces.

    >>> import settings

    >>> settings.non_existant_variable

    >>> print settings.new_variable
    None

    >>> settings.new_variable = 'hello'

    >>> settings.new_variable
    'hello'

    >>> del settings.new_variable

    >>> print settings.new_variable
    None

Unfortunately, reloading modules like this is currently broken:

    >>> reload(settings)
    Traceback (most recent call last):
    ...
    ImportError: No module named settings

"""

import sys

ModuleType = type(sys)

class DefaultModuleType(ModuleType):
    __doc__ = ModuleType.__doc__

    def __getattribute__(self, attribute):
        try:
            return ModuleType.__getattribute__(self, attribute)
        except:
            return None

def setup_dummy_module(name, docstring=None):
    return sys.modules.setdefault(name, DefaultModuleType(name, docstring))
