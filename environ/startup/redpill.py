"""
[redpill %(__version__)s]


                        _         _ _ _ 
           _ __ ___  __| |  _ __ (_) | |
          | '__/ _ \/ _` | | '_ \| | | |
          | | |  __/ (_| | | |_) | | | |
          |_|  \___|\__,_| | .__/|_|_|_|
                           |_|          

Usage: redpill [options]
Options:

  help            Display the help text.
  init            Compile and install all dependencies.
  version         Print the version number and exit.

  --verbose       Print updates relating to internals.

The ``redpill`` bootstraps you into the world of Espia.
%(__additional__)s
For now, simply run ``redpill init`` to get started.
"""

import os
import shutil
import sys
import tarfile

import plexnetenv
import gclient

from glob import glob
from os import stat, getcwd, listdir
from os.path import isdir, isfile, join as join_path, expanduser
from posixpath import split as posix_split
from shutil import rmtree
from subprocess import Popen, PIPE
from time import time
from urllib import urlopen

# ------------------------------------------------------------------------------
# do a chek for the required minimal python version and get out early if not met
# ------------------------------------------------------------------------------

__min_python_version__ = (2, 6, 1)

if not hasattr(sys, 'hexversion') or sys.version_info < __min_python_version__:

    try:
        print >> sys.stderr, "You need to have at least Python version",
        print >> sys.stderr, '.'.join(map(str, __min_python_version__)),
    except:
        sys.stderr.write("You do not have the required Python version.")

    sys.stderr.write('\n')

    version = __min_python_version__

    if len(version) == 3 and (version[-1] == 0):
        version = version[:2]

    version = '.'.join(map(str, version))

    if sys.platform == "darwin":

        print """
You can download a Universal build here:

  <http://www.python.org/ftp/python/%s/python-%s-macosx.dmg>
""" % (version, version)

    elif sys.platform == "win32":
        print """
You can download it here:

  <http://www.python.org/ftp/python/%s/python-%s.msi>
""" % (version, version)

    else:
        print """
This is often available in your operating system's native package format (via
apt-get or yum, for instance). You can also easily build Python from source on
Unix-like systems. Here is the source download link for Python:

  <http://www.python.org/ftp/python/%s/Python-%s.tgz>
""" % (version, version)

    sys.exit(1)

# ------------------------------------------------------------------------------
# distutils klassifiers and dependensies
# ------------------------------------------------------------------------------

CLASSIFIERS = filter(None, map(str.strip, """

    Development Status :: 3 - Alpha
    Intended Audience :: Developers
    Environment :: Operating System
    Natural Language :: English
    Operating System :: OS Independent
    Operating System :: POSIX
    Operating System :: Unix
    Operating System :: Microsoft :: Windows
    Programming Language :: Python
    Topic :: Software Development :: Libraries :: Python Modules

    """.splitlines()))

DOWNLOAD_MAP = [
    # 'ZODB3>=3.8.1b6',
    # ('rel', 'http://code.google.com/p/registeredeventlistener/downloads/list', 1),
    # 'ipython>=0.8.1',
    # 'pycrypto>=2.0.1',
    # ('pydns', 'http://sourceforge.net/project/showfiles.php?group_id=31674', 1),
    # ('PyObjC', 'http://pyobjc.sourceforge.net/software/pyobjc-1.4.tar.gz'),
    # ('lightblue',
    # http://prdownloads.sourceforge.net/lightblue/lightblue-0.2.2.tar.gz?download
    ]

DEPENDENCIES = [(isinstance(i, tuple) and i[0] or i) for i in DOWNLOAD_MAP]

# ------------------------------------------------------------------------------
# some konstants
# ------------------------------------------------------------------------------

__version__ = '0.1'
__additional__ = ''

DISTFILES_SERVER = "http://release.plexnet.org/distfiles"

STARTUP_DIRECTORY = plexnetenv.STARTUP_DIRECTORY
PLEXNET_ROOT = plexnetenv.PLEXNET_ROOT
PLEXNET_LOCAL = plexnetenv.PLEXNET_LOCAL
PLEXNET_INSTALLED = join_path(PLEXNET_LOCAL, 'share', 'installed')
PLEXNET_SOURCE = plexnetenv.PLEXNET_SOURCE
PYTHON_SITE_PACKAGES = plexnetenv.PYTHON_SITE_PACKAGES
THIRD_PARTY = plexnetenv.THIRD_PARTY

