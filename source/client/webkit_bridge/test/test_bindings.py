
from webkit_bridge.webkit_rffi import *

class TestBasic(object):
    def setup_method(cls, meth):
        cls.context = JSGlobalContextCreate()

    def teardown_method(cls, meth):
        JSGlobalContextRelease(cls.context)

    def test_string(self):
        s = JSStringCreateWithUTF8CString('xyz')
        assert JSStringGetLength(s) == 3
        vs = JSValueMakeString(self.context, s)
        assert JSValueGetType(self.context, vs) == kJSTypeString

    def test_interpret(self):
        pass
        
        
