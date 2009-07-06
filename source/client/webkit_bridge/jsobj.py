
from pypy.interpreter.baseobjspace import Wrappable, W_Root, ObjSpace
from pypy.interpreter.gateway import interp2app
from pypy.interpreter.typedef import TypeDef
from webkit_bridge.webkit_rffi import *

def wrap_js_object(space, js_ctx, js_obj):
    tp = JSValueGetType(js_ctx, js_obj)
    if tp == kJSTypeUndefined:
        return space.wrap(None)
    else:
        raise NotImplementedError(tp)

class JSObject(Wrappable):
    def __init__(self, js_ctx, js_val):
        self.js_ctx = js_ctx
        self.js_val = js_val

    def descr_getattribute(self, space, name):
        js_name = JSStringCreateWithUTF8CString(name)
        return wrap_js_object(space, self.js_ctx,
                              JSObjectGetProperty(self.js_ctx, self.js_val,
                                                  js_name))
                           

JSObject.typedef = TypeDef("JSObject",
        __getattribute__ = interp2app(JSObject.descr_getattribute,
                                      unwrap_spec=['self', ObjSpace, str]),

)