BASH_MESSAGE = """export PLEXNET_ROOT="%s"
source $PLEXNET_ROOT/environ/startup/plexnetenv.sh install
""" % PLEXNET_ROOT

CURRENT_DIRECTORY = os.getcwd()
USER_HOME = expanduser('~')
PLAT_EXT = ['.so', '.dll'][os.name == 'nt']

ACTION = '\x1b[34;01m>> '
INSTRUCTION = '\x1b[31;01m!! '
ERROR = '\x1b[31;01m!! '
NORMAL = '\x1b[0m'
PROGRESS = '\x1b[30;01m## '
SUCCESS = '\x1b[32;01m** '

if sys.platform == 'win32':
    INSTRUCTION = ACTION = '>> '
    ERROR = '!! '
    NORMAL = ''
    PROGRESS = '## '
    SUCCESS = '** '

try:
    from multiprocessing import cpu_count
    CPUS = cpu_count()
except:
    CPUS = 1

if CPUS > 1:
    PARALLEL = '-j%i' % CPUS
else:
    PARALLEL = ''

MTIME_CACHE = {}
LOCAL_FILELISTING = set()

class AlreadyInstalled(Exception):
    """Error raised when a package is detected to have already been installed."""

FLAGGED = None

# ------------------------------------------------------------------------------
# utility funktions
# ------------------------------------------------------------------------------

def get_mtime(file, directory=None, usecache=True):
    """Return the last modified time of the given file."""
    if directory is not None:
        file = join_path(directory, *file.split('/')) # posixpath
    if usecache:
        if file in MTIME_CACHE:
            return MTIME_CACHE[file]
    try:
        mtime = stat(file).st_mtime
    except OSError:
        mtime = 0
    if usecache:
        return MTIME_CACHE.setdefault(file, mtime)
    return mtime

def get_flag(flag, alter=True):
    """Return whether a specific flag is set in the command line parameters."""

    flagc = '%s:' % flag
    argv = []
    retval = None
    for arg in sys.argv:
        if arg == flag:
            retval = True
        elif arg.startswith(flagc):
            retval = arg.split(flagc, 1)[1] or True
        else:
            argv.append(arg)
    if alter:
        sys.argv[:] = argv
        if retval:
            global FLAGGED
            FLAGGED = True
    return retval

def install_dot_file(file, force=False, directory=False):
    """Copy the .dotfile to the user's home directory."""

    source = join_path(STARTUP_DIRECTORY, 'config', *posix_split(file))
    dest = join_path(USER_HOME, *posix_split('.'+file))
    if directory:
        if (not isdir(dest)) or force:
            print('Writing: %s' % dest)
            shutil.copytree(source, dest)
        else:
            print('Already Exists: %s' % dest)
    else:
        if (not isfile(dest)) or force:
            print('Writing: %s' % dest)
            shutil.copy(source, dest)
        else:
            print('Already Exists: %s' % dest)

def print_message(message, type=ACTION):
    """Pretty print the given ``message`` in nice colours."""

    print(type + message + NORMAL)
    print('')

def gather_local_filelisting(directory=PLEXNET_LOCAL, gathered=None):
    """Return a set of all resources inside the given ``directory``."""

    if gathered is None:
        if not isdir(directory):
            return set()
        gathered = set()

    for item in listdir(directory):
        path = join_path(directory, item)
        if isdir(path):
            gathered.add(path + '/')
            gather_local_filelisting(path, gathered)
        else:
            if path.endswith('.pyc') or path.endswith('.pyo'):
                continue
            gathered.add(path)

    return gathered

def compile_from_source_tarball(
    name, version, commands=None, config_command='./configure', config_flags='',
    separate_make_install=False, make_flags="install"
    ):
    """Compile and install from a source tarball."""

    try:
        dest_dir, path_prefix = untar(name, version)
    except AlreadyInstalled:
        return

    if commands is None:
        commands = []; add = commands.append
        add("%s %s --prefix=%s" % (config_command, config_flags, PLEXNET_LOCAL))
        if separate_make_install:
            add("make"); add("make %s" % make_flags)
        else:
            add("make %s" % make_flags)
    else:
        if isinstance(commands, basestring):
            commands = [commands]
        elif callable(commands):
            commands = commands()

    if not isinstance(commands, (tuple,list)):
        raise ValueError("%r is not a tuple" % commands)

    for command in commands:
        print_message("Running: %s" % command, PROGRESS)
        proc = Popen(command, shell=True)
        status = proc.wait()
        if status:
            print_message("Error running: %s" % command, ERROR)
            sys.exit(1)

    return rmsource(name, version, dest_dir, path_prefix)

