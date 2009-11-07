import py
from pypy.jit.metainterp.policy import StopAtXPolicy
from pypy.jit.metainterp.test.test_basic import LLJitMixin, OOJitMixin
from pypy.rlib.jit import JitDriver, OPTIMIZER_SIMPLE

class ListTests:

    def test_basic_list(self):
        py.test.skip("not yet")
        myjitdriver = JitDriver(greens = [], reds = ['n', 'lst'])
        def f(n):
            lst = []
            while n > 0:
                myjitdriver.can_enter_jit(n=n, lst=lst)
                myjitdriver.jit_merge_point(n=n, lst=lst)
                lst.append(n)
                n -= len(lst)
            return len(lst)
        res = self.meta_interp(f, [42], listops=True)
        assert res == 9

    def test_list_operations(self):
        class FooBar:
            def __init__(self, z):
                self.z = z
        def f(n):
            lst = [41, 42]
            lst[0] = len(lst)     # [2, 42]
            lst.append(lst[1])    # [2, 42, 42]
            m = lst.pop()         # 42
            m += lst.pop(0)       # 44
            lst2 = [FooBar(3)]
            lst2.append(FooBar(5))
            m += lst2.pop().z     # 49
            return m
        res = self.interp_operations(f, [11], listops=True)
        assert res == 49
        self.check_history_(call=5)

    def test_list_of_voids(self):
        myjitdriver = JitDriver(greens = [], reds = ['n', 'lst'])
        def f(n):
            lst = [None]
            while n > 0:
                myjitdriver.can_enter_jit(n=n, lst=lst)
                myjitdriver.jit_merge_point(n=n, lst=lst)
                lst = [None, None]
                n -= 1
            return len(lst)
        res = self.meta_interp(f, [21], listops=True)
        assert res == 2

    def test_make_list(self):
        from pypy.jit.metainterp import simple_optimize
        myjitdriver = JitDriver(greens = [], reds = ['n', 'lst'])
        def f(n):
            lst = None
            while n > 0:
                lst = [0] * 10
                myjitdriver.can_enter_jit(n=n, lst=lst)
                myjitdriver.jit_merge_point(n=n, lst=lst)
                n -= 1
            return lst[n]
        res = self.meta_interp(f, [21], listops=True, optimizer=OPTIMIZER_SIMPLE)
        assert res == 0

    def test_getitem(self):
        myjitdriver = JitDriver(greens = [], reds = ['n', 'lst', 'i'])
        def f(n):
            lst = []
            for i in range(n):
                lst.append(i)
            i = 0
            while n > 0:
                myjitdriver.can_enter_jit(n=n, lst=lst, i=i)
                myjitdriver.jit_merge_point(n=n, lst=lst, i=i)
                n -= lst[i]
                i += 1
            return lst[i]
        res = self.meta_interp(f, [21], listops=True)
        assert res == f(21)
        self.check_loops(call=0)

    def test_getitem_neg(self):
        def f(n):
            lst = [41]
            lst.append(42)
            return lst[n]
        res = self.interp_operations(f, [-2], listops=True)
        assert res == 41
        self.check_history_(call=1)

# we don't support resizable lists on ootype
#class TestOOtype(ListTests, OOJitMixin):
#    pass

class TestLLtype(ListTests, LLJitMixin):
    pass