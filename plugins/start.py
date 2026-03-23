from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import _C
from core.clients import _b1
from database.users import _asu
from database.chats import _asc

@_b1.on_message(filters.command(["start"], ["/"]) & filters.private)
async def _sp(_c, _m):
    _uid = _m.from_user.id
    _fn = _m.from_user.first_name
    
    # Track User in DB
    await _asu(_uid, _fn)
    
    bot_name = _c.me.first_name if _c.me else "Music Bot"
    
    _cap = f"""**✨ Hello, I'm {bot_name}! ✨**

🎵 **Your personal music streaming assistant!**

I can play high-quality audio and video in your Telegram voice chats with crystal-clear sound quality.

**🎭 Features:**
• ⚡ Lightning-fast streaming
• 🎭 Zero lag playback  
• 📝 Queue management
• 🔄 24/7 availability

╭─────────────────╮
│ **📌 Version:** {_C._v}
╰─────────────────╯"""
    
    _btn = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"➕ Add {bot_name}", url=f"https://t.me/{_b1.username}?startgroup=true")],
        [
            InlineKeyboardButton("Privacy Policy", callback_data="alice_privacy"), 
            InlineKeyboardButton("Repo", url="https://github.com/thanosbots/Alice")                 
        ],
        [
            InlineKeyboardButton("Support", url=_C.SUPPORT_GROUP),         
            InlineKeyboardButton("Updates", url=_C.SUPPORT_CHANNEL)        
        ],
        [
            InlineKeyboardButton("Help", callback_data="alice_help")    
        ]
    ])
    
    await _m.reply_photo(_C.START_IMAGE_URL, caption=_cap, reply_markup=_btn)
    
    # Log details to Log Group
    full_name = f"{_fn} {(_m.from_user.last_name or '')}"
    _un = f"@{_m.from_user.username}" if _m.from_user.username else "N/A"
    
    await _c.send_message(
        _C.LOG_GROUP_ID,
        text=f"**🎵 {bot_name} New User**\n\n**👤 Name:** {full_name}\n**🔗 Username:** {_un}\n**🆔 ID:** `{_uid}`"
    )

@_b1.on_message(filters.new_chat_members)
async def _ba(_c, _m):
    # Track when the bot is added to a new group
    if any(m.id == _b1.id for m in _m.new_chat_members):
        _cid = _m.chat.id
        await _asc(_cid) # Save group to DB
        
        bot_name = _c.me.first_name if _c.me else "Music Bot"
        
        _cap = f"""**✨ Hello, I'm {bot_name}! ✨**

🎵 Thank you for adding me to **{_m.chat.title}**!

I'm here to bring premium music streaming to your voice chat.

**🎭 Quick Commands:**
• `/play` - Play audio
• `/vplay` - Play video  
• `/pause` | `/resume` | `/skip`
• `/end` - Stop playback

**Tip:** Make me **Admin** so I can start voice chats automatically! 🎶"""
        
        _btn = InlineKeyboardMarkup([[InlineKeyboardButton("Help Menu", callback_data="alice_help")]])
        await _m.reply_text(text=_cap, reply_markup=_btn)

@_b1.on_callback_query(filters.regex("alice_privacy"))
async def _privacy_callback(client: Client, query: CallbackQuery):
    bot_name = client.me.first_name if client.me else "Music Bot"
    
    privacy_text = f"""**🔒 Privacy Policy for {bot_name}**

We keep it simple:
1. **IDs:** We store User and Group IDs to manage music and track stats.
2. **Names:** We store names to show who requested a song.
3. **Safety:** We do **not** log your messages or share data with anyone.

By using me, you agree to these terms."""

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="alice_home")]])
    await query.message.edit_text(text=privacy_text, reply_markup=back_btn)
    await query.answer()