import logging
from html import escape
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from core.clients import bot
from database.users import save_user
from database.chats import save_chat
from helpers.notifications import send_panel, spawn, save_later
from helpers.identity import is_owner, owner_mention
from helpers.style import home, home_buttons, card

@bot.on_message(filters.command('start'))
async def welcome(client, message):
    name = client.me.first_name if client.me else 'Alice'
    from helpers.access import private_owner
    owner = private_owner(message.from_user, message.chat, Config.OWNER_ID)
    text = home(name, owner=owner)
    buttons = home_buttons(bot.username, Config.SUPPORT_GROUP, owner=owner)
    try:
        await send_panel(client, message.chat.id, text, buttons, image='assets/alice-start-v2.png')
    except Exception as exc:
        logging.getLogger(__name__).warning('Welcome could not be delivered (%s)', type(exc).__name__)
        return
    if message.from_user:
        spawn(save_later(save_user(message.from_user.id, message.from_user.first_name)))

@bot.on_message(filters.new_chat_members)
async def added(client, message):
    if any(member.id == bot.id for member in message.new_chat_members):
        spawn(save_later(save_chat(message.chat.id)))
        await message.reply_text(card('Your listening room is open',
            f'<blockquote>Welcome to {escape(message.chat.title or "your group")}.</blockquote>\n'
            'Make me an admin, invite the assistant, and open a voice chat.\n\n'
            '<code>/play song name</code> — set the mood.'), parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◇ Open the guide', callback_data='alice_help')]]))

    elif any(is_owner(member) for member in message.new_chat_members):
        owner = next(member for member in message.new_chat_members if is_owner(member))
        await message.reply_text(card('A special arrival',
            f'<blockquote>Welcome, {owner_mention(owner)}. ♛</blockquote>\n'
            'The creator is in the room. Your next selection sets the mood.'), parse_mode=ParseMode.HTML)
