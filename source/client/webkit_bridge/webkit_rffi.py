
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
from pypy.rpython.tool import rffi_platform as platform

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

JSContextRef           = rffi.VOIDP
JSStringRef            = rffi.VOIDP
JSObjectRef            = rffi.VOIDP
JSPropertyNameArrayRef = rffi.VOIDP
JSValueRef             = rffi.VOIDP
# a simple pointer
JSValueRefP = rffi.CArrayPtr(JSValueRef)

class Configure:
    _compilation_info_ = eci
    
    JSType           = platform.SimpleType('JSType', rffi.INT)
    kJSTypeUndefined = platform.ConstantInteger('kJSTypeUndefined')
    kJSTypeNull      = platform.ConstantInteger('kJSTypeNull')
    kJSTypeBoolean   = platform.ConstantInteger('kJSTypeBoolean')
    kJSTypeNumber    = platform.ConstantInteger('kJSTypeNumber')
    kJSTypeString    = platform.ConstantInteger('kJSTypeString')
    kJSTypeObject    = platform.ConstantInteger('kJSTypeObject')

globals().update(platform.configure(Configure))

NULL = lltype.nullptr(rffi.VOIDP.TO)

# ------------------------------ globals ------------------------------

_JSEvaluateScript = external('JSEvaluateScript',
   [JSContextRef, JSStringRef, JSObjectRef, JSStringRef, rffi.INT, JSValueRefP],
                            JSValueRef)
# args are: context, script, this (can be NULL),
# sourceURL (can be NULL, for exceptions), startingLineNumber,
# exception pointer (can be NULL)

class JSException(Exception):
    pass

def _can_raise_wrapper(name, llf, exc_class=JSException):
    def f(*a):
        exc_data = lltype.malloc(JSValueRefP.TO, 1, flavor='raw')
        res = llf(*a + (exc_data,))
        if not res:
            exc = exc_data[0]
            lltype.free(exc_data, flavor='raw')
            raise exc_class(exc)
        lltype.free(exc_data, flavor='raw')
        return res
    f.func_name = name
    return f

def JSEvaluateScript(ctx, source, this):
    exc_data = lltype.malloc(JSValueRefP.TO, 1, flavor='raw')
    sourceref = JSStringCreateWithUTF8CString(source)
    res = _JSEvaluateScript(ctx, sourceref, this, NULL, 0, exc_data)
    if res:
        lltype.free(exc_data, flavor='raw')
        return res
    exc = exc_data[0]
    lltype.free(exc_data, flavor='raw')
    raise JSException(exc)
                                                 
JSGarbageCollect = external('JSGarbageCollect', [JSContextRef], lltype.Void)

# ------------------------------ context ------------------------------

JSGlobalContextRelease = external('JSGlobalContextRelease', [JSContextRef],
                                  lltype.Void)

_JSGlobalContextCreate = external('JSGlobalContextCreate', [rffi.VOIDP],
                                 JSContextRef)
def JSGlobalContextCreate():
    return _JSGlobalContextCreate(lltype.nullptr(rffi.VOIDP.TO))

# ------------------------------ strings ------------------------------

JSStringCreateWithUTF8CString = external('JSStringCreateWithUTF8CString',
                                         [rffi.CCHARP], JSStringRef)
JSStringGetLength = external('JSStringGetLength', [JSStringRef], rffi.INT)

# ------------------------------ values -------------------------------

JSValueMakeString = external('JSValueMakeString', [JSContextRef, JSStringRef],
                             JSValueRef)
JSValueMakeNumber = external('JSValueMakeNumber', [JSContextRef, rffi.DOUBLE],
                             JSValueRef)
JSValueGetType = external('JSValueGetType', [JSContextRef, JSValueRef],
                          JSType)

# ------------------------------ objects ------------------------------

JSObjectCopyPropertyNames = external('JSObjectCopyPropertyNames',
                                     [JSContextRef, JSObjectRef],
                                     JSPropertyNameArrayRef)
JSPropertyNameArrayGetNameAtIndex = external(
    'JSPropertyNameArrayGetNameAtIndex',
    [JSPropertyNameArrayRef, rffi.INT],
    JSStringRef)

# ------------------------------ numbers ------------------------------

_JSValueToNumber = external('JSValueToNumber', [JSContextRef, JSValueRef,
                                                JSValueRefP], rffi.DOUBLE)

JSValueToNumber = _can_raise_wrapper('JSValueToNumber', _JSValueToNumber)
