#!/usr/bin/env python
"""
plexdata.py - Plexdata Implementation
Author: Sean B. Palmer, inamidst.com
"""

import fieldtree

def computation(obj): 
   "Test whether an object is a computation."
   return callable(obj) and hasattr(obj, 'original')

class Unit(fieldtree.FieldTree): 
   "A hashtable that calls services automatically."
   units = {}

   def __init__(self, fields): 
      if isinstance(fields, dict): 
         fields = fields.items()    
      self.__changes = {}
      self.__depth = 0
      self.__error = None
      super(Unit, self).__init__(*fields)
      identifier = self['__id__']
      Unit.units[identifier] = self

   def __getitem__(self, key): 
      value = super(Unit, self).__getitem__(key)

      if computation(value): 
         self.__depth += 1
         try: value = value()
         except Exception, e: 
            if self.__error is None: 
               self.__error = Error(e)
         self.__depth -= 1

      if (self.__depth == 0) and (self.__error is not None): 
         value = self.__error
         self.__error = None
      return value

   def changed(self, *labels): 
      for label in labels: 
         field = self.get_field(label)
         self.__changes[label] = field

   def has_changes(self): 
      return len(self.__changes) > 0

   def get_changes(self): 
      changes = self.__changes.copy()
      self.__changes = {}
      return changes

class Error(object): 
   def __init__(self, e): 
      self.exception = e

   def __repr__(self): 
      args = (type(self.exception).__name__, str(self.exception))
      return '%s(%r)' % args

class CycleError(Exception): 
   "Circular call structure was detected."

def Service(original): 
   "Create a service definer from original."
   def compute(): 
      "Compute a service, autocalled by Unit etc."
      def value(n): 
         if n.name in Service.accessed: 
            raise CycleError("Cycle detected: %s" % n.name)
         Service.accessed.add(n.name)
         return Unit.units[n.unit][n.key]

      def evaluate(arg): 
         if isinstance(arg, ValueName): 
            return value(arg)
         elif computation(arg): 
            return arg()
         else: return arg

      accessed = Service.accessed.copy()
      args = [evaluate(arg) for arg in compute.args]
      result = compute.original(*args)
      Service.accessed = accessed
      return result
   compute.original = original

   def define(*args): 
      "Create a function to compute the service."
      compute.args = args
      return compute
   return define
Service.accessed = set()

@Service
def Sum(a, b): 
   return a + b

@Service
def Interest(a, b): 
   return a + (a * b)

class UnitName(str): 
   def __call__(self, key): 
      return ValueName(self, key)

class ValueName(object): 
   def __init__(self, unit, key): 
      self.unit = unit
      self.key = key
      self.name = unit + '.' + key

def account_test(): 
   this = UnitName('account')
   total = Sum(this('savings'), this('creditcard'))
   account = Unit({
      '__id__': this, 
      'savings': 5000,
      'creditcard': -3000, 
      'total': total, 
      'interest': 0.01, 
      'adjusted': Interest(this('total'), this('interest')), 
      'adj': Interest(total, this('interest')), 
   })
   
   changes = account.get_changes()
   total = account['total'] # expect: 2000
   adjusted = account['adjusted'] # expect: 2020
   account['savings'] += 1000
   total_ = account['total'] # expect: 3000
   adj_ = account['adj'] # expect: 3030
   
   print total, adjusted, total_, adj_
   print account.has_changes()
   print account.get_changes()

def cycle_test(): 
   this = UnitName('cycle')
   cycle = Unit({
      '__id__': this, 
      'first': Sum(this('zero'), this('second')), 
      'second': Sum(this('zero'), this('first')), 
      'zero': 0
   })
   
   print cycle['first']

def main(): 
   account_test()
   cycle_test()

if __name__ == '__main__': 
   main()
