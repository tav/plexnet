--- bindings/python/SConscript	2008-12-04 04:43:01.000000000 +0000
+++ bindings/python/SConscript.plexnet	2008-12-04 04:44:40.000000000 +0000
@@ -25,13 +25,16 @@
 
 Import('env')
 
-if env.Execute('pkg-config --exists pycairo') == 0:   
-    env.ParseConfig('pkg-config --cflags pycairo')
-    env.Append(CXXFLAGS = '-DHAVE_PYCAIRO');
+# if env.Execute('pkg-config --exists pycairo') == 0:   
+#     env.ParseConfig('pkg-config --cflags pycairo')
+#     env.Append(CXXFLAGS = '-DHAVE_PYCAIRO');
 
 prefix = env['PYTHON_PREFIX'] + '/' + env['LIBDIR_SCHEMA'] + '/python' + env['PYTHON_VERSION'] + '/site-packages/'
 install_prefix = env['DESTDIR'] + '/' + prefix
 
+import distutils.sysconfig, plexnetenv
+install_prefix = distutils.sysconfig.get_python_lib()
+
 thread_suffix = '-mt'
 
 if env['PLATFORM'] == 'FreeBSD':
@@ -55,17 +58,19 @@
         libraries.append('boost_thread%s%s' % (env['BOOST_APPEND'],thread_suffix))
     if '-DHAVE_PYCAIRO' in env['CXXFLAGS']:
         libraries.append([lib for lib in env['LIBS'] if lib.startswith('cairo')])
-    linkflags = '-F/ -framework Python'
+    linkflags = '-F%s -framework Python' % os.path.join(plexnetenv.PLEXNET_LOCAL, 'framework')
 
 headers = [env['PYTHON_PREFIX'] + '/include/python' + env['PYTHON_VERSION']] + env['CPPPATH']
 
 _mapnik = env.LoadableModule('_mapnik', glob.glob('*.cpp'), LIBS=libraries, LDMODULEPREFIX='', LDMODULESUFFIX='.so', CPPPATH=headers,LINKFLAGS=linkflags)
 
+from os.path import join as join_path
+
 paths = """
-mapniklibpath = '%s'
+mapniklibpath = '%%s'
 inputpluginspath = mapniklibpath + '/input'
-fontscollectionpath = mapniklibpath + '/fonts'
-"""
+fontscollectionpath = %r
+""" % join_path(plexnetenv.PLEXNET_LOCAL, 'share', 'font', 'dejavu')
 
 exp =  r"%s{2,}" % os.sep
 mapnik_plugins_dir  = re.sub(exp,os.sep, env['PREFIX'] + '/'+env['LIBDIR_SCHEMA']+'/mapnik')