def untar(name, version):
    """Extract source files from a tarball and enter the source directory."""

    global LOCAL_FILELISTING

    if not LOCAL_FILELISTING:
        LOCAL_FILELISTING = gather_local_filelisting()

    if version:
        path_prefix = "%s-%s" % (name.lower(), version)
    else:
        path_prefix = name.lower()

    if os.path.exists(join_path(PLEXNET_INSTALLED, path_prefix)):
        raise AlreadyInstalled(path_prefix)

    print_message("Installing %s %s" % (name, version), ACTION)
    dest_dir = join_path(THIRD_PARTY, 'distfiles', name.lower())
    os.chdir(dest_dir)

    tarball_filename = '%s.tar.bz2' % path_prefix

    try:
        tar = tarfile.open(tarball_filename, 'r:bz2')
    except:
        print_message("Downloading %s" % tarball_filename, PROGRESS)
        distfile = urlopen(
            "%s/%s/%s" % (DISTFILES_SERVER, name.lower(), tarball_filename)
            )
        tarball_source = distfile.read()
        tarball_file = open(tarball_filename, 'wb')
        tarball_file.write(tarball_source)
        distfile.close()
        tarball_file.close()
        tar = tarfile.open(tarball_filename, 'r:bz2')
        
    print_message("Unpacking %s" % tarball_filename, PROGRESS)
    tar.extractall()
    tar.close()

    os.chdir(path_prefix)

    return dest_dir, path_prefix

def rmsource(name, version, dest_dir, path_prefix):
    """Remove the extracted source and build files and then write a receipt."""

    os.chdir(dest_dir)
    # gclient.RemoveDirectory(path_prefix)
    rmtree(join_path(dest_dir, path_prefix))
    print_message("Successfully Installed %s %s" % (name, version), SUCCESS)

    global LOCAL_FILELISTING

    new_listing = gather_local_filelisting()
    receipt_data = new_listing.difference(LOCAL_FILELISTING)
    LOCAL_FILELISTING = new_listing

    receipt = open(join_path(PLEXNET_INSTALLED, path_prefix), 'wb')
    receipt.write('\n'.join(receipt_data))
    receipt.close()

    return True

def copy_from_resource_tarball(name, version, source, destination):
    """Extract and copy resource files from a tarball to a ``destination`` ."""

    if not isinstance(destination, tuple):
        raise ValueError("%r is not a tuple" % destination)

    try:
        dest_dir, path_prefix = untar(name, version)
    except AlreadyInstalled:
        return

    print_message("Copying resources for %s %s" % (name, version), PROGRESS)
    src = join_path(dest_dir, path_prefix, source)
    dst = join_path(PLEXNET_LOCAL, *destination)
    shutil.copytree(src, dst)

    return rmsource(name, version, dest_dir, path_prefix)

def get_boost_commands():
    """Compile Boost Jam and Return the boost compile commands."""

    cur_dir = os.getcwd()

    user_config = open('user-config.jam', 'wb')
    user_config.write("using python : 2.6 : %s ;\n" % sys.prefix)
    user_config.close()

    jam_dir = join_path(cur_dir, 'tools', 'jam', 'src')
    os.chdir(jam_dir)

    print_message("Compiling Boost Jam", PROGRESS)
    proc = Popen('./build.sh', shell=True)
    status = proc.wait()
    if status:
        print_message("Error compiling Boost Jam", ERROR)
        sys.exit(1)

    TOOLSET = Popen(['./build.sh', '--guess-toolset'], stdout=PIPE).communicate()[0].strip()

    cmd = """./tools/jam/src/bin.*/bjam -sICU_PATH=%s --user-config=user-config.jam --prefix=%s --toolset=%s --with-thread --with-filesystem --with-regex --with-program_options --with-python --with-system --with-iostreams %s""" % (PLEXNET_LOCAL, PLEXNET_LOCAL, TOOLSET, PARALLEL)

    os.chdir(cur_dir)

    return ("%s stage" % cmd, "%s install" % cmd)

