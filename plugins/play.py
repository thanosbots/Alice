import asyncio
import os
import random
import aiohttp
from pyrogram import filters, errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Voice
from pyrogram.raw.functions.phone import CreateGroupCall
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream, AudioQuality
from ntgcalls import TelegramServerError
from youtubesearchpython.__future__ import VideosSearch # 🌟 NEW: Smart Search

from config import _C
from core.clients import _b1, _a1, _c1
from database.chats import _asc
from database.users import _inc_played, _asu
from helpers.api import _dm
from helpers.queue import _atq, _aac_fn, _q
from core._0x1a2b import _gb
from helpers.thumbnail import generate_thumbnail

@_b1.on_message(filters.command(["play"], ["", "/"]) & ~filters.private)
async def _ss(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _cid = _m.chat.id
    _uid = _m.from_user.id
    _uname = _m.from_user.first_name
    bot_name = _c.me.first_name if _c.me else "Music Bot"
    
    # Update user in DB
    await _asu(_uid, _uname)
    
    _cn = _m.chat.title
    _cl = f"@{_m.chat.username}" if _m.chat.username else "Private Chat"
    _rb = (f"@{_m.from_user.username}" if _m.from_user.username else _m.from_user.mention) if _m.from_user else "Anonymous User"
    
    _rp = _m.reply_to_message
    _at = _rp.audio or _rp.voice if _rp else None
    
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    if _at:
        _aux = await _m.reply_text(f"**🔄 {_gb('pr')}...**")
        _lk = _rp.link if hasattr(_rp, 'link') else "Telegram Audio"
        _id = _at.file_unique_id
        try:
            _ti = _at.title or _at.file_name
        except:
            _ti = "Telegram Audio"
        _du = getattr(_at, 'duration', 0)
        try:
            _fn = _at.file_unique_id + "." + (_at.file_name.split(".")[-1] if not isinstance(_at, Voice) else "ogg")
        except:
            _fn = _at.file_unique_id + ".ogg"
            
        _fn = os.path.join(os.path.realpath("downloads"), _fn)
        
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
            return await _m.reply_text("**⚠️ Please provide a song name or link.**")
        
        _qr = " ".join(_m.command[1:])
        _aux = await _m.reply_text(f"**🔄 {_gb('pr')}...**")
        
        # ==========================================
        # 🧠 SMART SEARCH: ASK YOUTUBE FIRST
        # ==========================================
        smart_query = _qr
        try:
            yt_search = VideosSearch(_qr, limit=1)
            yt_result = await yt_search.next()
            
            if yt_result and yt_result.get('result'):
                top_video = yt_result['result'][0]
                yt_title = top_video.get('title', '')
                yt_artist = top_video.get('channel', {}).get('name', '')
                
                # Combine title and channel name
                smart_query = f"{yt_title} {yt_artist}"
                # Remove useless video keywords to help JioSaavn find the raw audio track
                for word in ["Official Video", "Lyrical", "Music Video", "Video", "Audio", "Full Song"]:
                    smart_query = smart_query.replace(word, "").replace(word.lower(), "")
                
                smart_query = smart_query.strip()
        except Exception as e:
            smart_query = _qr 
        # ==========================================

        try:
            # Query JioSaavn with the highly specific YouTube result
            _fp, _ti, _du, _lk, _th = await _dm(smart_query)
            
            if not _fp:
                # Fallback to the user's original query if smart search misses
                _fp, _ti, _du, _lk, _th = await _dm(_qr)
                if not _fp:
                    return await _aux.edit("**❌ Song not found on JioSaavn.**")
        except Exception as _e:
            return await _aux.edit(f"**❌ Error: {_e}**")
            
    # ==========================================
    # 🎨 DYNAMIC THUMBNAIL GENERATION
    # ==========================================
    try:
        await _aux.edit("**🎨 Generating Thumbnail...**")
        
        temp_cover_path = os.path.join("downloads", f"cover_{random.randint(1000, 9999)}.jpg")
        if _th and _th.startswith("http"):
            async with aiohttp.ClientSession() as session:
                async with session.get(_th) as resp:
                    if resp.status == 200:
                        with open(temp_cover_path, 'wb') as f:
                            f.write(await resp.read())
        else:
            temp_cover_path = "dummy_cover"
            
        loop = asyncio.get_event_loop()
        premium_thumb = await loop.run_in_executor(
            None, 
            generate_thumbnail, 
            temp_cover_path, 
            _ti,       
            _du,       
            0,         
            _rb,       
            bot_name   
        )
        _th = premium_thumb 
        
    except Exception as e:
        print(f"Thumbnail Generation Failed: {e}")
    # ==========================================
    
    _ms = MediaStream(
        media_path=_fp,
        video_flags=MediaStream.Flags.IGNORE,
        audio_parameters=AudioQuality.MEDIUM,
    )
    _st = "Audio"
    
    if _cid not in _q:
        try:
            try:
                await _c1.join_vc(_cid, _ms)
            except NoActiveGroupCall:
                try:
                    _peer = await _b1.resolve_peer(_cid)
                    await _b1.invoke(
                        CreateGroupCall(
                            peer=_peer,
                            random_id=random.randint(10000, 999999999)
                        )
                    )
                    await asyncio.sleep(1) 
                except Exception:
                    pass 
                
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
                        return await _aux.edit("**⚠️ Make me admin so I can auto-start Voice Chats!**")
                    
                    try:
                        await _c1.join_vc(_cid, _ms)
                    except NoActiveGroupCall:
                        return await _aux.edit("**❌ Could not start the Voice Chat. Please start it manually.**")
                except Exception as _e:
                    return await _aux.edit(f"**❌ Error: {_e}**")
            except TelegramServerError:
                return await _aux.edit("⚠️ **Telegram Server Error.**")
        except Exception as _e:
            return await _aux.edit(f"❌ **Stream failed.**\n\n`{_e}`")
    
    _pos = await _atq(_cid, _ms, _ti, _du, _lk, _th, _st, _cn, _cl, _rb)
    
    _sst = f"**{_C._e} {_gb('p')}**" if _pos == 0 else f"**✅ Added to {_gb('q')} (Position: #{_pos})**"
    
    _cap = f"""{_sst}

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
    except Exception as e:
        print(f"Failed to send thumbnail: {e}")
        await _m.reply_photo(photo=_C.START_IMAGE_URL, caption=_cap, reply_markup=_btn)
    
    if _cid != _C.LOG_GROUP_ID:
        try:
            await _c.send_photo(_C.LOG_GROUP_ID, photo=_th, caption=_cap)
        except:
            pass
            
    await _inc_played(_uid)
    
    if _pos == 0:
        await _aac_fn(_cid, _st)
    
    await _asc(_cid)