#!/usr/bin/env python
'services.py - Services'

import fieldtree

author = ('Sean B. Palmer', 'inamidst.com')

class Object(object): 
   def __init__(self, fields=None): 
      if fields is not None: 
         fields = fieldtree.FieldTree(*fields)
      else: fields = fieldtree.FieldTree()
      self.__fields = fields

   def __repr__(self): 
      items = ((attr, getattr(self, attr)) for attr in self.__fields.labels())
      return 'Object{%s}' % ', '.join('%s: %r' % item for item in items)

   def __getitem__(self, item): 
      return self.__fields[item]

   def __getattr__(self, attr): 
      if attr.startswith('_'): 
         return object.__getattr__(self, attr)

      value, special = self.__fields.get(attr)
      if special is not None: 
         value = special.derive(self, attr)
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
         current.react(self, attr, value)
         self.__fields[attr] = (value, current)
      else: self.__fields[attr] = (value, None)

   def __call__(self): 
      import copy
      fields = []
      for label, value in self.__fields.fields(): 
         fields.append((label, copy.deepcopy(value)))
      return Object(fields)

class Special(object): 
   pass

class Formula(Special): 
   def __init__(self, derivation, reactions): 
      self.derivation = derivation
      self.reactions = reactions

   def derive(self, obj, attr): 
      self.derivation.obj = obj
      return self.derivation()

   def react(self, obj, attr, value): 
      for output, reaction in self.reactions.iteritems(): 
         reaction.obj = obj
         result = reaction()
         setattr(obj, output, result)

class Reference(Special): 
   def __init__(self, obj, attr): 
      self.obj = obj
      self.attr = attr

   def derive(self, obj, attr): 
      return getattr(self.obj, self.attr)

   def react(self, obj, attr, value): 
      setattr(self.obj, str(self.attr), value)

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
               return getattr(compute.obj, arg)
            else: return arg
         return compute.original(*[evaluate(arg) for arg in compute.args])
      compute.original = define.original
      compute.args = args
      return compute
   define.original = original
   return define

@Computation
def Sum(a, b): 
   return a + b
 
@Computation
def Difference(a, b): 
   return a - b
 
def main(): 
   task1 = Object()
   task1.name = 'task1'
   task1.start = 1
   task1.length = 2
   get_end = Sum(local.start, local.length)
   set_end = { local.start: Difference(local.end, local.length) }
   task1.end = Formula(get_end, set_end)
   print 6, task1
   task1.start = 2
   print 9, task1

   task2 = task1()
   task2.name = 'task2'
   task2.start = Reference(task1, 'end')
   print 11, task2

   task2.end = 5
   print 13, task2
   print 16, task1

if __name__ == '__main__': 
   main()
