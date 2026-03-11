import asyncio
import logging
from pytgcalls.types import Update
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import _C
from core.clients import _b1, _c1
from helpers.queue import _cs, _pq, _q, _aac_fn
from core._0x1a2b import _gb

_l = logging.getLogger("Alice.Events")

# 1. The Auto-Play Logic (Runs safely in the background)
async def _process_stream_end(_cid):
    await asyncio.sleep(1) # Give pytgcalls a second to fully clear the old stream
    _l.info(f"🎵 Stream Ended in {_cid}. Triggering next track...")
    
    await _pq(_cid)
    _qd = _q.get(_cid)
    
    if not _qd:
        await _cs(_cid)
        try:
            await _c1.leave_vc(_cid)
        except:
            pass
        try:
            await _b1.send_message(_cid, f"**✅ Queue empty. {_C._n} left the voice chat.**\n\n{_C._f}")
        except:
            pass
        return
    
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
        return

    _cap = f"""**{_C._e} {_gb('p')} Next:**

**🏷 Title:** [{_ti[:40]}]({_lk})
**⏱ Duration:** {_du} Minutes
**📡 Source:** JioSaavn
**👤 Requested By:** {_rb}

{_C._f}"""
    
    _btn = InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Close", callback_data="alice_close")]])
    
    try:
        await _b1.send_photo(chat_id=_cid, photo=_th, caption=_cap, reply_markup=_btn)
    except:
        await _b1.send_message(chat_id=_cid, text=_cap, reply_markup=_btn)
        
    await _aac_fn(_cid, _st)



@_c1.vcbot.on_update()
def _stream_end_handler(client, update: Update):
    _ev = type(update).__name__
    
    
    print(f"=============================")
    print(f"🔊 ALICE CAUGHT EVENT: {_ev}")
    print(f"=============================")
    
    # Catch all known stream end names and trigger our background task safely
    if _ev in ["StreamAudioEnded", "StreamVideoEnded", "StreamEnd", "StreamEnded", "CallEnded", "UpdateStream"]:
        _cid = getattr(update, "chat_id", None)
        if _cid:
            loop = asyncio.get_event_loop()
            loop.create_task(_process_stream_end(_cid))
          
    _f = asyncio.Future()
    _f.set_result(None)
    return _f