def install_python_package(name, version):
    """Compile and install the Python package from a source tarball."""
    return compile_from_source_tarball(
        name, version, '%s setup.py install' % PYTHON_EXE
        )

def install_python_package_in_directory(directory):
    """Compile and install the python package in the given ``directory``."""

    path = join_path(PYTHON_SITE_PACKAGES, directory)
    os.chdir(path)
    os.system("%s setup.py install" % sys.executable)
    gclient.RemoveDirectory(path, 'build')
    os.chdir(CURRENT_DIRECTORY)

def get_extensions(directory, source='.c', compiled=PLAT_EXT, filename_only=0):
    """Return a list of Extensions that need to be compiled."""

    sep = os.sep
    extensions = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = join_path(dirpath, filename)
            if filename.endswith(source) and (not filename[0] == '.'):
                filebase = filepath[:-len(source)]
                if get_mtime(filepath, usecache=0) > get_mtime(filebase + compiled, usecache=0):
                    if filename_only:
                        extensions.append(filepath)
                    else:
                        module = filebase[len(directory+sep):].replace(sep, '.')
                        extensions.append(Extension(module, [filepath]))
    return extensions

def do_action_in_directory(action, past_action, directory, function):
    """Print progress of a function's action in a given directory."""

    try:
        print_message("%s in %s" % (action, directory), ACTION)
        function()
    except:
        print_message("Error %s in %s" % (action, directory), ERROR)
    else:
        print_message(
            "Successfully %s %s in %s" % (
                past_action, ' '.join(action.split()[1:]), directory
                ),
            SUCCESS)

# ------------------------------------------------------------------------------
# egg dependencies
# ------------------------------------------------------------------------------

def install_dependencies_via_eggs(download_map=DOWNLOAD_MAP):
    """Install various dependencies available as Python Eggs."""

    from setuptools.command.easy_install import main

    download_list = []

    from pkg_resources import require, VersionConflict, DistributionNotFound

    for item in download_map:

        prepend = None

        if len(item) == 2:
            item, path = item
        elif len(item) == 3:
            item, search_path, spam = item
            path = item
            prepend = ['-f', search_path]
        else:
            path = item

        try:
            require(item)
        except (VersionConflict, DistributionNotFound):
            if prepend:
                download_list[0:0] = prepend
            download_list.append(path)

    if download_list:
        return main(download_list)

# ------------------------------------------------------------------------------
# help
# ------------------------------------------------------------------------------

if get_flag('--help') or get_flag('help') or get_flag('-h') or get_flag('-H'):
    print __doc__ % locals()
    sys.exit(0)

if get_flag('--version') or get_flag('version') or get_flag('-v') or get_flag('-V'):
    print "redpill %s" % __version__
    sys.exit(0)

# ------------------------------------------------------------------------------
# init
# ------------------------------------------------------------------------------

# @/@ currently only tested for OS X 10.5 -- most packages are from MacPorts

