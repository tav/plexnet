--- setup.py	2008-12-10 20:46:32.000000000 +0000
+++ setup.py.plexnet	2008-12-10 20:51:28.000000000 +0000
@@ -118,6 +118,12 @@
         library_dirs = []
         include_dirs = []
 
+        from plexnetenv import PLEXNET_LOCAL, join_path
+
+        add_directory(library_dirs, join_path(PLEXNET_LOCAL, 'lib'))
+        add_directory(include_dirs, join_path(PLEXNET_LOCAL, 'include'))
+        add_directory(include_dirs, join_path(PLEXNET_LOCAL, 'include', 'freetype2'))
+
         add_directory(include_dirs, "libImaging")
 
         #
@@ -306,6 +312,7 @@
             # locate Tcl/Tk frameworks
             frameworks = []
             framework_roots = [
+                join_path(PLEXNET_LOCAL, 'framework'),
                 "/Library/Frameworks",
                 "/System/Library/Frameworks"
                 ]
