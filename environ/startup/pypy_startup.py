
def patch_unicodedb():
    from pypy.module.unicodedata import unicodedb_4_1_0
    from pypy.module.unicodedata.interp_ucd import UCD, methods, \
         unichr_to_code_w
    from pypy.interpreter.gateway import W_Root, ObjSpace, NoneNotWrapped
    from unicodedb import _casefold
    from pypy.interpreter.typedef import TypeDef, interp_attrproperty
    from pypy.interpreter.gateway import  interp2app

    def casefold(code):
        try:
            return _casefold[code]
        except KeyError:
            return [code]

    unicodedb_4_1_0.casefold = casefold

    # patch the app-level, so it's exposed
    def interp_casefold(self, space, w_unichr):
        code = unichr_to_code_w(space, w_unichr)
        return space.newlist([space.wrap(c) for c in casefold(code)])
    unwrap_spec = ['self', ObjSpace, W_Root]
    
    UCD.casefold = interp_casefold
    methods['casefold'] = interp2app(UCD.casefold, unwrap_spec=unwrap_spec)
    UCD.typedef = TypeDef("unicodedata.UCD",
                          __doc__ = "",
                          unidata_version = interp_attrproperty('version', UCD),
                          **methods)

def patch():
    patch_unicodedb()
