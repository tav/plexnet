--- Lib/ihooks.py	2008-05-10 23:45:07.000000000 +0100
+++ Lib/ihooks.py.plexnet	2008-12-10 20:26:51.000000000 +0000
@@ -359,7 +359,7 @@
     def set_hooks(self, hooks):
         return self.loader.set_hooks(hooks)
 
-    def import_module(self, name, globals={}, locals={}, fromlist=[]):
+    def import_module(self, name, globals={}, locals={}, fromlist=[], level=-1):
         name = str(name)
         if name in self.modules:
             return self.modules[name] # Fast path
@@ -401,7 +401,7 @@
 
     """A module importer that supports packages."""
 
-    def import_module(self, name, globals=None, locals=None, fromlist=None):
+    def import_module(self, name, globals=None, locals=None, fromlist=None, level=-1):
         parent = self.determine_parent(globals)
         q, tail = self.find_head_package(parent, str(name))
         m = self.load_tail(q, tail)
