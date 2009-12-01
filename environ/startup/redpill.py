# Released into the Public Domain. See documentation/legal.txt for more info.
# Author: tav <tav@espians.com>

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
import traceback

import plexnetenv

from glob import glob
from os import stat, getcwd, listdir
from os.path import abspath, dirname, exists, isdir, isfile, join as join_path
from os.path import expanduser
from posixpath import split as posix_split
from shutil import rmtree
from subprocess import Popen, PIPE
from time import time
from urllib import urlopen

from gclient_utils import RemoveDirectory
from lockfile import LockFile, LockError

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

__version__ = '0.2'
__additional__ = ''

DISTFILES_SERVER = (
    "http://cloud.github.com/downloads/tav/plexnet/distfile."
    "%(name)s-%(version)s.tar.bz2"
    )

STARTUP_DIRECTORY = plexnetenv.STARTUP_DIRECTORY
PLEXNET_ROOT = plexnetenv.PLEXNET_ROOT
PLEXNET_LOCAL = plexnetenv.PLEXNET_LOCAL
PLEXNET_INCLUDE = join_path(PLEXNET_LOCAL, 'include')
PLEXNET_INSTALLED = join_path(PLEXNET_LOCAL, 'share', 'installed')
PLEXNET_SOURCE = plexnetenv.PLEXNET_SOURCE
PYTHON_SITE_PACKAGES = plexnetenv.PYTHON_SITE_PACKAGES
ROLES_DIRECTORY = join_path(STARTUP_DIRECTORY, 'roles')
THIRD_PARTY = plexnetenv.THIRD_PARTY
THIRD_PARTY_PACKAGES_ROOT = join_path(THIRD_PARTY, 'distfiles')

BASH_MESSAGE = """export PLEXNET_ROOT="%s"
source $PLEXNET_ROOT/environ/startup/plexnetenv.sh install
""" % PLEXNET_ROOT

CURRENT_DIRECTORY = os.getcwd()
FIRST_RUN = not exists(join_path(PLEXNET_LOCAL, 'bin', 'python'))
HOME = expanduser('~')
LIB_EXTENSION = ['.so', '.dll'][os.name == 'nt']

ACTION = '\x1b[34;01m>> '
INSTRUCTION = '\x1b[31;01m!! '
ERROR = '\x1b[31;01m!! '
NORMAL = '\x1b[0m'
PROGRESS = '\x1b[30;01m## '
SUCCESS = '\x1b[32;01m** '
TERMTITLE = '\x1b]2;%s\x07'

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
PACKAGES = {}
FLAGGED = None

# ------------------------------------------------------------------------------
# exseptions
# ------------------------------------------------------------------------------

class AlreadyInstalled(Exception):
    """Error raised when a package is detected to have already been installed."""

# ------------------------------------------------------------------------------
# kommand line arguments parser
# ------------------------------------------------------------------------------

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

def install_dot_file(file, force=False, directory=False):
    """Copy the .dotfile to the user's home directory."""

    source = join_path(STARTUP_DIRECTORY, 'config', *posix_split(file))
    dest = join_path(HOME, *posix_split('.'+file))
    if directory:
        if (not isdir(dest)) or force:
            print 'Writing: %s' % dest
            shutil.copytree(source, dest)
        else:
            print 'Already Exists: %s' % dest
    else:
        if (not isfile(dest)) or force:
            print 'Writing: %s' % dest
            shutil.copy(source, dest)
        else:
            print 'Already Exists: %s' % dest

def print_message(message, type=ACTION):
    """Pretty print the given ``message`` in nice colours."""

    print type + message + NORMAL
    print ''

def set_term_title(title):
    """Set the Terminal with the given title."""

    print TERMTITLE % title

def download_distfile(distfile, distfile_location):
    """Download the given distfile."""

    if (distfile_location.startswith('http://') or
        distfile_location.startswith('https://')):

        print_message("Downloading %s" % distfile, PROGRESS)
        distfile_obj = urlopen(distfile_location)
        distfile_source = distfile_obj.read()
        distfile_file = open(distfile, 'wb')
        distfile_file.write(distfile_source)
        distfile_obj.close()
        distfile_file.close()

    elif not isfile(distfile_location):

        print_message(
            "Couldn't find distfile for %s %s: %s" %
            (name, version, distfile), ERROR
            )
        sys.exit(1)

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
            gathered.add(path)

    return gathered

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

