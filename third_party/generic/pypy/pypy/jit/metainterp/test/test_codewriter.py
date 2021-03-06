import py
from pypy.rlib import jit
from pypy.jit.metainterp import support, typesystem
from pypy.jit.metainterp.policy import JitPolicy
from pypy.jit.metainterp.codewriter import CodeWriter
from pypy.jit.metainterp.test.test_basic import LLJitMixin, OOJitMixin
from pypy.translator.translator import graphof
from pypy.rpython.lltypesystem.rbuiltin import ll_instantiate

def test_find_all_graphs():
    def f(x):
        if x < 0:
            return f(-x)
        return x + 1
    @jit.purefunction
    def g(x):
        return x + 2
    @jit.dont_look_inside
    def h(x):
        return x + 3
    def i(x):
        return f(x) * g(x) * h(x)

    rtyper = support.annotate(i, [7])
    cw = CodeWriter(rtyper)
    jitpolicy = JitPolicy()
    res = cw.find_all_graphs(rtyper.annotator.translator.graphs[0], None,
                             jitpolicy, True)
    translator = rtyper.annotator.translator

    funcs = set([graph.func for graph in res])
    assert funcs == set([i, f])

def test_find_all_graphs_without_floats():
    def g(x):
        return int(x * 12.5)
    def f(x):
        return g(x) + 1
    rtyper = support.annotate(f, [7])
    cw = CodeWriter(rtyper)
    jitpolicy = JitPolicy()
    translator = rtyper.annotator.translator
    res = cw.find_all_graphs(translator.graphs[0], None, jitpolicy,
                             supports_floats=True)
    funcs = set([graph.func for graph in res])
    assert funcs == set([f, g])

    cw = CodeWriter(rtyper)        
    res = cw.find_all_graphs(translator.graphs[0], None, jitpolicy,
                             supports_floats=False)
    funcs = [graph.func for graph in res]
    assert funcs == [f]

def test_find_all_graphs_loops():
    def g(x):
        i = 0
        while i < x:
            i += 1
        return i
    @jit.unroll_safe
    def h(x):
        i = 0
        while i < x:
            i += 1
        return i

    def f(x):
        i = 0
        while i < x*x:
            i += g(x) + h(x)
        return i

    rtyper = support.annotate(f, [7])
    cw = CodeWriter(rtyper)
    jitpolicy = JitPolicy()
    translator = rtyper.annotator.translator
    res = cw.find_all_graphs(translator.graphs[0], None, jitpolicy,
                             supports_floats=True)
    funcs = set([graph.func for graph in res])
    assert funcs == set([f, h])
    

def test_find_all_graphs_str_join():
    def i(x, y):
        return "hello".join([str(x), str(y), "bye"])

    rtyper = support.annotate(i, [7, 100])
    cw = CodeWriter(rtyper)
    jitpolicy = JitPolicy()
    translator = rtyper.annotator.translator
    # does not explode
    cw.find_all_graphs(translator.graphs[0], None, jitpolicy, True)

class SomeLabel(object):
    def __eq__(self, other):
        return repr(other).startswith('label')    # :-/


