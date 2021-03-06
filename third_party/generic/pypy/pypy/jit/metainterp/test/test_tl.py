import py
from pypy.rlib.jit import JitDriver, OPTIMIZER_SIMPLE
from pypy.jit.metainterp.policy import StopAtXPolicy
from pypy.jit.metainterp.test.test_basic import OOJitMixin, LLJitMixin


class ToyLanguageTests:

    def test_tlr(self):
        from pypy.jit.tl.tlr import interpret, SQUARE

        codes = ["", SQUARE]
        def main(n, a):
            code = codes[n]
            return interpret(code, a)

        res = self.meta_interp(main, [1, 10])
        assert res == 100

    def _get_main(self):
        from pypy.jit.tl.tl import interp_without_call
        from pypy.jit.tl.tlopcode import compile

        code = compile('''
                PUSH 1   #  accumulator
                PUSH 7   #  N

            start:
                PICK 0
                PUSH 1
                LE
                BR_COND exit

                SWAP
                PICK 1
                MUL
                SWAP
                PUSH 1
                SUB
                PUSH 1
                BR_COND start

            exit:
                POP
                RETURN
        ''')

        code2 = compile('''
                PUSHARG
            start:
                PUSH 1
                SUB
                PICK 0
                PUSH 1
                LE
                BR_COND exit
                PUSH 1
                BR_COND start
            exit:
                RETURN
        ''')
        
        codes = [code, code2]
        def main(n, inputarg):
            code = codes[n]
            return interp_without_call(code, inputarg=inputarg)
        return main

    def test_tl_base(self):
        # 'backendopt=True' is used on lltype to kill unneeded access
        # to the class, which generates spurious 'guard_class'
        main = self._get_main()
        res = self.meta_interp(main, [0, 6], listops=True,
                               backendopt=True)
        assert res == 5040
        self.check_loops({'int_mul':1, 'jump':1,
                          'int_sub':1, 'int_is_true':1, 'int_le':1,
                          'guard_false':1})

    def test_tl_2(self):
        main = self._get_main()
        res = self.meta_interp(main, [1, 10], listops=True,
                               backendopt=True)
        assert res == main(1, 10)
        self.check_loops({'int_sub':1, 'int_le':1,
                         'int_is_true':1, 'guard_false':1, 'jump':1})

    def test_tl_call(self, listops=True, policy=None):
        from pypy.jit.tl.tl import interp
        from pypy.jit.tl.tlopcode import compile
        from pypy.jit.metainterp import simple_optimize

        code = compile('''
              PUSHARG
          start:
              PUSH 1
              SUB
              PICK 0
              PUSH 0
              CALL func
              POP
              GT
              BR_COND start
          exit:
              RETURN
          func:
              PUSH 0
          inside:
              PUSH 1
              ADD
              PICK 0
              PUSH 5
              LE
              BR_COND inside
              PUSH 1
              RETURN
              ''')
        assert interp(code, inputarg=100) == 0
        codes = [code, '']
        def main(num, arg):
            return interp(codes[num], inputarg=arg)
        
        res = self.meta_interp(main, [0, 20], optimizer=OPTIMIZER_SIMPLE,
                               listops=listops, backendopt=True, policy=policy)
        assert res == 0

    def test_tl_call_full_of_residuals(self):
        # This forces most methods of Stack to be ignored and treated as
        # residual calls.  It tests that the right thing occurs in this
        # case too.
        from pypy.jit.tl.tl import Stack
        methods = [Stack.put,
                   Stack.pick,
                   Stack.roll,
                   Stack.append,
                   Stack.pop]
        for meth in methods:
            meth_func = meth.im_func
            assert not hasattr(meth_func, '_jit_look_inside_')
            meth_func._jit_look_inside_ = False
        try:
            self.test_tl_call(listops=False)
        finally:
            for meth in methods:
                meth_func = meth.im_func
                del meth_func._jit_look_inside_

class TestOOtype(ToyLanguageTests, OOJitMixin):
    pass

class TestLLtype(ToyLanguageTests, LLJitMixin):
    pass
