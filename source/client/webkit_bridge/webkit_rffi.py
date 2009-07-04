
""" Please create a symlink to webkit build called `webkit`.
It should contain a debug build and libJavaScriptCore.so. To create
libJavaScriptCore.so, go to WebKitBuild/Debug/.libs and perform:

ar x libJavaScriptCore.a
g++ -shared -o libJavaScriptCore.so *.o -lpthread -lglib-2.0 `icu-config --ldflags`

and make sure .so is on your LD_LIBRARY_PATH
"""

import py
from pypy.rpython.lltypesystem import lltype, rffi
from pypy.translator.tool.cbuild import ExternalCompilationInfo, log

class WebkitNotFound(Exception):
    pass

def error():
    print __doc__
    raise WebkitNotFound()

webkitdir = py.magic.autopath().dirpath().join('webkit')
if not webkitdir.check(dir=True):
    error()
libdir = webkitdir/'WebKitBuild'/'Debug'/'.libs'
if not libdir.join('libJavaScriptCore.so').check():
    error()
include_dirs = [webkitdir,
                webkitdir/'JavaScriptCore'/'ForwardingHeaders']

eci = ExternalCompilationInfo(
    libraries    = ['JavaScriptCore'],
    library_dirs = [libdir],
    include_dirs = include_dirs,
    includes     = ['JavaScriptCore/API/JSContextRef.h']
    )

def external(name, args, result, **kwds):
    return rffi.llexternal(name, args, result, compilation_info=eci, **kwds)

def copaqueptr(name):
    return rffi.COpaquePtr(name, compilation_info=eci)

JSContextRef = rffi.VOIDP

_JSGlobalContextCreate = external('JSGlobalContextCreate', [rffi.VOIDP],
                                 JSContextRef)
def JSGlobalContextCreate():
    return _JSGlobalContextCreate(lltype.nullptr(rffi.VOIDP.TO))

JSGlobalContextRelease = external('JSGlobalContextRelease', [JSContextRef],
                                  lltype.Void)
JSGarbageCollect = external('JSGarbageCollect', [JSContextRef], lltype.Void)
