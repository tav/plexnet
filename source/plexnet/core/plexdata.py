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
         for label, value in fields.itervalues(): 
            if not self.index.has_key(label): 
               self.index[label] = {}
            self.index[label].setdefault(value, set()).add(name)

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
   def __init__(self, packet): 
      self.packet = packet
      self.patterns = set()

   def pattern(self, function): 
      self.patterns.add(function)

   def matches(self, changeset): 
      if not self.patterns: 
         return False
      for pattern in self.patterns: 
         matches = False 
         for name, fields in changeset.iteritems(): 
            if not pattern(fields): 
               matches = True
         if not matches:
            return False
      return True

   def notify(self, changeset):
      matches = {}
      for pattern in self.patterns:
         for name, fields in changeset.iteritems():
            if pattern(fields):
               matches.setdefault(name, 0)
               matches[name] += 1

      full = [match for match, count in matches.iteritems() if
                  count == len(self.patterns)]

      identifier = 'Sensor(%s)' % id(self)
      obj, this = self.packet.object(identifier)
      obj.update({'notified': True})
      obj.update({'matches': full})

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
   packet = Packet()
   example1, this = packet.object('example1')
   example1.update({
      'message': 'This is an example'
   })
   example2, this = packet.object('example2')
   example2.update({
      'message': 'This is completely unrelated'
   })
   example3, this = packet.object('example3')
   example3.update({
      'message': 'This is another example',
      'addendum': 'It has more information'
   })

   sensor = Sensor(packet)
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
   sensor.pattern(example_message)
   packet.sensors.add(sensor)

   sensor = Sensor(packet)
   sensor.pattern(example_message)
   sensor.pattern(check_id)
   packet.sensors.add(sensor)

   packet.commit()

   print packet.objects.keys()
   for name in packet.objects.keys():
       if 'Sensor' in name:
           print packet.objects[name]

def main(): 
   account_test()
   cycle_test()
   sensor_test()

if __name__ == '__main__': 
   main()