if get_flag('init'):

    if not os.path.exists(PLEXNET_INSTALLED):
        os.makedirs(PLEXNET_INSTALLED)

    PYTHON_EXE = sys.executable
    SCONS_EXE = '%s -c "import SCons.Script; SCons.Script.main()"' % PYTHON_EXE

    SYSTEM_LOCAL = '/usr'
    SYSTEM_INCLUDE = '/usr/include'
    SYSTEM_LIB = '/usr/lib'

    PLEXNET_INCLUDE = join_path(PLEXNET_LOCAL, 'include')
    PLEXNET_BIN = join_path(PLEXNET_LOCAL, 'bin')
    PLEXNET_LIB = join_path(PLEXNET_LOCAL, 'lib')
    PLEXNET_MAN = join_path(PLEXNET_LOCAL, 'man')
    PLEXNET_FRAMEWORK = join_path(PLEXNET_LOCAL, 'framework')

    LIBTIFF_EXTRA = ''
    PYTHON3_EXTRA = ''
    LIBJPEG_EXTRA = ''

    if sys.platform == 'darwin':
        ICU_PLATFORM = 'MacOSX'
        LIBTIFF_EXTRA = ' --with-apple-opengl-framework'
        PYTHON3_EXTRA = '--enable-framework=%s' % PLEXNET_FRAMEWORK
    elif sys.platform == 'freebsd':
        ICU_PLATFORM = 'FreeBSD'
    elif sys.platform.startswith('linux'):
        ICU_PLATFORM = 'Linux'
        LIBJPEG_EXTRA = 'LIBTOOL=libtool'
    elif sys.platform.startswith('cygwin'):
        ICU_PLATFORM = 'Cygwin'

    # libxml2, libiconv, openssl/crypto, libexpat | curl, ncurses

    compile_from_source_tarball(
        'pkg-config', '0.23',
        config_flags='--mandir=%s --enable-indirect-deps --with-pc-path=%s/lib/pkgconfig:%s/share/pkgconfig' % (PLEXNET_MAN, PLEXNET_LOCAL, PLEXNET_LOCAL)
        )

    compile_from_source_tarball(
        'ICU', '4.0', config_command='./runConfigureICU',
        config_flags='%s --disable-samples --disable-tests --sbindir=%s' % (ICU_PLATFORM, PLEXNET_BIN)
        )

    compile_from_source_tarball('Freetype', '2.3.7')

    compile_from_source_tarball('Boost', '1.37', get_boost_commands)

    compile_from_source_tarball(
        'libPNG', '1.2.32', config_flags='--mandir=%s' % PLEXNET_MAN
        )

    compile_from_source_tarball(
        'libJPEG', '6b', config_flags="--enable-shared --enable-static",
        make_flags="%s install" % LIBJPEG_EXTRA
        )

    compile_from_source_tarball(
        'TIFF', '3.8.2',
        config_flags="--mandir=%s --with-jpeg-include-dir=%s --with-jpeg-lib-dir=%s --with-zlib-include-dir=%s --with-zlib-lib-dir=%s%s" % (PLEXNET_MAN, PLEXNET_INCLUDE, PLEXNET_LIB, SYSTEM_INCLUDE, SYSTEM_LIB, LIBTIFF_EXTRA)
        )
    # --with-docdir=${prefix}/share/doc/${name}-${version}

    compile_from_source_tarball(
        'PROJ', '4.6.0', config_flags='--mandir=%s' % PLEXNET_MAN
        )

    compile_from_source_tarball(
        'libgeotiff', '1.2.1',
        config_flags="--with-zip=%s --with-jpeg=%s --with-proj=%s --with-libtiff=%s --enable-incode-epsg" % (
            SYSTEM_LOCAL, PLEXNET_LOCAL, PLEXNET_LOCAL, PLEXNET_LOCAL
            ),
        separate_make_install=True
        )

    compile_from_source_tarball(
        'gdal', '1.5.1',
        config_flags="--mandir=%s --with-libz=%s --with-png=%s --with-jpeg=%s --with-libtiff=%s --with-geotiff=%s --with-static-proj4=%s --without-sqlite3 --without-python --without-pg --without-mysql --without-sqlite" % (PLEXNET_MAN, SYSTEM_LOCAL, PLEXNET_LOCAL, PLEXNET_LOCAL, PLEXNET_LOCAL, PLEXNET_LOCAL, PLEXNET_LOCAL)
        )

    compile_from_source_tarball('speex', 'fs.svn.r10488')

    copy_from_resource_tarball(
        'dejavu', '2.14', 'dejavu', ('share', 'font', 'dejavu')
        )

    copy_from_resource_tarball(
        'unicode', '5.1.0', 'unicode', ('share', 'unicode')
        )

    BOOST_TOOLKIT = glob(
        '%s%slibboost_system*' % (PLEXNET_LIB, os.sep)
        )[0].split('-')[1]

    compile_from_source_tarball(
        'mapnik', 'svn.r770',
        "%s PREFIX=%s BOOST_INCLUDES=%s BOOST_TOOLKIT=%s ADDITIONAL_LIB_PATH=%s ADDITIONAL_INCLUDE_PATH=%s %s install" % (
            SCONS_EXE, PLEXNET_LOCAL,
            join_path(PLEXNET_LOCAL, 'include', 'boost-1_37'),
            BOOST_TOOLKIT, PLEXNET_LIB, PLEXNET_INCLUDE, PARALLEL
            )
        )

    compile_from_source_tarball(
        'libevent', '1.4.8', config_flags='--mandir=%s' % PLEXNET_MAN
        )

    copy_from_resource_tarball(
        'geoipdata', '2008.11', 'geoipdata', ('share', 'geoipdata')
        )

    compile_from_source_tarball('libgeoip', '1.4.5')

    compile_from_source_tarball(
        'miniupnpc', '1.2', (SCONS_EXE, 'make install')
        )

    compile_from_source_tarball(
        'libnatpmp', '20081006', (SCONS_EXE, 'make install')
        )

    compile_from_source_tarball('liboil', 'git.200811')

    compile_from_source_tarball(
        'lame', 'cvs.200811',
        config_flags='--mandir=%s --disable-gtktest' % PLEXNET_MAN
        )

    compile_from_source_tarball(
        'x264', 'git.200811', config_flags='--disable-asm'
        )

    compile_from_source_tarball(
        'faac', '1.26', config_command='./bootstrap && ./configure'
        )

    compile_from_source_tarball(
        'libschroedinger', 'git.200811', config_command='./autogen.sh',
        config_flags='--disable-gtk-doc'
        )

    compile_from_source_tarball(
        'mplayer', 'svn.r27979',
        config_flags='--codecsdir=%s/share/codecs --mandir=%s' % (PLEXNET_LOCAL, PLEXNET_MAN)
        )

    compile_from_source_tarball(
        'freeswitch', 'svn.r10488',
        ('./bootstrap.sh', './configure --prefix=%s --mandir=%s' %
         (join_path(PLEXNET_LOCAL, 'freeswitch'), PLEXNET_MAN))
        )

    copy_from_resource_tarball('sounds', '1.0.6', 'sounds', ('share', 'sounds'))

    copy_from_resource_tarball('win32codecs', '', 'codecs', ('share', 'codecs'))

    compile_from_source_tarball(
        'python', '3.0', config_flags='--enable-ipv6 %s' % PYTHON3_EXTRA
        )

    # @/@ fixup "Current" framework version on OS X ?

    try:
        import pkg_resources
    except:
        SETUPTOOLS = 'setuptools-0.6c9'
        EGG_PATH = '%s-py2.6.egg' % SETUPTOOLS
        print_message("Installing %s" % EGG_PATH, ACTION)
        os.chdir(join_path(THIRD_PARTY, 'distfiles', 'setuptools'))
        proc = Popen(
            'sh %s --script-dir=%s -O2' % (EGG_PATH, PLEXNET_BIN),
            shell=True
            )
        status = proc.wait()
        if status:
            print_message("Error Installing %s" % SETUPTOOLS, ERROR)
            sys.exit(1)
        print_message("Successfully Installed %s" % SETUPTOOLS, SUCCESS)
        for path in sys.path:
            if isdir(path) and EGG_PATH in listdir(path):
                sys.path.append(join_path(path, EGG_PATH))

    install_python_package('pyopenssl', '0.8')
    install_python_package('pytz', '2009a')
    install_python_package('pil', '1.1.6')
    install_python_package('numpy', '1.2.1')

    original_argv = sys.argv

    from setuptools import setup, find_packages, Extension

    sys.argv[1:] = ['build_ext', '--inplace']
    os.chdir(PYTHON_SITE_PACKAGES)
    pyc_extensions = []

    EXTENSIONS = {
        'extension.GeoIP': (['extension/GeoIP.c'], ['GeoIP']),
        'extension.greenlet': ['greenlet/greenlet.c'],
        'extension.speex': (['extension/speex.c'], ['speex'], ['speex']),
        'extension.TimeStamp': ['extension/TimeStamp.c'],
        'extension.whirlpool': ['extension/whirlpool.c'],
        'genshi._speedups': ['genshi/_speedups.c'],
        'gdata.tlslite.utils.entropy': ['gdata/tlslite/utils/entropy.c'],
        # '_uuid': ['uuid.c', 'pyuuid.c'],
        }

    if sys.platform == "win32":
        EXTENSIONS['gdata.tlslite.utils.win32prng'] = ['gdata/tlslite/utils/win32prng.c']

    for name, sources in EXTENSIONS.iteritems():
        dest_mtime = get_mtime(name.replace('.', '/') + PLAT_EXT)
        include_dirs = [PLEXNET_INCLUDE]
        if isinstance(sources, tuple):
            if len(sources) == 2:
                sources, libraries = sources
            else:
                sources, libraries, additional_includes = sources
                for inc in additional_includes:
                    include_dirs.append(join_path(PLEXNET_INCLUDE, inc))
        else:
            libraries = []
        for source in sources:
            if get_mtime(source) > dest_mtime:
                pyc_extensions.append(Extension(
                    name, sources, include_dirs=include_dirs,
                    libraries=libraries, library_dirs=[PLEXNET_LIB],
                    ))
                break

    if pyc_extensions:
        do_action_in_directory(
            "Compiling Extensions", "Compiled", PYTHON_SITE_PACKAGES,
            lambda : setup(ext_modules=pyc_extensions),
            )
        gclient.RemoveDirectory(join_path(PYTHON_SITE_PACKAGES, 'build'))

    import plexnet as PACKAGE
    from Cython.Compiler.Main import main as compile_cython

    if original_argv[1:] and original_argv[1] == '--build':
        setup(
            name=PACKAGE.__name__,
            version=PACKAGE.__release__,
            url=PACKAGE.__moreinfo__[0],
            description=PACKAGE.__doc__.strip().splitlines()[0],
            long_description=PACKAGE.__doc__,
            author=PACKAGE.__maintainer__[0],
            author_email=PACKAGE.__maintainer__[1],
            license=PACKAGE.__copyright__[0],
            classifiers=CLASSIFIERS,
            test_suite='',
            packages=find_packages(exclude=['ez_setup']),
            include_package_data=True,
            namespace_packages=[PACKAGE.__name__],
            zip_safe=True,
            install_requires=DEPENDENCIES,
        )

    else:

        # @/@ hmz, can we just use `python setup.py develop` ?

        PKG_DIRECTORY = join_path(PLEXNET_SOURCE, PACKAGE.__name__)
        os.chdir(PKG_DIRECTORY)

        pyx_files = get_extensions(PKG_DIRECTORY, '.pyx', '.c', True)
        if pyx_files:
            sys.argv[1:] = pyx_files
            do_action_in_directory(
                "Compiling Cython files", "Compiled", PKG_DIRECTORY,
                compile_cython
                )

        sys.argv[1:] = ['build_ext', '--inplace']
        pyc_extensions = get_extensions(PKG_DIRECTORY)
        if pyc_extensions:
            do_action_in_directory(
                "Compiling Extensions", "Compiled", PKG_DIRECTORY,
                lambda : setup(name=PACKAGE.__name__, ext_modules=pyc_extensions),
                )

        gclient.RemoveDirectory(join_path(PKG_DIRECTORY, 'build'))

    sys.argv = original_argv