class TestCodeWriter:

    def make_graphs(self, func, values, type_system='lltype'):
        class FakeMetaInterpSd:
            virtualizable_info = None
            def find_opcode(self, name):
                default = len(self.opname_to_index)
                return self.opname_to_index.setdefault(name, default)
            def _register_indirect_call_target(self, fnaddress, jitcode):
                self.indirectcalls.append((fnaddress, jitcode))

        class FakeMethDescr:
            def __init__(self1, CLASS, methname):
                self.methdescrs.append(self1)
                self1.CLASS = CLASS
                self1.methname = methname
                self1.jitcodes = None
            def setup(self1, jitcodes):
                self1.jitcodes = jitcodes
        self.methdescrs = []

        class FakeCPU:
            supports_floats = False
            def fielddescrof(self, STRUCT, fieldname):
                return ('fielddescr', STRUCT, fieldname)
            def calldescrof(self, FUNC, NON_VOID_ARGS, RESULT):
                return ('calldescr', FUNC, NON_VOID_ARGS, RESULT)
            def typedescrof(self, CLASS):
                return ('typedescr', CLASS)
            def methdescrof(self, CLASS, methname):
                return FakeMethDescr(CLASS, methname)

        if type_system == 'lltype':
            FakeCPU.ts = typesystem.llhelper
        else:
            FakeCPU.ts = typesystem.oohelper

        self.metainterp_sd = FakeMetaInterpSd()
        self.metainterp_sd.opcode_implementations = None
        self.metainterp_sd.opname_to_index = {}
        self.metainterp_sd.indirectcalls = []
        self.metainterp_sd.cpu = FakeCPU()

        self.rtyper = support.annotate(func, values, type_system=type_system)
        self.metainterp_sd.cpu.rtyper = self.rtyper
        return self.rtyper.annotator.translator.graphs

    def graphof(self, func):
        rtyper = self.metainterp_sd.cpu.rtyper
        return graphof(rtyper.annotator.translator, func)

    def test_basic(self):
        def f(n):
            return n + 10
        graphs = self.make_graphs(f, [5])
        cw = CodeWriter(self.rtyper)
        cw.candidate_graphs = graphs
        cw._start(self.metainterp_sd, None)
        jitcode = cw.make_one_bytecode((graphs[0], None), False)
        assert jitcode._source == [
            SomeLabel(),
            'int_add', 0, 1, '# => r1',
            'make_new_vars_1', 2,
            'return']

    def test_guess_call_kind_and_calls_from_graphs(self):
        from pypy.objspace.flow.model import SpaceOperation, Constant, Variable

        portal_runner_ptr = object()
        g = object()
        g1 = object()
        cw = CodeWriter(None)
        cw.candidate_graphs = [g, g1]
        cw.portal_runner_ptr = portal_runner_ptr

        op = SpaceOperation('direct_call', [Constant(portal_runner_ptr)],
                            Variable())
        assert cw.guess_call_kind(op) == 'recursive'

        op = SpaceOperation('direct_call', [Constant(object())],
                            Variable())
        assert cw.guess_call_kind(op) == 'residual'        

        class funcptr:
            class graph:
                class func:
                    oopspec = "spec"
        op = SpaceOperation('direct_call', [Constant(funcptr)],
                            Variable())
        assert cw.guess_call_kind(op) == 'builtin'
        
        class funcptr:
            graph = g
        op = SpaceOperation('direct_call', [Constant(funcptr)],
                            Variable())
        res = cw.graphs_from(op)
        assert res == [g]        
        assert cw.guess_call_kind(op) == 'regular'

        class funcptr:
            graph = object()
        op = SpaceOperation('direct_call', [Constant(funcptr)],
                            Variable())
        res = cw.graphs_from(op)
        assert res is None        
        assert cw.guess_call_kind(op) == 'residual'

        h = object()
        op = SpaceOperation('indirect_call', [Variable(),
                                              Constant([g, g1, h])],
                            Variable())
        res = cw.graphs_from(op)
        assert res == [g, g1]
        assert cw.guess_call_kind(op) == 'regular'

        op = SpaceOperation('indirect_call', [Variable(),
                                              Constant([h])],
                            Variable())
        res = cw.graphs_from(op)
        assert res is None
        assert cw.guess_call_kind(op) == 'residual'        
        
    def test_direct_call(self):
        def g(m):
            return 123
        def f(n):
            return g(n+1)
        graphs = self.make_graphs(f, [5])
        cw = CodeWriter(self.rtyper)
        cw.candidate_graphs = graphs
        cw._start(self.metainterp_sd, None)
        jitcode = cw.make_one_bytecode((graphs[0], None), False)
        assert len(cw.all_graphs) == 2        

    def test_indirect_call_target(self):
        def g(m):
            return 123
        def h(m):
            return 456
        def f(n):
            if n > 3:
                call = g
            else:
                call = h
            return call(n+1) + call(n+2)
        graphs = self.make_graphs(f, [5])
        cw = CodeWriter(self.rtyper)
        cw.candidate_graphs = graphs
        cw._start(self.metainterp_sd, None)        
        jitcode = cw.make_one_bytecode((graphs[0], None), False)
        assert len(self.metainterp_sd.indirectcalls) == 2
        names = [jitcode.name for (fnaddress, jitcode)
                               in self.metainterp_sd.indirectcalls]
        assert dict.fromkeys(names) == {'g': None, 'h': None}

    def test_indirect_look_inside_only_one(self):
        def g(m):
            return 123
        @jit.dont_look_inside
        def h(m):
            return 456
        def f(n):
            if n > 3:
                call = g
            else:
                call = h
            return call(n+1) + call(n+2)
        graphs = self.make_graphs(f, [5])
        graphs = [g for g in graphs if getattr(g.func, '_jit_look_inside_',
                                               True)]
        cw = CodeWriter(self.rtyper)
        cw.candidate_graphs = graphs
        cw._start(self.metainterp_sd, None)        
        jitcode = cw.make_one_bytecode((graphs[0], None), False)
        assert len(self.metainterp_sd.indirectcalls) == 1
        names = [jitcode.name for (fnaddress, jitcode)
                               in self.metainterp_sd.indirectcalls]
        assert dict.fromkeys(names) == {'g': None}

    def test_oosend_look_inside_only_one(self):
        class A:
            pass
        class B(A):
            def g(self):
                return 123
        class C(A):
            @jit.dont_look_inside
            def g(self):
                return 456
        def f(n):
            if n > 3:
                x = B()
            else:
                x = C()
            return x.g() + x.g()
        graphs = self.make_graphs(f, [5], type_system='ootype')
        graphs = [g for g in graphs if getattr(g.func, '_jit_look_inside_',
                                               True)]
        cw = CodeWriter(self.rtyper)
        cw.candidate_graphs = graphs
        cw._start(self.metainterp_sd, None)        
        jitcode = cw.make_one_bytecode((graphs[0], None), False)
        assert len(self.methdescrs) == 1
        assert self.methdescrs[0].CLASS._name.endswith('.A')
        assert self.methdescrs[0].methname == 'og'
        assert len(self.methdescrs[0].jitcodes.keys()) == 2
        values = self.methdescrs[0].jitcodes.values()
        values.sort()
        assert values[0] is None
        assert values[1].name == 'B.g'
        for graph, _ in cw.all_graphs.keys():
            assert graph.name in ['f', 'B.g']

    def test_instantiate(self):
        class A1:     id = 651
        class A2(A1): id = 652
        class B1:     id = 661
        class B2(B1): id = 662
        def f(n):
            if n > 5:
                x, y = A1, B1
            else:
                x, y = A2, B2
            n += 1
            return x().id + y().id + n
        graphs = self.make_graphs(f, [5])
        cw = CodeWriter(self.rtyper)
        cw.candidate_graphs = graphs
        cw._start(self.metainterp_sd, None)        
        cw.make_one_bytecode((graphs[0], None), False)
        graph2 = self.graphof(ll_instantiate)
        jitcode = cw.make_one_bytecode((graph2, None), False)
        assert 'residual_call' not in jitcode._source
        names = [jitcode.name for (fnaddress, jitcode)
                               in self.metainterp_sd.indirectcalls]
        names = dict.fromkeys(names)
        assert len(names) >= 4
        for expected in ['A1', 'A2', 'B1', 'B2']:
            for name in names:
                if name.startswith('instantiate_') and name.endswith(expected):
                    break
            else:
                assert 0, "missing instantiate_*_%s in:\n%r" % (expected,
                                                                names)


