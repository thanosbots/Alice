import asyncio
import glob
import logging
import os

import aiohttp

from config import _C

_l = logging.getLogger("Alice.API")
_gs = None

# Content-Type -> file extension. Sirf naming ke liye; ntgcalls waise bhi
# content sniff karta hai, par sahi extension debugging aasan karta hai.
_CT_MAP = {
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/aac": "m4a",
    "audio/webm": "webm",
    "audio/ogg": "opus",
    "audio/opus": "opus",
    "audio/mpeg": "mp3",
    "video/mp4": "mp4",
    "video/webm": "webm",
}

_MIN_SIZE = 50_000


async def _gas():
    global _gs
    if _gs is None or _gs.closed:
        _t = aiohttp.ClientTimeout(total=300, connect=60, sock_read=60)
        _cn = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        _gs = aiohttp.ClientSession(
            timeout=_t,
            connector=_cn,
            headers={"User-Agent": "AliceMusicBot/2.0"},
        )
    return _gs


async def _cls():
    global _gs
    if _gs and not _gs.closed:
        await _gs.close()
        _gs = None


def _parse_duration(_raw) -> int:
    """
    HAMESHA int seconds return karta hai.

    Pehle ye function "3:45" jaisi string return karta tha, aur Telegram-audio
    wale path se int seconds aata tha. Dono generate_thumbnail() ko jaate the —
    isliye API songs par thumbnail chupchaap fail ho raha tha.
    """
    if _raw is None:
        return 0
    if isinstance(_raw, (int, float)):
        return int(_raw)
    _s = str(_raw).strip()
    if ":" in _s:                       # "3:45" ya "1:02:33"
        try:
            _parts = [int(_p) for _p in _s.split(":")]
        except ValueError:
            return 0
        _total = 0
        for _p in _parts:
            _total = _total * 60 + _p
        return _total
    try:
        return int(float(_s))
    except ValueError:
        return 0


def _cached_path(_vi: str):
    for _p in glob.glob(os.path.join("downloads", f"alice_{_vi}.*")):
        try:
            if os.path.getsize(_p) > _MIN_SIZE:
                return _p
            os.remove(_p)
        except OSError:
            pass
    return None


def _fix_mojibake(_s):
    """'JoÃ£o Faria' -> 'João Faria' (UTF-8 bytes ko latin-1 samjha gaya tha)."""
    if not isinstance(_s, str) or not any(m in _s for m in ("Ã", "â€", "Â")):
        return _s
    try:
        return _s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return _s


async def _dm(_q: str, _iv: bool = False):
    """
    Backward-compatible wrapper.
    Returns: (file_path, title, duration_seconds:int, link, thumbnail_url)
    """
    _r = await _dm_full(_q, _iv)
    if not _r:
        return None
    return _r["path"], _r["title"], _r["duration"], _r["link"], _r["thumbnail"]


async def _dm_full(_q: str, _iv: bool = False):
    """
    Poora metadata dict return karta hai (thumbnail ke liye artist/genre/views
    chahiye the, jo 5-tuple mein fit nahi hote the).
    Fail par None.
    """
    _fp = None
    try:
        os.makedirs("downloads", exist_ok=True)

        _au = f"{_C.CUSTOM_API_URL}/youtube"
        _p = {
            "query": _q,
            "video": "true" if _iv else "false",
            "api_key": _C.CUSTOM_API_KEY,
        }

        _s = await _gas()

        async with _s.get(_au, params=_p) as _r:
            if _r.status != 200:
                _l.error(f"API status {_r.status}")
                return None
            _d = await _r.json()

        if _d.get("status") != "success":
            _l.error(f"API failed: {_d.get('error', 'unknown')}")
            return None

        _raw_su = _d.get("stream_url")
        if not _raw_su:
            return None

        # Raw IP hata ke apne HTTPS domain se stream karo
        _stream_id = _raw_su.split("/")[-1]
        _su = f"{_C.CUSTOM_API_URL}/stream/{_stream_id}"

        _ti = _fix_mojibake(_d.get("title", "Unknown Title"))
        _ar = _fix_mojibake(_d.get("artist") or "")
        _du = _parse_duration(_d.get("duration"))
        _th = _d.get("thumbnail") or _C.START_IMAGE_URL
        _lk = _d.get("link", _q)
        _vi = str(_d.get("id") or abs(hash(_q)))

        _meta = {
            "title": _ti,
            "artist": _ar,
            "duration": _du,
            "link": _lk,
            "thumbnail": _th,
            "genre": _d.get("genre") or "",
            "views": _d.get("views"),
            "likes": _d.get("likes"),
            "id": _vi,
        }

        _hit = _cached_path(_vi)
        if _hit:
            _l.info(f"Cache hit: {_hit}")
            return {**_meta, "path": _hit}

        _l.info(f"Downloading: {_ti[:40]}")

        async with _s.get(_su) as _rs:
            if _rs.status != 200:
                _l.error(f"Download failed: {_rs.status}")
                return None

            # Extension response ke hisaab se — hardcoded "mp3" nahi.
            # Agar API m4a/opus passthrough karega to file sahi naam payegi.
            _ct = (_rs.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            _ex = _CT_MAP.get(_ct, "mp4" if _iv else "m4a")
            _fp = os.path.join("downloads", f"alice_{_vi}.{_ex}")

            with open(_fp, "wb") as _f:
                async for _ch in _rs.content.iter_chunked(1024 * 256):
                    _f.write(_ch)
                _f.flush()
                os.fsync(_f.fileno())

        _fs = os.path.getsize(_fp)
        if _fs < _MIN_SIZE:
            os.remove(_fp)
            _l.error(f"File too small: {_fs} bytes")
            return None

        _l.info(f"Downloaded {_fs} bytes -> {_fp}")
        return {**_meta, "path": _fp}

    except asyncio.CancelledError:
        raise
    except Exception as _e:
        _l.error(f"API error: {_e}")
        if _fp and os.path.exists(_fp):
            try:
                os.remove(_fp)          # aadha download pada na rahe
            except OSError:
                pass
        return None # api.py 