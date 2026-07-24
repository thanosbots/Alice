import asyncio
import logging

from core.clients import _c1

_l = logging.getLogger("Alice.Queue")

_q = {}
_aac = set()
_avc = set()

# Per-chat lock: do stream-end events ek saath aayein to queue do baar pop
# ho jaati thi aur ek gaana skip ho jaata tha.
_locks = {}


def _get_lock(_cid: int) -> asyncio.Lock:
    if _cid not in _locks:
        _locks[_cid] = asyncio.Lock()
    return _locks[_cid]


async def _atq(_cid: int, _ms, _t, _d, _l_, _th, _st, _cn, _cl, _rb, _meta=None):
    if _cid not in _q:
        _q[_cid] = []

    _i = {
        "media_stream": _ms,
        "title": _t,
        "duration": _d,
        "link": _l_,
        "thumbnail": _th,
        "stream_type": _st,
        "chat_name": _cn,
        "chat_link": _cl,
        "requested_by": _rb,
        "meta": _meta or {},      # artist / genre / views — up-next caption ke liye
    }

    _q[_cid].append(_i)
    return len(_q[_cid]) - 1


async def _gq(_cid: int):
    return _q.get(_cid, [])


async def _pq(_cid: int):
    _qx = _q.get(_cid)
    if _qx:
        return _qx.pop(0)
    return None


async def _cs(_cid: int):
    """
    Chat ka sab kuch saaf karo aur VC chhodo.

    PEHLE yahan tha:

        try:
            await _c1.leave_vc(_cid)
        except Exception:
            pass

    Wo `pass` hi bug tha. leave_vc() fail hone par error chupchaap gayab ho
    jaata tha — bot VC mein baitha rehta tha aur console par kuch nahi aata
    tha. Ab exception LOG hoti hai, aur leave hua ya nahi wo verify bhi
    karte hain.

    `_locks.pop()` bhi hata diya: wo tab chalta tha jab advance() abhi lock
    pakde hue tha, to agla _get_lock() naya lock bana deta — mutual
    exclusion toot jaati. Ek asyncio.Lock per chat bhulaane layak memory hai.
    """
    _q.pop(_cid, None)

    try:
        await _c1.leave_vc(_cid)
        _l.info(f"left vc in {_cid}")
    except Exception as _e:
        _l.error(f"leave_vc FAILED in {_cid}: {type(_e).__name__}: {_e}")

    # Sach mein nikle ya nahi — verify karo, ek retry do.
    try:
        _st = await _c1.get_call_status(_cid)
        if _st != "nothing":
            _l.warning(f"still in call {_cid} (status={_st}) — retrying leave")
            await asyncio.sleep(1)
            try:
                await _c1.leave_vc(_cid)
                _l.info(f"left vc in {_cid} on retry")
            except Exception as _e:
                _l.error(f"retry leave FAILED in {_cid}: {type(_e).__name__}: {_e}")
    except Exception as _e:
        _l.error(f"call status check failed in {_cid}: {_e}")

    try:
        await _dac(_cid)
    except Exception as _e:
        _l.error(f"_dac failed in {_cid}: {_e}")


async def _aac_fn(_cid: int, _st: str):
    _sx = (_st or "").lower()
    if _sx == "audio":
        _aac.add(_cid)
        _avc.discard(_cid)
    elif _sx == "video":
        _avc.add(_cid)
        _aac.discard(_cid)


async def _dac(_cid: int):
    _aac.discard(_cid)
    _avc.discard(_cid)