class ImmutableFieldsTests:

    def test_fields(self):
        class X(object):
            _immutable_fields_ = ["x"]

            def __init__(self, x):
                self.x = x

        def f(x):
            y = X(x)
            return y.x + 5
        res = self.interp_operations(f, [23])
        assert res == 28
        self.check_history_(getfield_gc=0, getfield_gc_pure=1, int_add=1)

    def test_array(self):
        class X(object):
            _immutable_fields_ = ["y[*]"]

            def __init__(self, x):
                self.y = x
        def f(index):
            l = [1, 2, 3, 4]
            l[2] = 30
            a = X(l)
            return a.y[index]
        res = self.interp_operations(f, [2], listops=True)
        assert res == 30
        self.check_history_(getfield_gc=0, getfield_gc_pure=1,
                            getarrayitem_gc=0, getarrayitem_gc_pure=1)


    def test_array_in_immutable(self):
        class X(object):
            _immutable_ = True
            _immutable_fields_ = ["lst[*]"]

            def __init__(self, lst, y):
                self.lst = lst
                self.y = y

        def f(x, index):
            y = X([x], x+1)
            return y.lst[index] + y.y + 5
        res = self.interp_operations(f, [23, 0], listops=True)
        assert res == 23 + 24 + 5
        self.check_history_(getfield_gc=0, getfield_gc_pure=2,
                            getarrayitem_gc=0, getarrayitem_gc_pure=1,
                            int_add=3)


class TestLLtypeImmutableFieldsTests(ImmutableFieldsTests, LLJitMixin):
    pass

class TestOOtypeImmutableFieldsTests(ImmutableFieldsTests, OOJitMixin):
   pass
