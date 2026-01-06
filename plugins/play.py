import asyncio
from pyrogram import filters, errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from ntgcalls import TelegramServerError
from config import _C
from core.clients import _b1, _a1, _c1
from database.chats import _asc
from helpers.api import _dm
from helpers.queue import _atq, _aac_fn, _q
from core._0x1a2b import _gb

@_b1.on_message(filters.command(["play", "vplay"], ["", "/"]) & ~filters.private)
async def _ss(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    _cn = _m.chat.title
    _cl = f"@{_m.chat.username}" if _m.chat.username else "Private Chat"
    _rb = (f"@{_m.from_user.username}" if _m.from_user.username else _m.from_user.mention) if _m.from_user else "Anonymous User"
    
    _rp = _m.reply_to_message
    _at = _rp.audio or _rp.voice if _rp else None
    _vt = _rp.video or _rp.document if _rp else None
    
    if _at or _vt:
        _aux = await _m.reply_text(f"**🔄 {_gb('pr')}...**")
        _lk = _rp.link
        if _at:
            _id = _at.file_unique_id
            try:
                _ti = _at.title or _at.file_name
            except:
                _ti = "Telegram Audio"
            _du = _at.duration
            try:
                _fn = _at.file_unique_id + "." + (_at.file_name.split(".")[-1] if not isinstance(_at, Voice) else "ogg")
            except:
                _fn = _at.file_unique_id + ".ogg"
            _fn = os.path.join(os.path.realpath("downloads"), _fn)
            _vs = False
        if _vt:
            _id = _vt.file_unique_id
            try:
                _ti = _vt.title or _vt.file_name
            except:
                _ti = "Telegram Video"
            _du = _vt.duration
            try:
                _fn = _vt.file_unique_id + "." + _vt.file_name.split(".")[-1]
            except:
                _fn = _vt.file_unique_id + ".mp4"
            _fn = os.path.join(os.path.realpath("downloads"), _fn)
            _vs = True
        if not os.path.exists(_fn):
            try:
                await _aux.edit(f"**⬇️ {_gb('d')}...**")
                await _rp.download(file_name=_fn)
            except:
                return await _aux.edit("**❌ Download failed.**")
                    
            while not os.path.exists(_fn):
                await asyncio.sleep(0.5)
        
        _fp = _fn
        _th = _C.START_IMAGE_URL
    else:
        if len(_m.command) < 2:
            return await _m.reply_text("**⚠️ Please provide a query or link.**")
        
        _qr = " ".join(_m.command[1:])
        _aux = await _m.reply_text(f"**🔄 {_gb('pr')}...**")
        
        _vs = _m.command[0].startswith("v")
        
        try:
            _fp, _ti, _du, _lk, _th = await _dm(_qr, _vs)
            
            if not _fp:
                return await _aux.edit("**❌ API Failed.**")
        except Exception as _e:
            return await _aux.edit(f"**❌ Error: {_e}**")
    
    _ms = (
        MediaStream(
            media_path=_fp,
            video_flags=MediaStream.Flags.IGNORE,
            audio_parameters=AudioQuality.MEDIUM,
        ) if not _vs else
        MediaStream(
            media_path=_fp,
            audio_parameters=AudioQuality.MEDIUM,
            video_parameters=VideoQuality.SD_480p,
        )
    )
    _st = "Audio" if not _vs else "Video"
    
    if _cid not in _q:
        try:
            try:
                await _c1.join_vc(_cid, _ms)
            except NoActiveGroupCall:
                try:
                    try:
                        await _b1.get_chat_member(_cid, _a1.id)
                    except errors.UserNotParticipant:
                        try:
                            _il = _m.chat.username or await _c.export_chat_invite_link(_cid)
                            await _a1.join_chat(_il)
                        except:
                            return await _aux.edit("**⚠️ Failed to invite Assistant.**")
                    except errors.ChatAdminRequired:
                        return await _aux.edit("**⚠️ Make me admin.**")
                    
                    try:
                        await _c1.join_vc(_cid, _ms)
                    except NoActiveGroupCall:
                        return await _aux.edit("**❌ No active Voice Chat.**")
                except Exception as _e:
                    return await _aux.edit(f"**❌ Error: {_e}**")
            except TelegramServerError:
                return await _aux.edit("⚠️ **Telegram Server Error.**")
        except Exception as _e:
            return await _aux.edit(f"❌ **Stream failed.**\n\n`{_e}`")
    
    _pos = await _atq(_cid, _ms, _ti, _du, _lk, _th, _st, _cn, _cl, _rb)
    
    _sst = f"**{_C._e} {_gb('p')}**" if _pos == 0 else f"**✅ Added to {_gb('q')} (Position: #{_pos})**"
    
    _cap = f"""{_sst}

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
        await _m.reply_photo(photo=_C.START_IMAGE_URL, caption=_cap, reply_markup=_btn)
    
    if _cid != _C.LOG_GROUP_ID:
        try:
            await _c.send_photo(_C.LOG_GROUP_ID, photo=_th, caption=_cap)
        except:
            pass
    
    if _pos == 0:
        await _aac_fn(_cid, _st)
    
    await _asc(_cid)
