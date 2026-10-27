"""Expiring search choices scoped to the requesting user and chat."""
from html import escape
from helpers.style import card
from helpers.identity import is_owner
import secrets
import time
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.clients import bot
from helpers.api import provider
from helpers.catalog import MusicError
from plugins.play import play_request

choices = {}

@bot.on_message(filters.command('search') & filters.group)
async def search(client, message):
    if not message.from_user or len(message.command) < 2:
        return await message.reply_text('Use /search <song or artist>.')
    try:
        tracks = await provider.search(' '.join(message.command[1:]), 5)
    except MusicError as exc:
        return await message.reply_text(str(exc), parse_mode=ParseMode.DISABLED)
    if not tracks:
        return await message.reply_text('No songs found. Try adding the artist name.')
    now = time.monotonic()
    for key in list(choices):
        if choices[key]['expires'] < now:
            del choices[key]
    while len(choices) >= 100:
        choices.pop(next(iter(choices)))
    token = secrets.token_hex(6)
    choices[token] = dict(tracks=tracks, user=message.from_user.id, chat=message.chat.id, expires=now + 300)
    lines = []
    buttons = []
    for index, track in enumerate(tracks):
        lines.append(f"<b>{index+1:02d} · {escape(track['title'][:100])}</b>\n{escape(track['artist'][:80])} · {track['duration']//60}:{track['duration']%60:02d}")
        buttons.append([InlineKeyboardButton(f"{index+1}. {track['title'][:50]}", callback_data=f'music_pick:{token}:{index}')])
    await message.reply_text(card('Rishabh’s record collection' if is_owner(message.from_user) else 'Find your next favourite', '\n\n'.join(lines), '<i>Your selection stays open for five minutes.</i>'), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex(r'^music_pick:([a-f0-9]{12}):([0-4])$'))
async def pick(client, query):
    _, token, index = query.data.split(':')
    choice = choices.get(token)
    if not choice or choice['expires'] < time.monotonic():
        return await query.answer('Search expired. Use /search again.', show_alert=True)
    if not query.message or choice['user'] != query.from_user.id or choice['chat'] != query.message.chat.id:
        return await query.answer('Run your own /search to choose a song.', show_alert=True)
    choices.pop(token, None)
    await query.answer('♛ Your selection, Rishabh. Preparing it now…' if is_owner(query.from_user) else 'Preparing your song…')
    await play_request(client, query.message, query='track:' + choice['tracks'][int(index)]['id'], requester=query.from_user)
