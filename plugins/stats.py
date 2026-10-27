from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from core.clients import bot
from database.users import get_user_ids
from database.chats import get_chat_ids
from helpers.queue import active_audio_chats, active_video_chats
from helpers.utils import uptime
from helpers.style import card, edit_panel
from helpers.access import private_owner

async def stats_screen():
    text = card('Rishabh’s observatory',
                f'<blockquote>Uptime · {uptime()}\nAudio rooms · {len(active_audio_chats)}\nVideo rooms · {len(active_video_chats)}</blockquote>\n'
                f'<b>Groups</b> · {len(await get_chat_ids())}\n<b>Listeners</b> · {len(await get_user_ids())}',
                '<i>♛ Rishabh Anand · Private owner desk</i>')
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton('↻ Refresh', callback_data='alice_stats'), InlineKeyboardButton('‹ Guide', callback_data='alice_help')],
    ])
    return text, keyboard

@bot.on_message(filters.command('stats') & filters.user(Config.OWNER_ID) & filters.private)
async def stats_command(client, message):
    text, keyboard = await stats_screen()
    await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

@bot.on_callback_query(filters.regex('^alice_stats$'))
async def stats_refresh(client, query):
    if not query.message or not private_owner(query.from_user, query.message.chat, Config.OWNER_ID):
        return await query.answer('This page is unavailable.', show_alert=True)
    await query.answer()
    text, keyboard = await stats_screen()
    await edit_panel(query.message, text, keyboard)
