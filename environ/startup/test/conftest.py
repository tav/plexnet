
import pypypath
import pypy_startup
pypy_startup.patch()

# make sure we import pypy's test infrastructure
from pypy.conftest import Directory, Module, option, ConftestPlugin

