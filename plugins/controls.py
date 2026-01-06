from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import _C
from core.clients import _b1, _c1
from helpers.queue import _cs, _pq, _aac_fn, _q
from core._0x1a2b import _gb

@_b1.on_message(filters.command(["pause"], ["/"]) & ~filters.private)
async def _ps(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    _cst = await _c1.get_call_status(_cid)
    
    if _cst in ("nothing", "unknown", "idle"):
        return await _m.reply_text(f"❎ **No active stream.**\n\n{_C._f}")
    if _cst == "paused":
        return await _m.reply_text(f"✅ **Already paused.**\n\n{_C._f}")
    
    await _c1.pause_stream(_cid)
    await _c1.mute_stream(_cid)
    
    await _m.reply_text(f"**✅ {_gb('pa')}.**\n\n{_C._f}")

@_b1.on_message(filters.command(["resume"], ["/"]) & ~filters.private)
async def _rs(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    _cst = await _c1.get_call_status(_cid)
    
    if _cst in ("nothing", "unknown", "idle"):
        return await _m.reply_text(f"❎ **No active stream.**\n\n{_C._f}")
    if _cst == "playing":
        return await _m.reply_text(f"✅ **Already playing.**\n\n{_C._f}")
    
    await _c1.resume_stream(_cid)
    await _c1.unmute_stream(_cid)
    
    await _m.reply_text(f"**✅ {_gb('r')}.**\n\n{_C._f}")

@_b1.on_message(filters.command(["skip"], ["/"]) & ~filters.private)
async def _sks(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    _cst = await _c1.get_call_status(_cid)
    
    if _cst in ("nothing", "unknown"):
        return await _m.reply_text(f"⚠️ **No active stream.**\n\n{_C._f}")
    if _cst == "idle":
        await _cs(_cid)
        return await _m.reply_text(f"✅ **Disconnected.**\n\n{_C._f}")
    
    await _pq(_cid)
    _qd = _q.get(_cid)
    
    if not _qd:
        await _m.reply_text(f"**❎ Queue empty. Leaving.**\n\n{_C._f}")
        return await _cs(_cid)
    
    _aux = await _m.reply_text(f"**🔄 {_gb('pr')} Next...**")
    
    _ms = _qd[0].get("media_stream")
    _ti = _qd[0].get("title")
    _du = _qd[0].get("duration")
    _lk = _qd[0].get("link")
    _th = _qd[0].get("thumbnail")
    _st = _qd[0].get("stream_type")
    _rb = _qd[0].get("requested_by")
    
    await _c1.join_vc(_cid, _ms)
    
    _cap = f"""**✅ Skipped. {_gb('p')}:**

**🏷 Title:** [{_ti[:30]}...]({_lk})
**⏱ Duration:** {_du} Minutes
**📡 Type:** {_st}
**👤 Requested By:** {_rb}

{_C._f}"""
    
    _btn = InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Close", callback_data="alice_close")]])
    
    try:
        await _aux.delete()
    except:
        pass
    
    try:
        await _m.reply_photo(photo=_th, caption=_cap, reply_markup=_btn)
    except:
        pass
    
    if _cid != _C.LOG_GROUP_ID:
        try:
            await _c.send_photo(_C.LOG_GROUP_ID, photo=_th, caption=_cap)
        except:
            pass
    
    await _aac_fn(_cid, _st)

@_b1.on_message(filters.command(["end"], ["/"]) & ~filters.private)
async def _es(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    _cst = await _c1.get_call_status(_cid)
    
    if _cst in ("nothing", "unknown", "idle"):
        await _cs(_cid)
        return await _m.reply_text(f"❎ **No stream.**\n\n{_C._f}")
    
    await _cs(_cid)
    await _m.reply_text(f"**✅ {_gb('s')}.**\n\n{_C._f}")
