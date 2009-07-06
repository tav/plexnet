
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

    def test_number(self):
        v = JSValueMakeNumber(self.context, 3.0)
        assert JSValueToNumber(self.context, v) == 3.0

    def test_interpret(self):
        script = '3'
        res = JSEvaluateScript(self.context, script, NULL)
        assert JSValueGetType(self.context, res) == kJSTypeNumber
        assert JSValueToNumber(self.context, res) == 3.0

    def test_interpret_object(self):
        script = '[1, 2, 3]'
        res = JSEvaluateScript(self.context, script, NULL)
        assert JSValueGetType(self.context, res) == kJSTypeObject
        s0 = JSStringCreateWithUTF8CString('0')
        fe = JSObjectGetProperty(self.context, res, s0)
        assert JSValueGetType(self.context, fe) == kJSTypeNumber
        assert JSValueToNumber(self.context, fe) == 1.0