def install_python_package_in_directory(directory):
    """Compile and install the python package in the given ``directory``."""

    path = join_path(PYTHON_SITE_PACKAGES, directory)
    os.chdir(path)
    os.system("%s setup.py install" % sys.executable)
    RemoveDirectory(path, 'build')
    os.chdir(CURRENT_DIRECTORY)

def get_extensions(directory, source='.c', compiled=LIB_EXTENSION, filename_only=0):
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
# try getting a lock to avoid concurrent redpill use
# ------------------------------------------------------------------------------

try:
    LOCK = LockFile(join_path(STARTUP_DIRECTORY, 'redpill.lock'))
except LockError:
    print_message("Another redpill process is already running", ERROR)
    sys.exit(1)

# ------------------------------------------------------------------------------
# egg dependencies
# ------------------------------------------------------------------------------

def install_setuptools():
    """Install setuptools if it's not already installed."""

    try:
        import pkg_resources
    except:
        SETUPTOOLS = 'setuptools-0.6c11'
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
# build file builtins
# ------------------------------------------------------------------------------

BUILTINS = {

    'abspath': abspath,
    'dirname': dirname,
    'environ': os.environ,
    'exists': exists,
    'glob': glob,
    'isdir': isdir,
    'isfile': isfile,
    'join_path': join_path,
    'os': os,
    'platform': sys.platform,
    'print_message': print_message,
    'sys': sys,

    'Popen': Popen,
    'PIPE': PIPE,

    'INSTRUCTION': INSTRUCTION,
    'ERROR': ERROR,
    'NORMAL': NORMAL,
    'PROGRESS': PROGRESS,
    'SUCCESS': SUCCESS,

    'CPUS': CPUS,
    'CURRENT_DIRECTORY': CURRENT_DIRECTORY,
    'HOME': HOME,
    'LIB_EXTENSION': LIB_EXTENSION,
    'PARALLEL': PARALLEL,

    'PLEXNET_BIN': join_path(PLEXNET_LOCAL, 'bin'),
    'PLEXNET_FRAMEWORK': join_path(PLEXNET_LOCAL, 'framework'),
    'PLEXNET_INCLUDE': PLEXNET_INCLUDE,
    'PLEXNET_LIB': join_path(PLEXNET_LOCAL, 'lib'),
    'PLEXNET_LOCAL': PLEXNET_LOCAL,
    'PLEXNET_MAN': join_path(PLEXNET_LOCAL, 'man'),
    'PLEXNET_ROOT': PLEXNET_ROOT,
    'PLEXNET_SOURCE': PLEXNET_SOURCE,

    'PYTHON_EXE': sys.executable,
    'PYTHON_SITE_PACKAGES': PYTHON_SITE_PACKAGES,
    'SCONS_EXE': (
        '%s -c "import SCons.Script; SCons.Script.main()"' % sys.executable
        ),
    'STARTUP_DIRECTORY': STARTUP_DIRECTORY,
    'SYSTEM_INCLUDE': '/usr/include',
    'SYSTEM_LIB': '/usr/lib',
    'SYSTEM_LOCAL': '/usr',
    'THIRD_PARTY': THIRD_PARTY,

    }

# ------------------------------------------------------------------------------
# build types
# ------------------------------------------------------------------------------

type_base = {
    'after_install': None,
    'before_install': None,
    'commands': None,
    'distfile_location': DISTFILES_SERVER,
    'distfile': "distfile.%(name)s-%(version)s.tar.bz2",
    'env': None,
    }

def command_default(info):

    commands = []; add = commands.append

    add("%s %s --prefix=%s" %
        (info['config_command'], info['config_flags'], PLEXNET_LOCAL))

    if info['separate_make_install']:
        add("make")
        add("make %s" % info['make_flags'])
    else:
        add("make %s" % info['make_flags'])

    return commands

type_default = type_base.copy()
type_default.update({
    'commands': command_default,
    'config_command': './configure',
    'config_flags': '',
    'make_flags': 'install',
    'separate_make_install': False
    })

type_python = type_base.copy()
type_python.update({
    'before_install': install_setuptools,
    'commands': "%s setup.py install" % sys.executable,
    })

def command_resources(info):
    return []

type_resources = type_base.copy()
type_resources.update({
    'commands': command_resources,
    'source': '',
    'destination': '',
    })

types = {
    'default': type_default,
    'python': type_python,
    'resources': type_resources,
    }

# ------------------------------------------------------------------------------
# kore install funktions
# ------------------------------------------------------------------------------

