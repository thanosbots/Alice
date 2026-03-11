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
    
    # Check our internal queue instead of PyTgCalls
    if _cid not in _q:
        return await _m.reply_text(f"❎ **No active stream.**\n\n{_C._f}")
    
    await _c1.pause_stream(_cid)
    
    await _m.reply_text(f"**✅ {_gb('pa')}.**\n\n{_C._f}")


@_b1.on_message(filters.command(["resume"], ["/"]) & ~filters.private)
async def _rs(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    
    if _cid not in _q:
        return await _m.reply_text(f"❎ **No active stream.**\n\n{_C._f}")
    
    await _c1.resume_stream(_cid)
    
    await _m.reply_text(f"**✅ {_gb('r')}.**\n\n{_C._f}")


@_b1.on_message(filters.command(["skip", "next"], ["/"]) & ~filters.private)
async def _sks(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    
    # 1. Check if anything is playing
    if _cid not in _q:
        return await _m.reply_text(f"⚠️ **No active stream.**\n\n{_C._f}")
    
    # 2. Pop the current song out of the queue
    await _pq(_cid)
    _qd = _q.get(_cid)
    
    # 3. If the queue is now empty, hang up and leave
    if not _qd:
        await _cs(_cid)
        try:
            await _c1.leave_vc(_cid)
        except:
            pass
        return await _m.reply_text(f"**❎ Queue empty. {_C._n} left the VC.**\n\n{_C._f}")
    
    _aux = await _m.reply_text(f"**🔄 {_gb('pr')} Next...**")
    
    _ms = _qd[0].get("media_stream")
    _ti = _qd[0].get("title")
    _du = _qd[0].get("duration")
    _lk = _qd[0].get("link")
    _th = _qd[0].get("thumbnail")
    _st = _qd[0].get("stream_type")
    _rb = _qd[0].get("requested_by")
    
    try:
        await _c1.join_vc(_cid, _ms)
    except Exception as e:
        await _cs(_cid)
        try:
            await _c1.leave_vc(_cid)
        except:
            pass
        return await _aux.edit(f"**❌ Failed to skip:** `{e}`")
    
    _cap = f"""**✅ Skipped. {_gb('p')} Next:**

**🏷 Title:** [{_ti[:40]}]({_lk})
**⏱ Duration:** {_du} Minutes
**📡 Source:** JioSaavn
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
        await _m.reply_photo(photo=_C.START_IMAGE_URL, caption=_cap, reply_markup=_btn)
    
    await _aac_fn(_cid, _st)


@_b1.on_message(filters.command(["end", "stop"], ["/"]) & ~filters.private)
async def _es(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    
    if _cid not in _q:
        return await _m.reply_text(f"❎ **No active stream.**\n\n{_C._f}")
    
    # Clear the queue completely and force the assistant to leave
    await _cs(_cid)
    try:
        await _c1.leave_vc(_cid)
    except:
        pass
    
    await _m.reply_text(f"**✅ {_gb('s')}.**\n\n{_C._f}")
