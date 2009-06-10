
from pypy.module.unicodedata import unicodedb_4_1_0
from pypy.conftest import gettestobjspace

class TestUnicodedb:
    def test_casefold(self):
        assert unicodedb_4_1_0.casefold(0xdf) == [ord('s')] * 2

class AppTestUnicodedb:
    def setup_class(cls):
        cls.space = gettestobjspace(usemodules=('unicodedata',))
    
    def test_casefold(self):
        import unicodedata
        unicodedata.ucd.casefold(u'\xdf') == ['s', 's']