def install_package(name, packages_root=THIRD_PARTY_PACKAGES_ROOT):
    """Read the build file for the given package name."""

    package_name = name.lower()

    if package_name in PACKAGES:
        return

    build_file = join_path(packages_root, package_name, 'build.py')
    builtins = BUILTINS.copy()
    local = {}

    if not isfile(build_file):
        print_message("Couldn't find %s" % build_file, ERROR)

    execfile(build_file, builtins, local)

    if 'versions' not in local:
        print_message(
            "Couldn't find 'versions' variable in build.py for %s" % name, ERROR
            )

    versions = local['versions']
    latest = versions[-1]

    if 'packages' not in local:
        packages = {latest: {}}
    else:
        packages = local['packages']

    PACKAGES[package_name] = {
        'latest': latest,
        'packages': packages,
        'versions': versions
        }

    if 'deps' in packages:
        for dep in packages['deps']:
            install_package(dep)

    for version in versions:
        package = packages[version]
        if 'deps' in package:
            for dep in package['deps']:
                install_package(dep)

def get_package_dependencies(name, version=None, installed=None, gathered=None):
    """Return a set of dependencies for the given package name."""

    if gathered is None:
        gathered = set()

    packages = PACKAGES[name]['packages']
    deps = packages.get('deps', [])[:]

    if not installed:
        version = PACKAGES[name]['latest']

    installed_package = packages.get(version, {})
    deps = deps + installed_package.get('deps', [])

    for dep in deps:
        if installed:
            if dep in installed:
                gathered.add(dep)
                get_package_dependencies(dep, installed[dep], installed, gathered)
        else:
            gathered.add(dep)
            get_package_dependencies(dep, gathered=gathered)

    return gathered

def uninstall_packages(uninstall, installed):
    """Uninstall the given list of packages in uninstall."""

    for name, version in uninstall.iteritems():
        print_message("Uninstalling %s %s" % (name, version))
        installed_version = '%s-%s' % (name, version)
        receipt_path = join_path(PLEXNET_INSTALLED, installed_version)
        receipt = open(receipt_path, 'rb')
        for path in receipt:
            path = path.strip()
            if not path:
                continue
            if not exists(path):
                continue
            if isdir(path):
                rmtree(path)
            else:
                os.remove(path)
        receipt.close()
        os.remove(receipt_path)
        del installed[name]

