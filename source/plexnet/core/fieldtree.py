#!/usr/bin/env python
"""
fieldtree.py - Field Tree Object
Author: Sean B. Palmer, inamidst.com

The FieldTree object is a kind of OrderedDict. The name Field refers
to a label and value pair, usually called an item in Python.

There are two main extra features that a FieldTree provides over an
OrderedDict. The first is that when a field is set, it returns a Key
object. This provides a kind of permanent link to the field. The
second is that there are methods that allow for the access of any
FieldTree objects nested inside a FieldTree.

New FieldTree objects can be constructed without arguments:

   >>> person = FieldTree()

You can add fields and keep the resulting keys:

   >>> a = person.add('gender', 'male')
   >>> b = person.add('name', 'John Smith')
   >>> c = person.add('website', 'example.com')

Or you can add fields and discard the keys:

   >>> person['phone'] = '123-456-7890'
   >>> person['email'] = 'john@example.com'

You can then access fields by key or by label:

   >>> person[b]
   'John Smith'
   >>> person['website']
   'example.com'

The useful thing about keys is that you can use them to access fields
that you might then want to modify, and they'll be available after
those modifications. So if we make a template from a FieldTree:

   >>> def format(person): 
   ...    args = person[b], person[a], person[c]
   ...    return 'Name: %s, Sex: %s, Website: %s' % args

This works in the expected way:

   >>> format(person)
   'Name: John Smith, Sex: male, Website: example.com'

But then even if you start adding and modifying values:

   >>> f = person.before(c, 'company', 'Acme Ltd.')
   >>> person.changelabel(a, 'sex')

So that the data has a different label and a new order:

   >>> for field in person.fields(): 
   ...    print field
   ... 
   ('sex', 'male')
   ('name', 'John Smith')
   ('company', 'Acme Ltd.')
   ('website', 'example.com')
   ('phone', '123-456-7890')
   ('email', 'john@example.com')

The template still works!

   >>> format(person)
   'Name: John Smith, Sex: male, Website: example.com'

Now, let's say we want to use a FieldTree structure for the name so
that we can store the forename and surname separately. We'll make
this FieldTree by passing some field arguments:

   >>> name = FieldTree(('forename', 'John'), ('surname', 'Smith'))

And then we can query the new object for its keys:

   >>> g = name.get_key('forename')
   >>> h = name.get_key('surname')

We can then change the existing value of the 'name' label:

   >>> person['name'] = name

And because this is a field tree, we can use the keys we got from the
nested FieldTree to access its values from the parent tree:

   >>> person[g]
   'John'
   >>> person['name'][h]
   'Smith'

But of course, we can't use labels to access nested values:

   >>> person['forename']
   Traceback (most recent call last):
      ...
   KeyError: "no 'forename' label"

Using labels in the regular way does work, though:

   >>> person['name']['forename']
   'John'

Printing out all the fields iterates also over the nested fields, but
it skips any FieldTree values themselves:

   >>> for field in person: 
   ...    print field
   ... 
   ('sex', 'male')
   ('forename', 'John')
   ('surname', 'Smith')
   ('company', 'Acme Ltd.')
   ('website', 'example.com')
   ('phone', '123-456-7890')
   ('email', 'john@example.com')

With FieldTree objects there is a general principle that you can use
labels only on the current FieldTree object, but you can use keys in
a nested way. So for example, you can check whether a FieldTree or
any of its nested FieldTree objects contains a key:

   >>> a in person # gender/sex
   True
   >>> g in person # forename
   True

But you can only check for labels in a non-nested way:

   >>> 'sex' in person
   True
   >>> 'name' in person
   True
   >>> 'forename' in person
   False

You can iterate over all kinds of combinations of fields, labels,
keys, and values using the iteration methods:

   >>> import itertools
   >>> def show(iter, num): 
   ...    return list(itertools.islice(iter, num))

To, for example, note that keys are a subclass of int:

   >>> show(person.keys(), 3)
   [Key(1), Key(2), Key(6)]

And that labels (but not keys) referring to FieldTree object values
are skipped, so that the following doesn't have 'name':

   >>> show(person.tree_labels(), 3)
   ['sex', 'forename', 'surname']

Another feature of FieldTree objects is that you can set values that
don't have any labels. This means that you can only refer to this
value using its key:

   >>> i = person.add('John Smith plays the trumpet')
   >>> person[i]
   'John Smith plays the trumpet'
   >>> person.get_field(i)
   (Empty(), 'John Smith plays the trumpet')

You can also delete values using a similar method. You shouldn't
remove a whole field entirely, so delete replaces the current value
with an Empty() object:

   >>> del person['phone']
   >>> person['phone']
   Empty()

Though you can remove a field entirely, it's not really recommended:

   >>> example = FieldTree(('a', 'b'), ('p', 'q'))
   >>> first = example.get_key('a')
   >>> example.remove(first)
   >>> len(example)
   1
   >>> example['a']
   Traceback (most recent call last):
      ...
   KeyError: "no 'a' label"

There are some other convenience functions for looking up various
kinds of fields, keys, labels, and values:

   >>> person.get_field(g)
   ('forename', 'John')
   >>> person.get_label(g)
   'forename'
   >>> person.get_value(g)
   'John'

"""

import itertools

class Key(int): 
   __counter = itertools.count(1)

   def __repr__(self): 
      return 'Key(%s)' % int(self)

   @staticmethod
   def next(): 
      num = Key.__counter.next()
      return Key(num)

class Empty(object): 
   def __repr__(self): 
      return 'Empty()'

