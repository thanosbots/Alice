from core.clients import _c1

_q = {}
_aac = set()
_avc = set()

async def _atq(_cid: int, _ms, _t, _d, _l, _th, _st, _cn, _cl, _rb):
    if _cid not in _q:
        _q[_cid] = []

    _i = {
        "media_stream": _ms,
        "title": _t,
        "duration": _d,
        "link": _l,
        "thumbnail": _th,
        "stream_type": _st,
        "chat_name": _cn,
        "chat_link": _cl,
        "requested_by": _rb
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
    _q.pop(_cid, None)
    try:
        await _c1.leave_vc(_cid)
    except:
        pass
    try:
        await _dac(_cid)
    except:
        pass

async def _aac_fn(_cid: int, _st: str):
    _sx = _st.lower()
    if _sx == "audio":
        _aac.add(_cid)
        _avc.discard(_cid)
    elif _sx == "video":
        _avc.add(_cid)
        _aac.discard(_cid)

async def _dac(_cid: int):
    _aac.discard(_cid)
    _avc.discard(_cid)
