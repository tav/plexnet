#!/usr/bin/env python
"""
data.py - Object Datatype
Author: Sean B. Palmer, inamidst.com

This module defines an Object class whose attributes can be set to
dynamic values which get calculated when accessed or assigned. You
can assign static attributes just by setting them:

   >>> task1 = Object()
   >>> task1.name = 'task1'
   >>> task1.start = 1
   >>> task1.length = 2

To add a dynamic attribute, you have to create getter and setter
functions, which will be called when the attribute is accessed or
assigned respectively, and then wrap them up in a Dynamic object to
be assigned to an object attribute:

   >>> end = Dynamic()
   >>> end.getter = Sum(local.start, local.length)
   >>> end.setter = { local.start: Difference(local.end, local.length) }
   >>> task1.end = end
   >>> task1
   Object{name: 'task1', start: 1, length: 2, end: 3}

Here we've made it so that the end attribute computes the value of
start and length added together. When we change start, end is
automatically updated:

   >>> task1.start = 2
   >>> task1
   Object{name: 'task1', start: 2, length: 2, end: 4}

You can also derive a new object from an old object, making a kind of
copy of the object. This will automatically copy over any old values,
but if you want to refer to a value on the old object you can use an
Attribute to do so:

   >>> task2 = task1()
   >>> task2.name = 'task2'
   >>> task2.start = Attribute(task1, 'end')
   >>> task2
   Object{name: 'task2', start: 4, length: 2, end: 6}

So that, putting this all together, the fields are interdependent in
interesting ways:

   >>> task2.end = 5
   >>> task2
   Object{name: 'task2', start: 3, length: 2, end: 5}
   >>> task1
   Object{name: 'task1', start: 1, length: 2, end: 3}
   >>> task2.length = 3
   >>> task2.end
   6

Although seemingly non-sensical, the fact that you set a value does
not require it to be the value actually set

   >>> task3 = Object()
   >>> task3.name = 'task3'
   >>> task3.task1 = Attribute(task1, 'end')
   >>> task3.task2 = Attribute(task2, 'end')
   >>> total = Dynamic()
   >>> total.getter = Sum(local.task1, local.task2)
   >>> total.setter = { local.task1: Difference(local.total, local.task2) }
   >>> task3.total = total
   >>> task3
   Object{name: 'task3', task1: 3, task2: 6, total: 9}
   >>> task3.total = 10
   >>> task3
   Object{name: 'task3', task1: 4, task2: 7, total: 11}

We also will error if we have a dependency chain which loops back onto itself.

   >>> cycle = Object()
   >>> cycle.name = 'cycle'
   >>> first = Dynamic()
   >>> first.getter = Sum(local.zero, local.second)
   >>> first.setter = { local.second: Difference(local.first, local.zero) }
   >>> cycle.first = first
   >>> second = Dynamic()
   >>> second.getter = Sum(local.zero, local.first)
   >>> second.setter = { local.first: Difference(local.second, local.zero) }
   >>> cycle.second = second
   >>> cycle.zero = 0
   >>> cycle.first
   Traceback (most recent call last):
       ...
   CycleError: Cycle detected: cycle.first

   >>> cycle.first = 1
   Traceback (most recent call last):
       ...
   CycleError: Cycle detected: cycle.first

   >>> cycle2 = Object()
   >>> cycle2.name = 'cycle2'
   >>> cycle2.loop = Attribute(cycle2, 'loop')
   >>> cycle2.loop
   Traceback (most recent call last):
       ...
   CycleError: Cycle detected: cycle2.loop

   >>> cycle2.loop = 1
   Traceback (most recent call last):
       ...
   CycleError: Cycle detected: cycle2.loop

"""

import fieldtree

