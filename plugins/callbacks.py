from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import _C
from core.clients import _b1
from core._0x1a2b import _gb, _gm

@_b1.on_callback_query(filters.regex("alice_help"))
async def _ahc(_c, _q):
    _cap = f"""**🎵 {_C._fn} Commands**

╭──────────────────────╮
│ **🎶 Music Commands**
╰──────────────────────╯

`/play` [song name/link] - Play audio
`/vplay` [video name/link] - Play video
`/pause` - Pause stream
`/resume` - Resume stream
`/skip` - Skip track
`/end` - Stop & leave

╭──────────────────────╮
│ **✨ About {_C._n}**
╰──────────────────────╯

{_C._fn} is a premium music streaming bot with cutting-edge features!

**{_gm('m1')}**

{_C._f}"""
    
    _btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back", callback_data="alice_home"),
            InlineKeyboardButton("👨‍💻 Dev", url=f"https://t.me/{_C._du}")
        ]
    ])
    
    await _q.message.edit(text=_cap, reply_markup=_btn)
    await _q.answer()

@_b1.on_callback_query(filters.regex("alice_home"))
async def _ahom(_c, _q):
    _mn = _q.from_user.mention
    _gr = _gb('g')
    _m1 = _gm('m1')
    
    _cap = f"""**{_C._e} {_gr}, {_mn}! {_C._e}**

🎵 **{_m1}**

I bring high-quality music to your Telegram voice chats with features like:

• ⚡ Lightning-fast streaming
• 🎭 Queue management
• 🎵 HD audio quality
• 📹 Video playback
• 🔄 24/7 availability

{_C._f}"""
    
    _btn = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"➕ Add {_C._n}", url=f"https://t.me/{_b1.username}?startgroup=true")],
        [
            InlineKeyboardButton("📜 Commands", callback_data="alice_help"),
            InlineKeyboardButton("👨‍💻 Dev", url=f"https://t.me/{_C._du}")
        ]
    ])
    
    await _q.message.edit(text=_cap, reply_markup=_btn)
    await _q.answer()

@_b1.on_callback_query(filters.regex("alice_close"))
async def _acl(_c, _q):
    try:
        await _q.message.delete()
    except:
        pass
    await _q.answer(f"{_C._e} {_C._n} says goodbye!")
