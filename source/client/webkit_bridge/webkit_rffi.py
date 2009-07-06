
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
    _compilation_info_   = eci
    
    JSType               = platform.SimpleType('JSType', rffi.INT)
    JSPropertyAttributes = platform.SimpleType('JSPropertyAttributes', rffi.INT)
    c_bool = platform.SimpleType('bool', rffi.INT)

for name in [
    'kJSTypeUndefined', 'kJSTypeNull', 'kJSTypeBoolean', 'kJSTypeNumber',
    'kJSTypeString', 'kJSTypeObject', 'kJSPropertyAttributeNone',
    'kJSPropertyAttributeReadOnly', 'kJSPropertyAttributeDontEnum',
    'kJSPropertyAttributeDontDelete']:
    setattr(Configure, name, platform.ConstantInteger(name))

globals().update(platform.configure(Configure))

NULL = lltype.nullptr(rffi.VOIDP.TO)

# ------------------------------ globals ------------------------------

_JSEvaluateScript = external('JSEvaluateScript',
                             [JSContextRef, JSStringRef,
                              JSObjectRef, JSStringRef,
                              rffi.INT, JSValueRefP],
                             JSValueRef)
# args are: context, script, this (can be NULL),
# sourceURL (can be NULL, for exceptions), startingLineNumber,
# exception pointer (can be NULL)

class JSException(Exception):
    def __init__(self, context, jsexc):
        self.context = context
        self.jsexc   = jsexc

    def __str__(self):
        v = JSValueToString(self.context, self.jsexc)
        return JSStringGetUTF8CString(v)

def _can_raise_wrapper(name, args, res, exc_class=JSException):
    llf = external(name, args + [JSValueRefP], res)
    def f(context, *a):
        exc_data = lltype.malloc(JSValueRefP.TO, 1, flavor='raw', zero=True)
        res = llf(context, *a + (exc_data,))
        exc = exc_data[0]
        lltype.free(exc_data, flavor='raw')
        if exc:
            raise exc_class(context, exc)
        return res
    f.func_name = name
    return f

def JSEvaluateScript(ctx, source, this):
    exc_data = lltype.malloc(JSValueRefP.TO, 1, flavor='raw')
    sourceref = JSStringCreateWithUTF8CString(source)
    res = _JSEvaluateScript(ctx, sourceref, this, NULL, 0, exc_data)
    exc = exc_data[0]
    lltype.free(exc_data, flavor='raw')
    if exc:
        return res
    raise JSException(ctx, exc)

def empty_object(ctx):
    return JSEvaluateScript(ctx, '[]', NULL)
                                                 
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

_JSStringGetUTF8CString = external('JSStringGetUTF8CString',
                                   [JSStringRef, rffi.CCHARP, rffi.INT],
                                   rffi.INT)
_JSStringGetMaximumUTF8CStringSize = external(
    'JSStringGetMaximumUTF8CStringSize', [JSStringRef], rffi.INT)

def JSStringGetUTF8CString(s):
    # XXX horribly inefficient
    lgt = _JSStringGetMaximumUTF8CStringSize(s)
    buf = lltype.malloc(rffi.CCHARP.TO, lgt, flavor='raw')
    newlgt = _JSStringGetUTF8CString(s, buf, lgt)
    res = rffi.charp2strn(buf, newlgt)
    lltype.free(buf, flavor='raw')
    return res

# ------------------------------ values -------------------------------

JSValueMakeString = external('JSValueMakeString', [JSContextRef, JSStringRef],
                             JSValueRef)
JSValueMakeNumber = external('JSValueMakeNumber', [JSContextRef, rffi.DOUBLE],
                             JSValueRef)
JSValueMakeBoolean = external('JSValueMakeBoolean', [JSContextRef, c_bool],
                              JSValueRef)
JSValueToBoolean = external('JSValueToBoolean', [JSContextRef, JSValueRef],
                            c_bool)
JSValueMakeUndefined = external('JSValueMakeUndefined', [JSContextRef],
                                JSValueRef)
JSValueGetType = external('JSValueGetType', [JSContextRef, JSValueRef],
                          JSType)
JSValueProtect = external('JSValueProtect', [JSContextRef, JSValueRef],
                          lltype.Void)
JSValueUnprotect = external('JSValueUnprotect', [JSContextRef, JSValueRef],
                            lltype.Void)
JSValueToString = _can_raise_wrapper('JSValueToStringCopy',
                                     [JSContextRef, JSValueRef],
                                     JSStringRef)

# ------------------------------ objects ------------------------------

JSObjectCopyPropertyNames = external('JSObjectCopyPropertyNames',
                                     [JSContextRef, JSObjectRef],
                                     JSPropertyNameArrayRef)
JSPropertyNameArrayGetNameAtIndex = external(
    'JSPropertyNameArrayGetNameAtIndex',
    [JSPropertyNameArrayRef, rffi.INT],
    JSStringRef)

JSObjectHasProperty = external('JSObjectHasProperty',
                               [JSContextRef, JSObjectRef, JSStringRef],
                               lltype.Bool)
# context, object, property name

JSObjectGetProperty = _can_raise_wrapper('JSObjectGetProperty',
                                         [JSContextRef,
                                          JSObjectRef,
                                          JSStringRef],
                                         JSValueRef)

JSObjectSetProperty = _can_raise_wrapper('JSObjectSetProperty',
                                         [JSContextRef, JSObjectRef,
                                          JSStringRef, JSValueRef,
                                          JSPropertyAttributes],
                                         lltype.Void)

_JSObjectCallAsFunction = external('JSObjectCallAsFunction',
                                   [JSContextRef, JSObjectRef,
                                    JSObjectRef, rffi.INT,
                                    JSValueRefP], JSValueRef)

def JSObjectCallAsFunction(ctx, object, this, args):
    ll_args = lltype.malloc(JSValueRefP.TO, len(args), flavor='raw')
    exc_data = lltype.malloc(JSValueRefP.TO, 1, flavor='raw', zero=True)
    for i in range(len(args)):
        ll_args[i] = args[i]
    res = _JSObjectCallAsFunction(ctx, object, this, len(args), ll_args,
                                  exc_data)
    lltype.free(ll_args, flavor='raw')
    exc = exc_data[0]
    lltype.free(exc_data, flavor='raw')
    if exc:
        raise JSException(ctx, exc)
    return res

# ------------------------------ numbers ------------------------------

JSValueToNumber = _can_raise_wrapper('JSValueToNumber',
                                     [JSContextRef, JSValueRef],
                                     rffi.DOUBLE)