class Object(object): 
   def __init__(self, fields=None): 
      self.__fields = fieldtree.FieldTree()

   def __repr__(self): 
      items = ((attr, getattr(self, attr)) for attr in self.__fields.labels())
      return 'Object{%s}' % ', '.join('%s: %r' % item for item in items)

   def __getattr__(self, attr): 
      if attr.startswith('_'): 
         return object.__getattr__(self, attr)

      value, special = self.__fields.get(attr)
      if special is not None: 
         value = special.get_value(self, attr)
         self.__fields[attr] = (value, special)
      return value

   def __setattr__(self, attr, value): 
      if attr.startswith('_'): 
         return object.__setattr__(self, attr, value)

      current = self.__fields.get(attr, (None, None))[1]
      if isinstance(value, Special): 
         self.__fields[attr] = (None, value)
      elif isinstance(current, Special): 
         self.__fields[attr] = (value, None)
         current.set_value(self, attr, value)
         self.__fields[attr] = (value, current)
      else: self.__fields[attr] = (value, None)

   def __getitem__(self, item): 
      return self.__fields[item]

   def __setitem__(self, item, value): 
      self.__fields[item] = value

   def __call__(self): 
      import copy
      obj = Object()
      for label, value in self.__fields.fields(): 
         obj[label] = value
      return obj

class Special(object): 
   getted = set()
   originals = {}
   unknown = None

   def get_value(self, obj, attr): 
      myhash = str(hash(obj)) + '.' + str(hash(attr))

      first = True if Special.unknown == None else False
      if first:
         Special.unknown = set()

      if myhash in Special.unknown:
         #if first: do unrolling, somehow
         raise CycleError("Cycle detected: %s.%s" % (obj.name, attr))

      Special.unknown.add(myhash)

      value = self._get_value(obj, attr) # do specific operations

      Special.unknown.discard(myhash)
      Special.getted.add(myhash)

      if first:
         getted = set()
         originals = {}
         unknown = None

      return value

   def set_value(self, obj, attr, value): 
      myhash = str(hash(obj)) + '.' + str(hash(attr))

      was = None if myhash not in Special.getted else getattr(obj, attr)
      first = True if Special.unknown == None else False
      if first:
         was = None # we don't have a value if we are starting
         Special.unknown = set()

      if myhash in Special.unknown:
         #if first: do unrolling, somehow
         raise CycleError("Cycle detected: %s.%s" % (obj.name, attr))

      self._set_value(obj, attr, value)
      value = getattr(obj, attr) # do specific operations

      if was != None and was != value:
         #if first: do unrolling, somehow
         raise CycleError("Cycle detected: %s.%s. was: %s, now: %s" %
                 (obj.name, attr, was, value))

      if first:
         getted = set()
         originals = {}
         unknown = None

class Dynamic(Special): 
   def __init__(self): 
      self.getter = None
      self.setter = None

   def _get_value(self, obj, attr): 
      self.getter.objects.append(obj)
      value = self.getter()
      self.getter.objects.pop()

      return value

   def _set_value(self, obj, attr, value): 
      for output, calculate in self.setter.iteritems(): 
         calculate.objects.append(obj)
         setattr(obj, output, calculate())
         calculate.objects.pop()

class Attribute(Special): 
   def __init__(self, obj, attr): 
      self.obj = obj
      self.attr = attr

   def _get_value(self, obj, attr): 
      return getattr(self.obj, self.attr)

   def _set_value(self, obj, attr, value): 
      setattr(self.obj, self.attr, value)

class Local(str): 
   pass

class LocalNamespace(object): 
   def __getattr__(self, attr): 
      return Local(attr)
local = LocalNamespace()

def Computation(original): 
   def define(*args): 
      def compute(): 
         def evaluate(arg): 
            if isinstance(arg, Local): 
               return getattr(compute.objects[-1], arg)
            else: return arg
         return compute.original(*[evaluate(arg) for arg in compute.args])
      compute.original = define.original
      compute.args = args
      compute.objects = []
      return compute
   define.original = original
   return define

@Computation
def Sum(a, b): 
   return a + b
 
@Computation
def Difference(a, b): 
   return a - b

class CycleError(Exception):
   "Circular call structure was detected."

def test(): 
   import doctest
   Documentation = type('Documentation', (object,), {'__doc__': __doc__})
   doctest.run_docstring_examples(Documentation, globals(), verbose=True)

def summary(): 
   import sys, StringIO

   stdout = sys.stdout
   sys.stdout = StringIO.StringIO()
   test()
   buffer = sys.stdout
   sys.stdout = stdout
   buffer.seek(0)

   success, failure = 0, 0
   for line in buffer: 
      success += int(line.startswith('ok'))
      failure += int(line.startswith('Fail'))
   print "%s/%s Tests Passed" % (success, success + failure)

def main(): 
   summary()

if __name__ == '__main__': 
   main()
