
from pypy.interpreter.baseobjspace import Wrappable, W_Root, ObjSpace
from pypy.interpreter.gateway import interp2app
from pypy.interpreter.typedef import TypeDef
from webkit_bridge.webkit_rffi import *

class JavaScriptContext(object):
    def __init__(self, space, _ctx):
        self._ctx = _ctx
        self.space = space

    def python_to_js(self, w_obj):
        space = self.space
        if space.is_w(w_obj, space.w_None):
            return JSValueMakeUndefined(self._ctx)
        elif space.is_true(space.isinstance(w_obj, space.w_bool)):
            return JSValueMakeBoolean(self._ctx, space.is_true(w_obj))
        elif space.is_true(space.isinstance(w_obj, space.w_int)):
            return JSValueMakeNumber(self._ctx, space.int_w(w_obj))
        elif space.is_true(space.isinstance(w_obj, space.w_float)):
            return JSValueMakeNumber(self._ctx, space.float_w(w_obj))
        elif space.is_true(space.isinstance(w_obj, space.w_str)):
            return JSValueMakeString(self._ctx, self.newstr(space.str_w(w_obj)))
        elif isinstance(w_obj, JSObject):
            return w_obj.js_val
        else:
            raise NotImplementedError()

    def js_to_python(self, js_obj):
        space = self.space
        tp = JSValueGetType(self._ctx, js_obj)
        if tp == kJSTypeUndefined:
            return space.w_None
        elif tp == kJSTypeNull:
            return space.w_None
        elif tp == kJSTypeBoolean:
            return space.wrap(JSValueToBoolean(self._ctx, js_obj))
        elif tp == kJSTypeNumber:
            return space.wrap(JSValueToNumber(self._ctx, js_obj))
        elif tp == kJSTypeString:
            return space.wrap(self.str_js(js_obj))
        elif tp == kJSTypeObject:
            return space.wrap(JSObject(self, js_obj))
        else:
            raise NotImplementedError(tp)

    def newstr(self, s):
        return JSStringCreateWithUTF8CString(s)

    def str_js(self, js_s):
        return JSStringGetUTF8CString(JSValueToString(self._ctx, js_s))

    def get(self, js_obj, name):
        return JSObjectGetProperty(self._ctx, js_obj, self.newstr(name))

    def set(self, js_obj, name, js_val):
        js_name = JSStringCreateWithUTF8CString(name)
        JSObjectSetProperty(self._ctx, js_obj, js_name, js_val, 0)

    def eval(self, s, this=NULL):
        return JSEvaluateScript(self._ctx, s, this)

    def call(self, js_val, args, this=NULL):
        return JSObjectCallAsFunction(self._ctx, js_val, this, args)

class JSObject(Wrappable):
    def __init__(self, ctx, js_val):
        self.ctx = ctx
        self.js_val = js_val

    def descr_get(self, space, w_name):
        js_val = self.ctx.get(self.js_val, space.str_w(w_name))
        return self.ctx.js_to_python(js_val)

    def descr_set(self, space, w_name, w_value):
        js_val = self.ctx.python_to_js(w_value)
        self.ctx.set(self.js_val, space.str_w(w_name), js_val)
        return space.w_None

    def call(self, space, args_w):
        js_res = self.ctx.call(self.js_val, [self.ctx.python_to_js(arg)
                                             for arg in args_w])
        return self.ctx.js_to_python(js_res)

    def str(self, space):
        return space.wrap('JSObject(' + self.ctx.str_js(self.js_val) + ')')

JSObject.typedef = TypeDef("JSObject",
        __getattribute__ = interp2app(JSObject.descr_get,
                                      unwrap_spec=['self', ObjSpace, W_Root]),
        __getitem__ = interp2app(JSObject.descr_get,
                                 unwrap_spec=['self', ObjSpace, W_Root]),
        __setitem__ = interp2app(JSObject.descr_set,
                              unwrap_spec=['self', ObjSpace, W_Root, W_Root]),
        __setattr__ = interp2app(JSObject.descr_set,
                              unwrap_spec=['self', ObjSpace, W_Root, W_Root]),
        __str__ = interp2app(JSObject.str,
                             unwrap_spec=['self', ObjSpace]),
        __call__ = interp2app(JSObject.call,
                              unwrap_spec=['self', ObjSpace, 'args_w'])
)
