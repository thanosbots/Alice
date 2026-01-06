from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import _C
from core.clients import _b1, _s
from database.users import _gsu
from database.chats import _gsc
from helpers.queue import _aac, _avc
from helpers.utils import _gu

@_b1.on_message(filters.command(["stats"], ["/"]) & _s)
async def _bst(_c, _m):
    try:
        await _m.delete()
    except:
        pass
    
    _up = _gu()
    _ac = len(_aac)
    _vc = len(_avc)
    _tc = len(await _gsc())
    _tu = len(await _gsu())
    
    _cap = f"""**🎵 {_C._fn} Analytics**

╭─────────────────────╮
│ **📊 Performance**
╰─────────────────────╯

**⏱ Uptime:** `{_up}`
**🔈 Audio Streams:** `{_ac}`
**🎥 Video Streams:** `{_vc}`
**👥 Total Groups:** `{_tc}`
**👤 Total Users:** `{_tu}`

╭─────────────────────╮
│ **🎭 Bot Info**
╰─────────────────────╯

**🤖 Name:** {_C._fn}
**📌 Version:** {_C._v}

{_C._f}"""
    
    _btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="alice_stats"),
            InlineKeyboardButton("✖️ Close", callback_data="alice_close")
        ]
    ])
    
    await _m.reply_text(_cap, reply_markup=_btn)
