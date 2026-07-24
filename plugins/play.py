import asyncio
import functools
import os
import random

from pyrogram import filters, errors
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Voice
from pyrogram.raw.functions.phone import CreateGroupCall
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream, AudioQuality
from ntgcalls import TelegramServerError

from config import _C
from core.clients import _b1, _a1, _c1
from database.chats import _asc
from database.users import _inc_played, _asu
from helpers.api import _dm_full, _gas
from helpers.captions import now_playing, queued
from helpers.queue import _atq, _aac_fn, _q
from core._0x1a2b import _gb
from helpers.thumbnail import generate_thumbnail


# ---------------------------------------------------------------------------
# AUDIO MODE — stutter ho to "mono", sab smooth ho to "stereo" try karo.
#
#   mono   = 48000 Hz, 1 channel  -> poora frequency range, encode load aadha
#   stereo = 48000 Hz, 2 channels -> AudioQuality.HIGH ke barabar
#
# MEDIUM (36 kHz) par WAPAS MAT JAANA — wahi original quality loss tha.
# Frequency range girana quality maarta hai; channels girana nahi.
# ---------------------------------------------------------------------------
_AUDIO_MODE = "stereo"


def _audio_params():
    """
    AudioParameters ka signature py-tgcalls versions ke beech badla hai,
    isliye fail hone par AudioQuality par safe fallback.
    """
    if _AUDIO_MODE == "stereo":
        return AudioQuality.HIGH
    try:
        from pytgcalls.types import AudioParameters
        return AudioParameters(bitrate=48000, channels=1)
    except Exception as _e:
        print(f"[audio] AudioParameters unavailable ({_e}) -> AudioQuality.HIGH")
        return AudioQuality.HIGH


def _fmt_dur(_sec) -> str:
    try:
        _sec = int(float(_sec))
    except (TypeError, ValueError):
        return "0:00"
    if _sec >= 3600:
        return f"{_sec // 3600}:{(_sec % 3600) // 60:02d}:{_sec % 60:02d}"
    return f"{_sec // 60}:{_sec % 60:02d}"


async def _build_thumb(_th_url, _ti, _du_sec, _rb, _bot_name, _meta=None):
    """
    Cover download + PIL render.

    NOTE: ye ab VC join se PEHLE chalta hai (original order).
    Pichhle version mein maine ise join ke baad move kiya tha taki music
    jaldi start ho — par uska side-effect ye tha ki PIL rendering stream ke
    DAURAAN chalti thi, aur CPU tight hone par gaane ke pehle kuch second
    mein extra stutter deti thi. Music ~2 sec late start hoga, par opening
    clean rahegi.
    """
    _tmp = "dummy_cover"
    try:
        if _th_url and str(_th_url).startswith("http"):
            _path = os.path.join("downloads", f"cover_{random.randint(1000, 999999)}.jpg")
            _s = await _gas()
            async with _s.get(_th_url) as _r:
                if _r.status == 200:
                    with open(_path, "wb") as _f:
                        _f.write(await _r.read())
                    _tmp = _path

        _meta = _meta or {}
        _loop = asyncio.get_event_loop()
        # run_in_executor kwargs support nahi karta -> functools.partial
        _fn = functools.partial(
            generate_thumbnail,
            _tmp, _ti, _du_sec, 0, _rb, _bot_name,
            artist=_meta.get("artist") or None,
            genre=_meta.get("genre") or None,
            views=_meta.get("views"),
            likes=_meta.get("likes"),
        )
        return await _loop.run_in_executor(None, _fn)
    except Exception as _e:
        print(f"Thumbnail generation failed: {_e}")
        return _th_url
    finally:
        if _tmp != "dummy_cover" and os.path.exists(_tmp):
            try:
                os.remove(_tmp)
            except OSError:
                pass


