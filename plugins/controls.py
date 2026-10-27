import random
from html import escape
from helpers.style import card
from helpers.identity import is_owner, owner_note
from pyrogram import filters
from pyrogram.enums import ParseMode
from core.clients import bot, voice
from helpers.queue import queues, stop_playback, chat_locks, repeat_modes
from helpers.player import advance, is_dj, queue_text

async def action(client, chat_id, user, command, args):
    if command in ('queue', 'now'):
        return queue_text(chat_id) if command == 'queue' else (f"Now playing: {queues[chat_id][0]['title']}" if queues.get(chat_id) else 'Nothing is playing.')
    if not await is_dj(client, chat_id, user):
        return 'Only group admins can change playback or edit the queue.'
    async with chat_locks[chat_id]:
        if command in ('stop', 'end'):
            await stop_playback(chat_id)
            return '◇ Session closed. Playback and pending requests cleared.'
        queue = queues.get(chat_id)
        if not queue:
            return 'Nothing is playing. Use /play first.'
        if command == 'pause':
            await voice.pause_stream(chat_id)
            return 'Playback paused.'
        if command == 'resume':
            await voice.resume_stream(chat_id)
            return 'Playback resumed.'
        if command in ('skip', 'next'):
            await advance(chat_id, manual=True)
            return 'Skipped.'
        if command == 'shuffle':
            upcoming = queue[1:]
            random.shuffle(upcoming)
            queue[1:] = upcoming
            return 'Upcoming tracks shuffled.'
        if command == 'clearqueue':
            del queue[1:]
            return 'Upcoming tracks cleared.'
        if command == 'repeat':
            if len(args) != 1 or args[0] not in ('off', 'one', 'all'):
                return 'Usage: /repeat off|one|all'
            repeat_modes[chat_id] = args[0]
            return f'Repeat: {args[0]}'
        try:
            positions = [int(a) for a in args]
            if len(positions) != (2 if command == 'move' else 1):
                raise ValueError
            if any(p < 1 or p >= len(queue) for p in positions):
                raise ValueError
        except ValueError:
            return 'Use valid upcoming queue positions: /remove 2 or /move 3 1'
        item = queue.pop(positions[0])
        if command == 'move':
            queue.insert(positions[1], item)
            return 'Queue reordered.'
        return f'Removed: {item["title"]}'

@bot.on_message(filters.command(['pause','resume','skip','next','stop','end','queue','now','shuffle','repeat','remove','move','clearqueue']) & filters.group)
async def player_command(client, message):
    try:
        text = await action(client, message.chat.id, message.from_user, message.command[0].lower(), message.command[1:])
    except Exception:
        text = 'Unable to update playback. Check the voice chat and bot permissions.'
    await message.reply_text(card('At your service, Rishabh' if is_owner(message.from_user) else 'The listening room', '<blockquote>' + escape(text[:3200]) + '</blockquote>', owner_note(message.from_user)), parse_mode=ParseMode.HTML)

@bot.on_callback_query(filters.regex(r'^music_(pause|resume|skip|stop|queue)$'))
async def player_button(client, query):
    if not query.message:
        return await query.answer('This control is unavailable.', show_alert=True)
    await query.answer()
    try:
        text = await action(client, query.message.chat.id, query.from_user, query.data[6:], [])
    except Exception:
        text = 'Unable to update playback. Check the voice chat and bot permissions.'
    await query.message.reply_text(card('At your service, Rishabh' if is_owner(query.from_user) else 'The listening room', '<blockquote>' + escape(text[:3200]) + '</blockquote>', owner_note(query.from_user)), parse_mode=ParseMode.HTML)
