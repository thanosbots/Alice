from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import _C, HELP_DICT # Added HELP_DICT import
from core.clients import _b1, _c1
from helpers.queue import _cs, _pq, _aac_fn, _q

# Registering the Admin commands to the dynamic Help Menu!
HELP_DICT["⚙️ Admin"] = """**⚙️ Admin & Control Commands**

`/pause` - Pause the currently playing stream
`/resume` - Resume the paused stream
`/skip` or `/next` - Skip to the next track in the queue
`/end` or `/stop` - Stop playback, clear queue, and make the bot leave"""

@_b1.on_message(filters.command(["pause"], ["/"]) & ~filters.private)
async def _ps(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    
    if _cid not in _q:
        return await _m.reply_text("❎ **No active stream.**")
    
    await _c1.pause_stream(_cid)
    
    # Cleaned up response
    await _m.reply_text("**✅ Stream Paused.**")


@_b1.on_message(filters.command(["resume"], ["/"]) & ~filters.private)
async def _rs(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    
    if _cid not in _q:
        return await _m.reply_text("❎ **No active stream.**")
    
    await _c1.resume_stream(_cid)
    
    # Cleaned up response
    await _m.reply_text("**✅ Stream Resumed.**")


@_b1.on_message(filters.command(["skip", "next"], ["/"]) & ~filters.private)
async def _sks(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    bot_name = _c.me.first_name if _c.me else "Music Bot"
    
    if _cid not in _q:
        return await _m.reply_text("⚠️ **No active stream.**")
    
    await _pq(_cid)
    _qd = _q.get(_cid)
    
    if not _qd:
        await _cs(_cid)
        try:
            await _c1.leave_vc(_cid)
        except:
            pass
        return await _m.reply_text(f"**❎ Queue empty. {bot_name} left the VC.**")
    
    _aux = await _m.reply_text("**🔄 Processing Next...**")
    
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
    
   
    _cap = f"""**✅ Skipped. ✨ {bot_name} Now Playing Next:**

**🏷 Title:** [{_ti[:40]}]({_lk})
**⏱ Duration:** {_du} Minutes
**📡 Source:** {bytes.fromhex('616c69636520617069').decode()}
**👤 Requested By:** {_rb}"""
    
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
    bot_name = _c.me.first_name if _c.me else "Music Bot"
    
    if _cid not in _q:
        return await _m.reply_text("❎ **No active stream.**")
    
    await _cs(_cid)
    try:
        await _c1.leave_vc(_cid)
    except:
        pass
   
    await _m.reply_text(f"**✅ Stream stopped and {bot_name} cleared the queue.**")