"""
events.py — stream-end / call-dead logic.

⚠️  YAHAN AB KOI @on_update DECORATOR NAHI HAI. Jaan-bujh ke.

WAJAH (asli bug):
Pehle ye file khud register karti thi —

    @_c1.vcbot.on_update()
    async def _stream_end_handler(client, update): ...

— aur core/decorators.py ka _sh() bhi register karta tha —

    @_cl.vcbot.on_update(fl.stream_end)
    async def _seh(_, _u): ...

Dono EK HI PyTgCalls instance par lagte the. main.py pehle _b1.start() karta
hai (Pyrogram plugins load karta hai -> pehla handler), phir _sh(_c1) chalata
hai (-> doosra handler). To har stream end par DONO chalte the:

  · _pq() do baar      -> queue se do track pop -> gaane skip ho jaate the
  · join_vc() do baar  -> chalta hua stream restart -> POORE GAANE MEIN STUTTER
  · do captions bheji jaati thin

Upar se bina filter wale handler ko py-tgcalls await nahi karta tha
("coroutine was never awaited"), yaani is file ka code chalta hi nahi tha —
saara kaam purana _seh kar raha tha, apni purani "{_du} Minutes" caption ke
saath. Isiliye caption fix yahan karne ke baad bhi asar nahi dikha.

AB: logic yahan, registration sirf core/decorators.py mein. Ek hi jagah.

Purana _END_EVENTS / _KILL_EVENTS naam-matching bhi hata diya —
"CallEnded", "LeftCall", "KickedFromCall" jaisi koi class py-tgcalls 2.x mein
hai hi nahi, to wo set kabhi match nahi karta tha. Ab pytgcalls ke apne
filters use hote hain (ChatUpdate.Status.LEFT_CALL waghairah).
"""

import asyncio
import logging
import os

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.clients import _b1
from helpers.captions import up_next
from helpers.queue import _cs, _pq, _q, _aac_fn, _get_lock

_l = logging.getLogger("Alice.Events")

# Jab hum khud leave_vc() karte hain, Telegram LEFT_CALL wapas bhejta hai
# -> cleanup() -> _cs() -> leave_vc() -> phir LEFT_CALL -> loop.
# Ye set us cycle ko todta hai.
_CLEANING = set()


async def _release_guard(_cid: int) -> None:
    """Guard ko background mein chhodo — caller ko rokna nahi hai."""
    await asyncio.sleep(2)
    _CLEANING.discard(_cid)


async def cleanup(_cid: int) -> None:
    """
    Call band ho gayi / bot nikaal diya gaya -> sirf cleanup, next song nahi.

    NOTE: pehle yahan `finally` ke andar `await asyncio.sleep(2)` tha, jo
    caller ko poore 2 second rok deta tha — aur advance() us waqt queue ka
    lock pakde hue hota hai. Ab guard background task mein release hota hai.
    """
    if _cid in _CLEANING:
        _l.info(f"cleanup already running for {_cid}, skipping")
        return
    _CLEANING.add(_cid)
    try:
        _l.info(f"cleaning up {_cid}")
        await _cs(_cid)
    finally:
        asyncio.create_task(_release_guard(_cid))


async def advance(_cid: int, _join) -> None:
    """
    Ek track khatam -> queue aage badhao.

    _join: _c1.join_vc yahan pass hota hai. core.clients se _c1 import nahi
    karte kyunki decorators.py already usse hold karta hai.
    """
    # Lock: do end events saath aane par queue do baar pop hoti thi -> skip
    async with _get_lock(_cid):
        await asyncio.sleep(0.5)
        _l.info(f"stream ended in {_cid}, advancing queue")

        await _pq(_cid)                     # khatam hua track hatao
        _qd = _q.get(_cid)

        if not _qd:
            # _cs() khud leave_vc call karta hai — yahan dobara mat karo
            await cleanup(_cid)
            try:
                _name = _b1.me.first_name if _b1.me else "Music Bot"
                await _b1.send_message(
                    _cid,
                    f"<b>✅ Queue empty — {_name} left the voice chat.</b>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
            return

        _item = _qd[0]
        _th = _item.get("thumbnail")

        try:
            await _join(_cid, _item.get("media_stream"))
        except Exception as _e:
            _l.error(f"join_vc failed in {_cid}: {_e}")
            await cleanup(_cid)
            try:
                await _b1.send_message(
                    _cid,
                    "<b>❌ Could not start the next track. Stopping.</b>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
            return

        # queue item se meta banao (artist/genre wahan store hota hai)
        _meta = dict(_item.get("meta") or {})
        _meta.setdefault("title", _item.get("title"))
        _meta.setdefault("duration", _item.get("duration"))
        _meta.setdefault("link", _item.get("link"))

        # Duration ab caption builder format karta hai — "133 Minutes" nahi.
        _cap = up_next(_meta, _item.get("requested_by") or "Someone")

        _btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✖️ Close", callback_data="alice_close")]]
        )

        try:
            await _b1.send_photo(
                chat_id=_cid, photo=_th, caption=_cap,
                parse_mode=ParseMode.HTML, reply_markup=_btn,
            )
        except Exception:
            try:
                await _b1.send_message(
                    chat_id=_cid, text=_cap,
                    parse_mode=ParseMode.HTML, reply_markup=_btn,
                )
            except Exception:
                pass

        # Ab bhej diya -> generated thumbnail disk par pada na rahe
        if _th and str(_th).startswith("downloads") and os.path.exists(_th):
            try:
                os.remove(_th)
            except OSError:
                pass

        await _aac_fn(_cid, _item.get("stream_type"))