@_b1.on_message(filters.command(["play"], ["", "/"]) & ~filters.private)
async def _ss(_c, _m):
    try:
        await _m.delete()
    except Exception:
        pass

    _cid = _m.chat.id
    _uid = _m.from_user.id
    _uname = _m.from_user.first_name
    _bot_name = _c.me.first_name if _c.me else "Music Bot"

    await _asu(_uid, _uname)

    _cn = _m.chat.title
    _cl = f"@{_m.chat.username}" if _m.chat.username else "Private Chat"
    _rb = (
        (f"@{_m.from_user.username}" if _m.from_user.username else _m.from_user.mention)
        if _m.from_user
        else "Anonymous User"
    )

    _rp = _m.reply_to_message
    _at = (_rp.audio or _rp.voice) if _rp else None

    os.makedirs("downloads", exist_ok=True)

    # ---------------------------------------------------------------- source
    if _at:
        _aux = await _m.reply_text(f"**🔄 {_gb('pr')}...**")
        _lk = _rp.link if hasattr(_rp, "link") else "Telegram Audio"

        try:
            _ti = _at.title or _at.file_name
        except Exception:
            _ti = "Telegram Audio"
        _du = int(getattr(_at, "duration", 0) or 0)

        try:
            _ext = "ogg" if isinstance(_at, Voice) else _at.file_name.split(".")[-1]
        except Exception:
            _ext = "ogg"
        _fp = os.path.join(os.path.realpath("downloads"), f"{_at.file_unique_id}.{_ext}")

        if not os.path.exists(_fp):
            try:
                await _aux.edit(f"**⬇️ {_gb('d')}...**")
                await _rp.download(file_name=_fp)
            except Exception:
                return await _aux.edit("**❌ Download failed.**")

        _th = _C.START_IMAGE_URL
        _meta = {}
    else:
        if len(_m.command) < 2:
            return await _m.reply_text("**⚠️ Please provide a song name or link.**")

        _qr = " ".join(_m.command[1:])
        _aux = await _m.reply_text(f"**🔄 {_gb('pr')}...**")

        # REMOVED: youtubesearchpython ka VideosSearch block.
        # _dm() khud /youtube endpoint hit karta hai jo already YouTube search
        # karta hai — hum do baar search kar rahe the, 3-15 sec extra latency.
        try:
            _res = await _dm_full(_qr)
        except Exception as _e:
            return await _aux.edit(f"**❌ Error: {_e}**")

        if not _res:
            return await _aux.edit("**❌ Song not found.**")

        _fp = _res["path"]
        _ti = _res["title"]
        _du = _res["duration"]
        _lk = _res["link"]
        _th = _res["thumbnail"]
        _meta = _res

    # ------------------------------------------------- thumbnail (stream se pehle)
    try:
        await _aux.edit("**🎨 Generating Thumbnail...**")
    except Exception:
        pass
    _th = await _build_thumb(_th, _ti, _du, _rb, _bot_name, _meta)
    _gen_thumb = _th if str(_th).startswith("downloads") else None

    # ------------------------------------------------------------ mediastream
    # ffmpeg reconnect flags yahan NAHI chahiye — _dm() file ko local disk par
    # download karta hai, live HTTP stream nahi hai.
    _ms = MediaStream(
        media_path=_fp,
        video_flags=MediaStream.Flags.IGNORE,
        audio_parameters=_audio_params(),
    )
    _st = "Audio"

    # ------------------------------------------------------------------ join
    if _cid not in _q:
        try:
            try:
                await _c1.join_vc(_cid, _ms)
            except NoActiveGroupCall:
                try:
                    _peer = await _b1.resolve_peer(_cid)
                    await _b1.invoke(
                        CreateGroupCall(peer=_peer, random_id=random.randint(10000, 999999999))
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
                        except Exception:
                            return await _aux.edit("**⚠️ Failed to invite Assistant.**")
                    except errors.ChatAdminRequired:
                        return await _aux.edit(
                            "**⚠️ Make me admin so I can auto-start Voice Chats!**"
                        )

                    try:
                        await _c1.join_vc(_cid, _ms)
                    except NoActiveGroupCall:
                        return await _aux.edit(
                            "**❌ Could not start the Voice Chat. Please start it manually.**"
                        )
                except Exception as _e:
                    return await _aux.edit(f"**❌ Error: {_e}**")
            except TelegramServerError:
                return await _aux.edit("⚠️ **Telegram Server Error.**")
        except Exception as _e:
            return await _aux.edit(f"❌ **Stream failed.**\n\n`{_e}`")

    # ----------------------------------------------------------------- queue
    _pos = await _atq(_cid, _ms, _ti, _du, _lk, _th, _st, _cn, _cl, _rb, _meta)

    _meta.setdefault("title", _ti)
    _meta.setdefault("duration", _du)
    _meta.setdefault("link", _lk)

    # PURANI caption mein "{_C._e} {_gb('p')}" se "Alice Alice Now Playing"
    # duplicate ho raha tha, aur "{_C._f}" footer add karta tha.
    # Ab dono captions helpers/captions.py se aati hain.
    _cap = now_playing(_meta, _rb) if _pos == 0 else queued(_meta, _rb, _pos)

    _btn = InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Close", callback_data="alice_close")]])

    try:
        await _aux.delete()
    except Exception:
        pass

    try:
        await _m.reply_photo(photo=_th, caption=_cap,
                             parse_mode=ParseMode.HTML, reply_markup=_btn)
    except Exception as _e:
        print(f"Failed to send thumbnail: {_e}")
        await _m.reply_photo(photo=_C.START_IMAGE_URL, caption=_cap,
                             parse_mode=ParseMode.HTML, reply_markup=_btn)

    if _cid != _C.LOG_GROUP_ID:
        try:
            await _c.send_photo(_C.LOG_GROUP_ID, photo=_th, caption=_cap,
                                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    await _inc_played(_uid)

    if _pos == 0:
        await _aac_fn(_cid, _st)

    # generated thumbnail ab bhej di gayi hai -> disk se hata do
    # (har play ek 1280x720 PNG banata hai; warna downloads/ bharta rehta hai)
    if _gen_thumb and os.path.exists(_gen_thumb):
        try:
            os.remove(_gen_thumb)
        except OSError:
            pass

    await _asc(_cid)