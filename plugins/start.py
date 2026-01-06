from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import _C
from core.clients import _b1
from core._0x1a2b import _gb, _gm
from database.users import _asu

@_b1.on_message(filters.command(["start"], ["/"]) & filters.private)
async def _sp(_c, _m):
    _uid = _m.from_user.id
    await _asu(_uid)
    
    _mn = _m.from_user.mention
    
    _cap = f"""**{_C._e} {_gb('g')} {_C._e}**

🎵 **{_gm('m1')}**

I can play high-quality audio and video in your Telegram voice chats with crystal-clear sound quality.

**🎭 Features:**
• ⚡ Lightning-fast streaming
• 🎭 Zero lag playback  
• 📝 Queue management
• 🔄 24/7 availability

╭─────────────────╮
│ **📌 Version:** {_C._v}
╰─────────────────╯

{_C._f}"""
    
    _btn = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"➕ Add {_C._n}", url=f"https://t.me/{_b1.username}?startgroup=true")],
        [
            InlineKeyboardButton("📜 Commands", callback_data="alice_help"),
            InlineKeyboardButton("👨‍💻 Dev", url=f"https://t.me/{_C._du}")
        ],
        [
            InlineKeyboardButton("💬 Support", url=_C.SUPPORT_GROUP),
            InlineKeyboardButton("📢 Updates", url=_C.SUPPORT_CHANNEL)
        ]
    ])
    
    await _m.reply_photo(_C.START_IMAGE_URL, caption=_cap, reply_markup=_btn)
    
    _fn = _m.from_user.first_name + " " + (_m.from_user.last_name or "")
    _un = f"@{_m.from_user.username}" if _m.from_user.username else "N/A"
    
    await _c.send_message(
        _C.LOG_GROUP_ID,
        text=f"""**🎵 {_C._n} New User**

**👤 Name:** {_fn}
**🔗 Username:** {_un}
**🆔 ID:** `{_uid}`

{_C._f}"""
    )

@_b1.on_message(filters.new_chat_members)
async def _ba(_c, _m):
    for _mb in _m.new_chat_members:
        if _mb.id == _b1.id:
            from database.chats import _asc
            
            _cid = _m.chat.id
            await _asc(_cid)
            
            _cap = f"""**{_C._e} {_gb('g')} {_C._e}**

🎵 Thank you for adding me to your group!

**{_gm('m2')}**

**🎭 Quick Commands:**
• `/play` [song name] - Play audio
• `/vplay` [video name] - Play video  
• `/pause` - Pause playback
• `/resume` - Resume playback
• `/skip` - Skip to next
• `/end` - Stop and leave

**{_gm('m3')}** 🎶

{_C._f}"""
            
            _btn = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📜 Help", callback_data="alice_help"),
                    InlineKeyboardButton("👨‍💻 Dev", url=f"https://t.me/{_C._du}")
                ]
            ])
            
            await _m.reply_text(text=_cap, reply_markup=_btn)