class FieldTree(object): 
   def __init__(self, *args): 
      self.__fields = {} # {key: (label, value)}
      self.__values = {} # {label: (key, value)}
      self.__order = [] # [keys]
      self.__trees = set() # [field-tree-values]

      for label, value in args: 
         self[label] = value

   def __repr__(self): 
      return 'FieldTree%s' % (tuple(self.fields()),)

   def __len__(self): 
      return len(self.__order)

   def __contains__(self, obj): 
      if isinstance(obj, Key): 
         return self.has_tree_key(obj)
      else: return self.has_label(obj)

   def has_key(self, key): 
      return self.__fields.has_key(key)

   def has_tree_key(self, key): 
      for tree in [self] + list(self.__trees): 
         if tree.has_key(key): 
            return True
      return False

   def has_label(self, label): 
      return self.__values.has_key(label)

   def __iter__(self): 
      return self.tree_fields()

   def fields(self): 
      for key in self.__order: 
         yield self.__fields[key]

   def tree_fields(self): 
      for key in self.__order: 
         label, value = self.__fields[key]

         if isinstance(value, FieldTree): 
            for field in value.tree_fields(): 
               yield field
         else: yield label, value

   def keys(self): 
      for key in self.__order: 
         yield key

   def tree_keys(self): 
      for key in self.__order: 
         label, value = self.__fields[key]

         if isinstance(value, FieldTree): 
            for vkey in value.tree_keys(): 
               yield vkey
            else: yield key

   def labels(self): 
      for label, value in self.fields(): 
         yield label

   def tree_labels(self): 
      for label, value in self.tree_fields(): 
         yield label

   def values(self): 
      for label, value in self.fields(): 
         yield value

   def tree_values(self): 
      for label, value in self.tree_fields(): 
         yield value

   def __getitem__(self, item): 
      return self.get_value(item)

   def get_field(self, key): 
      "key -> field (deep)"
      assert isinstance(key, Key)
      if self.has_key(key): 
         return self.__fields[key]
      for tree in self.__trees: 
         try: return tree.get_field(key)
         except KeyError: continue
      raise KeyError("no %r key" % key)

   def get_key(self, label): 
      "label -> key (shallow)"
      if self.has_label(label): 
         return self.__values[label][0]
      else: raise KeyError("no %r label" % label)

   def get_label(self, key): 
      "key -> label (deep)"
      return self.get_field(key)[0]

   def get_value(self, obj): 
      "key -> value (deep) or label -> value (shallow)"
      if isinstance(obj, Key): 
         return self.get_key_value(obj)
      else: return self.get_label_value(obj)

   def get_key_value(self, key): 
      "key -> value (deep)"
      return self.get_field(key)[1]

   def get_label_value(self, label): 
      "label -> value (shallow)"
      if self.has_label(label): 
         return self.__values[label][1]
      else: raise KeyError("no %r label" % label)

   def __setitem__(self, obj, value): 
      if not (obj in self): 
         self.add(obj, value)
      else: self.changevalue(obj, value)

   def __arguments(self, args): 
      if len(args) == 1: 
         args = Empty(), args[0]
      elif len(args) != 2: 
         raise ValueError("Expected one or two args")

      if any(isinstance(arg, Key) for arg in args): 
         raise ValueError("FieldTrees can't contain Keys")
      return args

   def __set(self, args): 
      label, value = self.__arguments(args)

      if self.has_label(label): 
         key, oldvalue = self.__values[label]
         if isinstance(oldvalue, FieldTree): 
            self.__trees.remove(oldvalue)
      else: key = Key.next()

      self.__fields[key] = (label, value)
      if not isinstance(label, Empty): 
         self.__values[label] = (key, value)
      self.changed(key)
      return key

   def add(self, *args): 
      key = self.__set(args)
      self.__order.append(key)
      return key

   def update(self, args, ignore = None): 
      for label, value in args: 
         if not ignore or label not in ignore:
            self[label] = value

   def before(self, next, *args): 
      if not self.has_key(next): 
         raise KeyError("no %r key" % next)
      key = self.__set(args)

      index = self.__order.index(next)
      self.__order.insert(index, key)
      return key

   def __delitem__(self, obj): 
      self.delete(obj)

   def delete(self, obj): 
      self.changevalue(obj, Empty())

   def remove(self, key): 
      assert isinstance(key, Key)
      label, value = self.get_field(key)
      del self.__fields[key]
      del self.__values[label]
      self.__order.remove(key)
      if isinstance(value, FieldTree): 
         self.__trees.remove(value)
      self.changed(key)

   def changelabel(self, key, label): 
      if not self.has_key(key): 
         raise KeyError("no %r key" % key)
      oldlabel, value = self.__fields[key]

      self.__fields[key] = (label, value)
      self.__values[label] = (key, value)
      self.changed(key)

   def changevalue(self, obj, value): 
      if isinstance(obj, Key) and self.has_key(obj): 
         key, (label, oldvalue) = obj, self.__fields[obj]
      elif self.has_label(obj): 
         label, (key, oldvalue) = obj, self.__values[obj]
      else: raise KeyError("%r" % obj)

      self.__fields[key] = (label, value)
      self.__values[label] = (key, value)

      if isinstance(oldvalue, FieldTree): 
         self.__trees.remove(oldvalue)
      if isinstance(value, FieldTree): 
         self.__trees.add(value)
      self.changed(key)

   def changefield(self, key, label, value): 
      self.changelabel(key, label)
      self.changevalue(key, value)
      self.changed(key)

   def changed(self, *keys): 
      pass

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
      if line.startswith('ok'): 
         success += 1
      elif line.startswith('Fail'): 
         failure += 1
   print "%s/%s Tests Passed" % (success, success + failure)

def main(): 
   summary()

if __name__ == '__main__': 
   main()
