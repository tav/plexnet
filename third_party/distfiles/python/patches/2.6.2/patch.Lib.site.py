--- Lib/site.py	2008-12-10 14:05:34.000000000 +0000
+++ Lib/site.py.plexnet	2008-12-10 13:59:14.000000000 +0000
@@ -283,6 +283,13 @@
                         os.path.join("~", "Library", "Python",
                                      sys.version[:3], "site-packages")))
 
+    try:
+        import plexnetenv
+    except:
+        pass
+    else:
+        sitedirs.append(plexnetenv.PYTHON_SITE_PACKAGES)
+
     for sitedir in sitedirs:
         if os.path.isdir(sitedir):
             addsitedir(sitedir, known_paths)
