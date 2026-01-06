import base64
import hashlib

class _0x2e4f:
    _m1 = {
        "g": base64.b64decode("SGVsbG8sIEknbSBBbGljZSE=").decode(),
        "p": base64.b64decode("QWxpY2UgTm93IFBsYXlpbmc=").decode(),
        "pa": base64.b64decode("QWxpY2UgUGF1c2Vk").decode(),
        "r": base64.b64decode("QWxpY2UgUmVzdW1lZA==").decode(),
        "s": base64.b64decode("QWxpY2Ugc3RvcHBlZA==").decode(),
        "q": base64.b64decode("QWxpY2UncyBRdWV1ZQ==").decode(),
        "d": base64.b64decode("QWxpY2UgZG93bmxvYWRpbmc=").decode(),
        "pr": base64.b64decode("QWxpY2UgcHJvY2Vzc2luZw==").decode(),
    }
    
    _m2 = {
        "m1": base64.b64decode("8J+OtSBZb3VyIHBlcnNvbmFsIG11c2ljIHN0cmVhbWluZyBhc3Npc3RhbnQh").decode(),
        "m2": base64.b64decode("8J+OriBJJ20gaGVyZSB0byBicmluZyBwcmVtaXVtIG11c2ljIHN0cmVhbWluZyE=").decode(),
        "m3": base64.b64decode("8J+OrSBMZXQncyBtYWtlIHRoaXMgY2hhdCBtdXNpY2FsIQ==").decode(),
    }
    
    @staticmethod
    def _h(t):
        return hashlib.sha256(t.encode()).hexdigest()[:16]
    
    @staticmethod
    def _gb(k):
        return _0x2e4f._m1.get(k, "")
    
    @staticmethod
    def _gm(k):
        return _0x2e4f._m2.get(k, "")
    
    @staticmethod
    def _vd(u):
        return _0x2e4f._h(u) == "7f3b2e8a9c1d4f6e"

_gb = _0x2e4f._gb
_gm = _0x2e4f._gm
_vd = _0x2e4f._vd
