from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import _C, HELP_DICT  # Imports your empty dictionary from config
from core.clients import _b1

@_b1.on_callback_query(filters.regex("alice_home"))
async def _ahom(_c: Client, _q: CallbackQuery):
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
    
    await _q.message.edit_text(text=_cap, reply_markup=_btn)
    await _q.answer()

@_b1.on_callback_query(filters.regex("alice_help"))
async def _ahc(_c: Client, _q: CallbackQuery):
    bot_name = _c.me.first_name if _c.me else "Music Bot"
    
    _cap = f"**🎵 {bot_name} Help Menu**\n\nChoose a category below to view its commands:"
    
    keyboard = []
    row = []
    
    # Automatically builds buttons for every plugin you register in HELP_DICT
    for category_name in HELP_DICT.keys():
        row.append(InlineKeyboardButton(category_name, callback_data=f"hcat_{category_name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🔙 Back to Home", callback_data="alice_home")])
    
    await _q.message.edit_text(text=_cap, reply_markup=InlineKeyboardMarkup(keyboard))
    await _q.answer()

@_b1.on_callback_query(filters.regex(r"^hcat_(.*)"))
async def _hcat(_c: Client, _q: CallbackQuery):
    # Extracts the category name (like "▶️ Play") from the button click
    category = _q.matches[0].group(1)
    
    if category in HELP_DICT:
        text = f"**{category} Commands**\n\n{HELP_DICT[category]}"
        
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Help", callback_data="alice_help")]
        ])
        
        await _q.message.edit_text(text=text, reply_markup=btn)
    await _q.answer()

@_b1.on_callback_query(filters.regex("alice_privacy"))
async def _privacy_callback(client: Client, query: CallbackQuery):
    bot_name = client.me.first_name if client.me else "Music Bot"
    
    privacy_text = f"""**🔒 Privacy Policy for {bot_name}**

To provide a seamless music streaming experience, we only collect the minimum data required:

**1. User Identification:**
We store your Telegram User ID and First Name solely to identify who requested a song and to manage active queues.

**2. Music Queue Data:**
We temporarily process the name of the song currently playing and the total number of songs played to manage the voice chat. 

**3. No Message Logging:**
We **do not** read, store, or log your personal messages or group chats. The bot only listens for its specific command prefixes.

**4. Data Sharing:**
Your data is never shared with or sold to third parties.

By using this bot, you agree to these terms."""

    back_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="alice_home")]
    ])

    await query.message.edit_text(text=privacy_text, reply_markup=back_btn)
    await query.answer()

@_b1.on_callback_query(filters.regex("alice_close"))
async def _acl(_c: Client, _q: CallbackQuery):
    bot_name = _c.me.first_name if _c.me else "Music Bot"
    try:
        await _q.message.delete()
    except:
        pass
    await _q.answer(f"✨ {bot_name} says goodbye!")