def install_packages(types=types, altered=False):
    """Handle the actual installation/uninstallation of appropriate packages."""

    if not exists(PLEXNET_INSTALLED):
        os.makedirs(PLEXNET_INSTALLED)

    to_install = set()
    to_install_iteration = None
    inverse_dependencies = {}

    for name in PACKAGES:
        deps = get_package_dependencies(name)
        for dep in deps:
            inverse_dependencies.setdefault(dep, set()).add(name)

    # @/@ assumes invariant that all packages only have one version installed

    installed = dict([f.split('-', 1) for f in listdir(PLEXNET_INSTALLED)])
    uninstall = {}

    for name in list(installed):
        version = installed[name]
        if name not in PACKAGES:
            uninstall[name] = version
        elif PACKAGES[name]['latest'] != version:
            uninstall[name] = version
            for dep in get_package_dependencies(name, version, installed):
                uninstall[dep] = installed[dep]

    uninstall_packages(uninstall, installed)

    while 1:
        if ((to_install_iteration is not None) and
            (to_install_iteration == to_install)):
            to_install = to_install_iteration
            break
        else:
            to_install, to_install_iteration = to_install_iteration, set()
        uninstall = {}
        to_install_iteration = set()
        for name in PACKAGES:
            if name in installed:
                if installed[name] == PACKAGES[name]['latest']:
                    continue
            to_install_iteration.add(name)
            for dep in inverse_dependencies.get(name, []):
                if dep in installed:
                    to_install_iteration.add(dep)
                    uninstall[dep] = installed[dep]
        uninstall_packages(uninstall, installed)

    to_install_list = []

    for name in to_install:
        index = len(to_install_list)
        for dep in inverse_dependencies.get(name, []):
            try:
                dep_index = to_install_list.index(dep)
            except:
                continue
            else:
                if dep_index < index:
                    index = dep_index
        to_install_list.insert(index, name)

    local_filelisting = gather_local_filelisting()

    for name in to_install_list:

        meta = PACKAGES[name]
        versions = meta['versions']
        version = meta['latest']
        packages = meta['packages']
        package = packages[version]

        print_message("Installing %s %s" % (name, version))

        type = package.get('type', meta.get('type', 'default'))
        info = types[type].copy()

        for key in packages:
            if key not in versions:
                info[key] = packages[key]

        info.update(package)

        if info['before_install']:
            info['before_install']()

        dest_dir = join_path(THIRD_PARTY, 'distfiles', name)
        distfile = info['distfile'] % {'name': name, 'version': version}

        distfile_location = info['distfile_location'] % (
            {'name': name, 'version': version}
            )

        os.chdir(dest_dir)

        if distfile and distfile.endswith('.tar.bz2'):

            try:
                tar = tarfile.open(distfile, 'r:bz2')
            except:
                download_distfile(distfile, distfile_location)
                tar = tarfile.open(distfile, 'r:bz2')
                    
            print_message("Unpacking %s" % distfile, PROGRESS)
            tar.extractall()
            tar.close()
            os.chdir(name)

        elif distfile:
            download_distfile(distfile, distfile_location)

        env = os.environ.copy()
        if info['env']:
            env.update(info['env'])

        commands = info['commands']

        if isinstance(commands, basestring):
            commands = [commands]
        elif callable(commands):
            try:
                commands = commands(info)
            except Exception:
                print_message(
                    "Error calling build command for %s %s" %
                    (name, version), ERROR
                    )
                traceback.print_exc()
                sys.exit(1)

        if not isinstance(commands, (tuple,list)):
            print_message(
                "Invalid build commands for %s %s: %r" %
                (name, version, commands), ERROR
                )
            sys.exit(1)

        for command in commands:
            print_message("Running: %s" % command, PROGRESS)
            proc = Popen(command, shell=True, env=env)
            status = proc.wait()
            if status:
                print_message("Error running: %s" % command, ERROR)
                sys.exit(1)

        print_message("Successfully Installed %s %s" % (name, version), SUCCESS)

        updated_local_filelisting = gather_local_filelisting()
        receipt_data = updated_local_filelisting.difference(local_filelisting)
        local_filelisting = updated_local_filelisting

        receipt = open(
            join_path(PLEXNET_INSTALLED, '%s-%s' % (name, version)), 'wb'
            )
        receipt.write('\n'.join(receipt_data))
        receipt.close()

        os.chdir(dest_dir)

        if distfile.endswith('.tar.bz2'):
            # RemoveDirectory(name)
            rmtree(join_path(dest_dir, name))

        if info['after_install']:
            info['after_install']()

    return altered

def setup_role(role):
    """Setup the installation requirements for the given ``role``."""

    try:
        role_info_file = open(join_path(ROLES_DIRECTORY, '%s.role' % role), 'rb')
    except IOError, error:
        print_message("%s: %s" % (error[1], error.filename), ERROR)
        sys.exit(1)

    for package in map(str.strip, role_info_file.readlines()):
        if (not package) or package.startswith('#'):
            continue
        install_package(package)
    role_info_file.close()

# ------------------------------------------------------------------------------
# install or update the "base" redpill installation if need be...
# ------------------------------------------------------------------------------

setup_role('base')

if FIRST_RUN:
    install_packages()
    sys.exit(1)

# ------------------------------------------------------------------------------
# init
# ------------------------------------------------------------------------------

# @/@ currently only tested for OS X 10.5 -- most packages are from MacPorts

if get_flag('init'):

    roles = sys.argv[1:] or ['default']

    for role in roles:
        setup_role(role)

    install_packages()

    # libxml2, libiconv, libexpat | curl, ncurses

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
        dest_mtime = get_mtime(name.replace('.', '/') + LIB_EXTENSION)
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
        RemoveDirectory(join_path(PYTHON_SITE_PACKAGES, 'build'))

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

        RemoveDirectory(join_path(PKG_DIRECTORY, 'build'))

    sys.argv = original_argv

# ------------------------------------------------------------------------------
# @/@ these need to be implemented
# ------------------------------------------------------------------------------

if get_flag('update'):
    pass

if get_flag('startupfiles'): # @/@ generate startup tarballs/zipfiles
    pass

# ------------------------------------------------------------------------------
# env info
# ------------------------------------------------------------------------------

if not os.environ.get('PLEXNET_INSTALLED', ''):
    if os.name == 'posix':
        print
        print_message(
            "Add the following %i lines to %s !!"
            % (len(BASH_MESSAGE.splitlines()),
               join_path(HOME, '.bash_profile')
               ), INSTRUCTION
            )
        print BASH_MESSAGE

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
    if exists(join_path(CURRENT_DIRECTORY, 'SConstruct')):
        import SCons.Script
        SCons.Script.main()
        sys.exit()

print __doc__ % locals()
