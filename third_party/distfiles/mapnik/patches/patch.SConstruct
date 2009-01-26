40d39
< opts.Add(PathOption('BOOST_LIBS', 'Search path for boost library files', '/usr/' + LIBDIR_SCHEMA))
44,57c43,44
< opts.Add(PathOption('ICU_INCLUDES', 'Search path for ICU include files', '/usr/include'))
< opts.Add(PathOption('ICU_LIBS','Search path for ICU include files','/usr/' + LIBDIR_SCHEMA))
< opts.Add(PathOption('PNG_INCLUDES', 'Search path for libpng include files', '/usr/include'))
< opts.Add(PathOption('PNG_LIBS','Search path for libpng include files','/usr/' + LIBDIR_SCHEMA))
< opts.Add(PathOption('JPEG_INCLUDES', 'Search path for libjpeg include files', '/usr/include'))
< opts.Add(PathOption('JPEG_LIBS', 'Search path for libjpeg library files', '/usr/' + LIBDIR_SCHEMA))
< opts.Add(PathOption('TIFF_INCLUDES', 'Search path for libtiff include files', '/usr/include'))
< opts.Add(PathOption('TIFF_LIBS', 'Search path for libtiff library files', '/usr/' + LIBDIR_SCHEMA))
< opts.Add(PathOption('PGSQL_INCLUDES', 'Search path for PostgreSQL include files', '/usr/include'))
< opts.Add(PathOption('PGSQL_LIBS', 'Search path for PostgreSQL library files', '/usr/' + LIBDIR_SCHEMA))
< opts.Add(PathOption('PROJ_INCLUDES', 'Search path for PROJ.4 include files', '/usr/local/include'))
< opts.Add(PathOption('PROJ_LIBS', 'Search path for PROJ.4 library files', '/usr/local/' + LIBDIR_SCHEMA))
< opts.Add(PathOption('GDAL_INCLUDES', 'Search path for GDAL include files', '/usr/include'))
< opts.Add(PathOption('GDAL_LIBS', 'Search path for GDAL library files', '/usr/' + LIBDIR_SCHEMA))
---
> opts.Add(PathOption('ADDITIONAL_LIB_PATH','Search path for library files','/usr/' + LIBDIR_SCHEMA))
> opts.Add(PathOption('ADDITIONAL_INCLUDE_PATH','Search path for library files','/usr/include'))
127,134c114,122
< # Adding the prerequisite library directories to the include path for
< # compiling and the library path for linking, respectively.
< for prereq in ('BOOST', 'PNG', 'JPEG', 'TIFF', 'PGSQL', 'PROJ', 'GDAL',):
<     inc_path = env['%s_INCLUDES' % prereq]
<     lib_path = env['%s_LIBS' % prereq]
<     uniq_add(env, 'CPPPATH', inc_path)
<     uniq_add(env, 'LIBPATH', lib_path)
<     
---
> if env['BOOST_INCLUDES'] not in env['CPPPATH']:
>     env['CPPPATH'].append(env['BOOST_INCLUDES'])
> 
> if env['ADDITIONAL_LIB_PATH'] not in env['LIBPATH']:
>     env['LIBPATH'].append(env['ADDITIONAL_LIB_PATH'])
> 
> if env['ADDITIONAL_INCLUDE_PATH'] not in env['CPPPATH']:
>     env['CPPPATH'].append(env['ADDITIONAL_INCLUDE_PATH'])
> 
137,139c125,127
< if env.Execute('pkg-config --exists cairomm-1.0') == 0:
<     env.ParseConfig('pkg-config --libs --cflags cairomm-1.0')
<     env.Append(CXXFLAGS = '-DHAVE_CAIRO');
---
> # if env.Execute('pkg-config --exists cairomm-1.0') == 0:
> #     env.ParseConfig('pkg-config --libs --cflags cairomm-1.0')
> #     env.Append(CXXFLAGS = '-DHAVE_CAIRO');
236a225
> 
296,299d284
< 
< 
< SConscript('fonts/SConscript')
< 
