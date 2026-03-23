import aiohttp
import asyncio
import logging
import os
from config import _C

_l = logging.getLogger("Alice.API")
_gs = None

async def _gas():
    global _gs
    if _gs is None or _gs.closed:
        _t = aiohttp.ClientTimeout(total=300, connect=60)
        _cn = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        _gs = aiohttp.ClientSession(
            timeout=_t,
            connector=_cn,
            headers={"User-Agent": "AliceMusicBot/2.0"}
        )
    return _gs

async def _cls():
    global _gs
    if _gs and not _gs.closed:
        await _gs.close()
        _gs = None

async def _dm(_q: str, _iv: bool = False):
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
            
        _ts = int(asyncio.get_event_loop().time())
        _ex = "mp4" if _iv else "mp3"
        
        _au = f"{_C.CUSTOM_API_URL}/music"
        _p = {
            "query": _q,
            "video": "true" if _iv else "false",
            "api_key": _C.CUSTOM_API_KEY
        }
        
        _s = await _gas()
        
        async with _s.get(_au, params=_p) as _r:
            if _r.status != 200:
                _l.error(f"API Status {_r.status}")
                return None, None, None, None, None
                
            _d = await _r.json()
        
        if _d.get("status") != "success":
            _l.error(f"API Failed: {_d.get('error')}")
            return None, None, None, None, None

        _su = _d.get("stream_url")
        _ti = _d.get("title", "Unknown Title")
        _du = _d.get("duration", "0")
        _th = _d.get("thumbnail", _C.START_IMAGE_URL)
        _lk = _d.get("link", _q)
        
        try:
            _di = int(float(_du))
            _dm = f"{_di // 60}:{_di % 60:02d}" if _di > 60 else str(_di)
        except:
            _dm = str(_du)

        if not _su:
            return None, None, None, None, None

        _vi = _d.get("id", str(_ts))
        _fp = os.path.join("downloads", f"alice_{_vi}.{_ex}")

        if os.path.exists(_fp):
            _fs = os.path.getsize(_fp)
            if _fs > 50000:
                _l.info(f"Using cached: {_fp}")
                return _fp, _ti, _dm, _lk, _th
            else:
                os.remove(_fp)

        _l.info(f"Downloading: {_ti[:40]}...")
        
        async with _s.get(_su) as _rs:
            if _rs.status != 200:
                _l.error(f"Download failed: {_rs.status}")
                return None, None, None, None, None
                
            with open(_fp, 'wb') as _f:
                async for _ch in _rs.content.iter_chunked(1024 * 256):
                    _f.write(_ch)
                _f.flush()
                os.fsync(_f.fileno())
            
            if not os.path.exists(_fp):
                return None, None, None, None, None
                
            _fs = os.path.getsize(_fp)
            if _fs < 50000:
                os.remove(_fp)
                return None, None, None, None, None
            
            _l.info(f"Downloaded: {_fs} bytes")
            return _fp, _ti, _dm, _lk, _th
                    
    except Exception as _e:
        _l.error(f"API Error: {_e}")
        return None, None, None, None, None
