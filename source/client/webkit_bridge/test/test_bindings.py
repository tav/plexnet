
from webkit_bridge.webkit_rffi import *
from pypy.rpython.lltypesystem import lltype, rffi

class TestBasic(object):
    def setup_method(cls, meth):
        cls.context = JSGlobalContextCreate()

    #def teardown_method(cls, meth):
    #    JSGlobalContextRelease(cls.context)

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

    def test_get_set(self):
        script = '[]'
        obj = JSEvaluateScript(self.context, script, NULL)
        assert JSValueGetType(self.context, obj) == kJSTypeObject
        prop = JSStringCreateWithUTF8CString('prop')
        el = JSObjectGetProperty(self.context, obj, prop)
        assert JSValueGetType(self.context, el) == kJSTypeUndefined
        v = JSValueMakeNumber(self.context, 3)
        JSObjectSetProperty(self.context, obj, prop, v, 0)
        el = JSObjectGetProperty(self.context, obj, prop)
        assert JSValueGetType(self.context, el) == kJSTypeNumber

    def test_str(self):
        script = '[1,2,     3]'
        obj = JSEvaluateScript(self.context, script, NULL)
        s = JSValueToString(self.context, obj)
        assert JSStringGetUTF8CString(s) == '1,2,3'

    def test_function(self):
        script = 'this.x = function (a, b) { return (a + b); }'
        this = JSEvaluateScript(self.context, '[]', NULL)
        obj = JSEvaluateScript(self.context, script, this)
        name = JSStringCreateWithUTF8CString('x')
        f = JSObjectGetProperty(self.context, this, name)
        assert JSValueGetType(self.context, f) == kJSTypeObject
        args = [JSValueMakeNumber(self.context, 40),
                JSValueMakeNumber(self.context, 2)]
        res = JSObjectCallAsFunction(self.context, f, this, args)
        assert JSValueGetType(self.context, res) == kJSTypeNumber
        assert JSValueToNumber(self.context, res) == 42