# ------------------------------------------------------------------------------
# @/@ these need to be implemented
# ------------------------------------------------------------------------------

if get_flag('update'):
    pass

if get_flag('commit'):
    pass

if get_flag('startupfiles'): # @/@ generate startup tarballs/zipfiles
    pass

# ------------------------------------------------------------------------------
# env info
# ------------------------------------------------------------------------------

if not os.environ.get('PLEXNET_INSTALLED', ''):
    if os.name == 'posix':
        for i in xrange(1):
            print
            print_message(
                "Add the following %i lines to %s !!"
                % (len(BASH_MESSAGE.splitlines()),
                   join_path(USER_HOME, '.bash_profile')
                   ), INSTRUCTION
                )
            print(BASH_MESSAGE)

# ------------------------------------------------------------------------------
# emulate ``scons`` when not called from the enklosing direktory
# ------------------------------------------------------------------------------

__additional__ = """
In particular, it aims to provide the following functionality:

* Initial download of the Plexnet source code
* Compilation of the source code
* Installation of related applications/scripts
* Application runners
* Source code update facilities
* Generation of documentation and release files

Everything you ever wanted to know about life, the universe,
and everything!

# Motivation

The red pill derives from earlier work done as part of the
``espSetup`` project which provided a single self-update-able
application which was used to install and update other apps.

In fact, it is expected that a future version of the redpill
will have pretty front-end GUI applications like ``espSetup``.
"""

if FLAGGED:
    sys.exit()

if CURRENT_DIRECTORY != STARTUP_DIRECTORY:
    if os.path.exists(join_path(CURRENT_DIRECTORY, 'SConstruct')):
        import SCons.Script
        SCons.Script.main()
        sys.exit()

print __doc__ % locals()
