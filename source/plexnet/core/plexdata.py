#!/usr/bin/env python
"""
plexdata.py - Plexdata Implementation
Author: Sean B. Palmer, inamidst.com
"""

import fieldtree

class Packet(object): 
   "Generic object container."
   def __init__(self): 
      self.objects = {}
      self.index = {}
      self.sensors = set()
      Service.packet = self

   def __str__(self): 
      objects = self.objects.iteritems()
      return 'Packet{ %s }' % ', '.join('%s := %s' % (a, b) for a, b in objects)

   def object(self, name): 
      this = ObjectName(name)
      obj = Object({'__id__': this})
      self.add(obj)
      return obj, this

   def add(self, obj): 
      assert isinstance(obj, Object)
      identifier = obj['__id__']
      self.objects[identifier] = obj

   def get(self, n): 
      return self.objects[n.object][n.label]

   def commit(self): 
      changeset = {}
      for name, object in self.objects.iteritems(): 
         if object.has_changes(): 
            changeset[name] = object.get_changes()

      for name, fields in changeset.iteritems(): 
         for key, (label, value) in fields.iteritems(): 
            if isinstance(value, set): 
               value = frozenset(value)

            if not self.index.has_key(key): 
               self.index[key] = {}
            self.index[key].setdefault(value, set()).add(name)

      for sensor in self.sensors: 
         if sensor.matches(changeset): 
            sensor.notify(changeset)

class Object(fieldtree.FieldTree): 
   "Generic object with Service calling code."
   def __init__(self, fields): 
      self.__changes = {}
      self.__depth = 0
      self.__error = None

      if isinstance(fields, dict): 
         fields = fields.items()    
      super(Object, self).__init__(*fields)

   def __str__(self): 
      return 'Object{ %s }' % ', '.join('%s: %r' % (a, b) for a, b in self.fields())

   def __getitem__(self, label): 
      value = super(Object, self).__getitem__(label)

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

   def update(self, fields): 
      if isinstance(fields, dict): 
         fields = fields.items()    
      super(Object, self).update(fields)

   def changed(self, *keys): 
      for key in keys: 
         field = self.get_field(key)
         self.__changes[key] = field

   def has_changes(self): 
      return len(self.__changes) > 0

   def get_changes(self): 
      changes = self.__changes.copy()
      self.__changes = {}
      return changes

def Service(original): 
   "Create a service definer from original."
   def compute(): 
      "Compute a service, autocalled by Object etc."
      def value(n): 
         if n.name in Service.accessed: 
            raise CycleError("Cycle detected: %s" % n.name)
         Service.accessed.add(n.name)
         return Service.packet.get(n)

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
Service.packet = None
Service.accessed = set()

@Service
def Sum(a, b): 
   return a + b

@Service
def Interest(a, b): 
   return a + (a * b)

class Sensor(object): 
   def __init__(self, obj): 
      self.output = obj
      self.optional_patterns = set()
      self.mandatory_patterns = set()
      self.matched = set()

   def optional(self, function): 
      self.optional_patterns.add(function)

   def mandatory(self, function): 
      self.mandatory_patterns.add(function)

   def matches(self, changeset): 
      optional = set()
      mandatory = set()
      self.matched = set()

      for opt in self.optional_patterns: 
         o = [opt(fields) for name, fields in changeset.iteritems()]
         optional.add(o.count(True))
         if o.count(True): 
            self.matched.add(opt.__name__)

      for man in self.mandatory_patterns: 
         m = [man(fields) for name, fields in changeset.iteritems()]
         mandatory.add(m.count(True))
         if m.count(True): 
            self.matched.add(man.__name__)

      return any(optional or [True]) and all(mandatory or [True])

   def notify(self, changeset): 
      identifier = 'Sensor(%s)' % id(self)
      self.output.update({'notified': True})
      self.output.update({'matches': self.matched})

class Schema(object): 
   def __init__(self, **kargs): 
      self.properties = kargs

   def __call__(self, obj): 
      import new
      for key, value in self.properties.iteritems(): 
         function = lambda self=self, value=value: self[value]
         method = new.instancemethod(function, obj, type(obj))
         setattr(obj, key, method)
      return obj

class ObjectName(str): 
   def __call__(self, label): 
      return ValueName(self, label)

class ValueName(object): 
   def __init__(self, object, label): 
      self.object = object
      self.label = label
      self.name = object + '.' + label

class Error(object): 
   def __init__(self, e): 
      self.exception = e

   def __repr__(self): 
      args = (type(self.exception).__name__, str(self.exception))
      return '%s(%r)' % args

class CycleError(Exception): 
   "Circular call structure was detected."

def computation(obj): 
   "Test whether an object is a computation."
   return callable(obj) and hasattr(obj, 'original')

def account_test(): 
   packet = Packet()
   account, this = packet.object('account')
   total = Sum(this('savings'), this('creditcard'))
   account.update({
      'savings': 5000,
      'creditcard': -3000, 
      'total': total, 
      'interest': 0.01, 
      'adjusted': Interest(this('total'), this('interest')), 
      'adj': Interest(total, this('interest')), 
   })
   
   total = account['total'] # expect: 2000
   adjusted = account['adjusted'] # expect: 2020
   account['savings'] += 1000
   total_ = account['total'] # expect: 3000
   adj_ = account['adj'] # expect: 3030
   
   print total, adjusted, total_, adj_

   packet.commit()
   print packet.index

def cycle_test(): 
   packet = Packet()
   cycle, this = packet.object('cycle')
   cycle.update({
      'first': Sum(this('zero'), this('second')), 
      'second': Sum(this('zero'), this('first')), 
      'zero': 0
   })
   
   print cycle['first']

def sensor_test(): 
   first = Packet()
   example1, this = first.object('example1')
   example1.update({
      'message': 'This is an example'
   })
   output2, this = first.object('output2')
   output2.update({
      'message': 'This is the second output object'
   })

   second = Packet()
   example2, this = second.object('example2')
   example2.update({
      'message': 'This is another example',
      'addendum': 'It has more information'
   })
   output1, this = second.object('output1')
   output1.update({
      'message': 'This is the first output object'
   })

   def example_message(unit):
      for label, value in unit.itervalues():
         if (label == 'message') and ('example' in value):
            return True
      return False

   def check_id(unit):
      for label, value in unit.itervalues():
         if (label == 'addendum'):
            return True
      return False

   # sensor1 in first, to match example1, output to output1 in second
   sensor1 = Sensor(output1)
   sensor1.mandatory(example_message)
   first.sensors.add(sensor1)
   first.commit()

   # sensor2 in second, to match example2, output to output1 in first
   sensor2 = Sensor(output2)
   sensor2.mandatory(example_message)
   sensor2.mandatory(check_id)
   second.sensors.add(sensor2)
   second.commit()

   print first.objects.keys()
   for name in first.objects.keys():
       if 'Sensor' in name:
           print first.objects[name]

   print second.objects.keys()
   for name in second.objects.keys():
       if 'Sensor' in name:
           print second.objects[name]

   print first

def schema_test(): 
   packet = Packet()
   account, this = packet.object('account')
   account.update({
      'savings': 5000,
      'creditcard': -3000, 
      'total': Sum(this('savings'), this('creditcard'))
   })

   Account = Schema(total=account.get_key('total'))
   account = Account(account)
   print account.total()

def main(): 
   account_test()
   cycle_test()
   sensor_test()
   schema_test()

if __name__ == '__main__': 
   main()
