
from webkit_bridge.webkit_rffi import *

class TestBasic(object):
    def test_context_create(self):
        context = JSGlobalContextCreate()
        JSGarbageCollect(context)
        JSGlobalContextRelease(context)
