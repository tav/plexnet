
from pypy.conftest import gettestobjspace
from webkit_bridge.jsobj import JSObject
from webkit_bridge.webkit_rffi import (JSGlobalContextCreate,
                                       JSGlobalContextRelease,
                                       empty_object)

class AppTestBindings(object):
    def setup_class(cls):
        space = gettestobjspace()
        ctx = JSGlobalContextCreate()
        cls.w_js_obj = space.wrap(JSObject(ctx, empty_object(ctx)))
    
    def test_getsetattr_none(self):
        assert self.js_obj.x == None
