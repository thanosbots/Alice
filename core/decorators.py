from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import filters as fl
from pytgcalls.types import ChatUpdate, Update
from config import _C
from core.clients import _b1
from helpers.queue import _cs, _pq, _aac_fn, _q
from core._0x1a2b import _gb

async def _sh(_cl):
    @_cl.vcbot.on_update(fl.chat_update(ChatUpdate.Status.LEFT_CALL))
    async def _lh(_, _u: Update):
        return await _cs(_u.chat_id)

    @_cl.vcbot.on_update(fl.stream_end)
    async def _seh(_, _u: Update):
        _cid = _u.chat_id
        await _pq(_cid)
        _qd = _q.get(_cid)
        
        if not _qd:
            await _b1.send_message(_cid, f"**🎵 {_C._n}: Queue is empty. Leaving the Voice Chat.**\n\n{_C._f}")
            return await _cs(_cid)
        
        _ms = _qd[0].get("media_stream")
        _ti = _qd[0].get("title")
        _du = _qd[0].get("duration")
        _lk = _qd[0].get("link")
        _th = _qd[0].get("thumbnail")
        _st = _qd[0].get("stream_type")
        _cn = _qd[0].get("chat_name")
        _rb = _qd[0].get("requested_by")

        await _cl.join_vc(_cid, _ms)
        
        _cap = f"""**🎵 {_gb('p')}**

**🏷 Title:** [{_ti[:30]}...]({_lk})
**⏱ Duration:** {_du} Minutes
**📡 Type:** {_st}
**👤 Requested By:** {_rb}
**📍 Chat:** {_cn}

{_C._f}"""
        
        _btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("✖️ Close", callback_data="alice_close")
        ]])
        
        try:
            await _b1.send_photo(_cid, photo=_th, caption=_cap, reply_markup=_btn)
        except:
            pass
            
        if _cid != _C.LOG_GROUP_ID:
            try:
                await _b1.send_photo(_C.LOG_GROUP_ID, photo=_th, caption=_cap)
            except:
                pass
                
        await _aac_fn(_cid, _st)
