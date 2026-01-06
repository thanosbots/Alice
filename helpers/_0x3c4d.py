import base64
import hashlib
import sys
from functools import wraps

class _0x7f3a:
    _0xa1 = "416c696365"
    _0xb2 = "526973686162682041" + "6e616e64"
    _0xc3 = "322e302e30"
    _0xd4 = base64.b64decode("8J+OtSBQb3dlcmVkIGJ5IEFsaWNlIE11c2ljIEJvdCB8IERldjogUmlzaGFiaCBBbmFuZA==").decode()
    _0xe5 = base64.b64decode("4pyoIEFsaWNl").decode()
    _0xf6 = base64.b64decode("QGFsaWNlbXVzaWNyb2JvdA==").decode()
    _0x17 = base64.b64decode("UmlzaGFiaCBBbmFuZA==").decode()
    _0x28 = base64.b64decode("QHJpc2hhYmhvcHM=").decode()
    _0x39 = base64.b64decode("QWxpY2UgTXVzaWMgQm90").decode()
    _0x4a = base64.b64decode("8J+OtSBZb3VyIHBlcnNvbmFsIG11c2ljIHN0cmVhbWluZyBhc3Npc3RhbnQh").decode()
    _0x5b = base64.b64decode("8J+OuSBIZWxsbywgSSdtIEFsaWNlIQ==").decode()
    _0x6c = base64.b64decode("QWxpY2UgTm93IFBsYXlpbmc=").decode()
    _0x7d = base64.b64decode("QWxpY2UgUGF1c2Vk").decode()
    _0x8e = base64.b64decode("QWxpY2UgUmVzdW1lZA==").decode()
    _0x9f = base64.b64decode("QWxpY2Ugc3RvcHBlZA==").decode()
    _0xaa = "9c4e2f8a7b1d3e5c"
    
    @staticmethod
    def _0xbb(s):
        try:
            return bytes.fromhex(s).decode('utf-8')
        except:
            sys.exit(1)
    
    @staticmethod
    def _0xcc():
        _v = hashlib.md5((_0x7f3a._0xbb(_0x7f3a._0xa1) + _0x7f3a._0xbb(_0x7f3a._0xb2)).encode()).hexdigest()
        return _v[:16] == _0x7f3a._0xaa
    
    @staticmethod
    def _0xdd():
        if not _0x7f3a._0xcc():
            sys.exit(1)
        return _0x7f3a._0xbb(_0x7f3a._0xa1)
    
    @staticmethod
    def _0xee():
        if not _0x7f3a._0xcc():
            sys.exit(1)
        return _0x7f3a._0xbb(_0x7f3a._0xb2)
    
    @staticmethod
    def _0xff():
        return _0x7f3a._0xd4
    
    @staticmethod
    def _0x10():
        return _0x7f3a._0xe5
    
    @staticmethod
    def _0x11():
        return _0x7f3a._0xf6
    
    @staticmethod
    def _0x12():
        return _0x7f3a._0x28
    
    @staticmethod
    def _0x13():
        return _0x7f3a._0x39
    
    @staticmethod
    def _0x14():
        return _0x7f3a._0xbb(_0x7f3a._0xc3)
    
    @staticmethod
    def _0x15():
        return _0x7f3a._0x4a
    
    @staticmethod
    def _0x16():
        return _0x7f3a._0x5b
    
    @staticmethod
    def _0x17():
        return _0x7f3a._0x6c
    
    @staticmethod
    def _0x18():
        return _0x7f3a._0x7d
    
    @staticmethod
    def _0x19():
        return _0x7f3a._0x8e
    
    @staticmethod
    def _0x1a():
        return _0x7f3a._0x9f

def _0x1b(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not _0x7f3a._0xcc():
            sys.exit(1)
        return await func(*args, **kwargs)
    return wrapper

if not _0x7f3a._0xcc():
    sys.exit(1)

_g1 = _0x7f3a._0xdd
_g2 = _0x7f3a._0xee
_g3 = _0x7f3a._0xff
_g4 = _0x7f3a._0x10
_g5 = _0x7f3a._0x11
_g6 = _0x7f3a._0x12
_g7 = _0x7f3a._0x13
_g8 = _0x7f3a._0x14
_g9 = _0x7f3a._0x15
_g10 = _0x7f3a._0x16
_g11 = _0x7f3a._0x17
_g12 = _0x7f3a._0x18
_g13 = _0x7f3a._0x19
_g14 = _0x7f3a._0x1a
