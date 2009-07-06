
from pypy.interpreter.baseobjspace import Wrappable, W_Root, ObjSpace
from pypy.interpreter.gateway import interp2app
from pypy.interpreter.typedef import TypeDef
from webkit_bridge.webkit_rffi import *

def wrap_js_object(space, js_ctx, js_obj):
    tp = JSValueGetType(js_ctx, js_obj)
    if tp == kJSTypeUndefined:
        return space.wrap(None)
    elif tp == kJSTypeNumber:
        return space.wrap(JSValueToNumber(js_ctx, js_obj))
    else:
        raise NotImplementedError(tp)

def unwrap_to_js_object(space, js_ctx, w_obj):
    if space.is_true(space.isinstance(w_obj, space.w_int)):
        return JSValueMakeNumber(js_ctx, space.int_w(w_obj))
    else:
        raise NotImplementedError()

class JSObject(Wrappable):
    def __init__(self, js_ctx, js_val):
        self.js_ctx = js_ctx
        self.js_val = js_val

    def descr_get(self, space, w_name):
        js_name = JSStringCreateWithUTF8CString(space.str_w(w_name))
        return wrap_js_object(space, self.js_ctx,
                              JSObjectGetProperty(self.js_ctx, self.js_val,
                                                  js_name))

    def descr_set(self, space, w_name, w_value):
        js_val = unwrap_to_js_object(space, self.js_ctx, w_value)
        js_name = JSStringCreateWithUTF8CString(space.str_w(w_name))
        JSObjectSetProperty(self.js_ctx, self.js_val, js_name, js_val, 0)
        return space.w_None

JSObject.typedef = TypeDef("JSObject",
        __getattribute__ = interp2app(JSObject.descr_get,
                                      unwrap_spec=['self', ObjSpace, W_Root]),
        __getitem__ = interp2app(JSObject.descr_get,
                                 unwrap_spec=['self', ObjSpace, W_Root]),
        __setitem__ = interp2app(JSObject.descr_set,
                              unwrap_spec=['self', ObjSpace, W_Root, W_Root]),
        __setattr__ = interp2app(JSObject.descr_set,
                              unwrap_spec=['self', ObjSpace, W_Root, W_Root]),
)
