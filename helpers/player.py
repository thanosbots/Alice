"""Shared playback transitions and controls."""
import logging
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from core.clients import bot, voice
from helpers.style import track_card
from helpers.artwork import artwork_for, background_notice
from helpers.queue import queues, stop_playback, mark_active, advance_queue

log = logging.getLogger(__name__)


def controls():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ⅱ Pause", callback_data="music_pause"), InlineKeyboardButton("▷ Resume", callback_data="music_resume"), InlineKeyboardButton("› Skip", callback_data="music_skip")],
        [InlineKeyboardButton("≡ Queue", callback_data="music_queue"), InlineKeyboardButton("□ Stop", callback_data="music_stop")],
    ])


async def is_dj(client, chat_id, user):
    if not user:
        return False
    if user.id == Config.OWNER_ID:
        return True
    member = await client.get_chat_member(chat_id, user.id)
    return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)


async def announce(chat_id, track):
    artwork = track.get('artwork_path') or await artwork_for(track)
    queue = queues.get(chat_id, [])
    if not queue or queue[0]['media_stream'] is not track['media_stream']:
        return
    track['artwork_path'] = artwork
    caption = track_card(track)
    try:
        await bot.send_photo(chat_id, artwork, caption=caption, parse_mode=ParseMode.HTML, reply_markup=controls())
    except Exception:
        await bot.send_message(chat_id, caption, parse_mode=ParseMode.HTML, reply_markup=controls())


async def advance(chat_id, manual=False):
    """Caller holds the chat lock. Failed tracks are discarded, not retried forever."""
    track = advance_queue(chat_id, manual)
    while track:
        try:
            await voice.join_vc(chat_id, track['media_stream'])
        except Exception:
            log.exception("Unable to play next track in chat %s", chat_id)
            queues[chat_id].pop(0)
            track = queues[chat_id][0] if queues[chat_id] else None
            continue
        await mark_active(chat_id, track['stream_type'])
        background_notice(announce(chat_id, track))
        return
    await stop_playback(chat_id)
    await bot.send_message(chat_id, "Queue finished. Left the voice chat.")


def queue_text(chat_id):
    queue = queues.get(chat_id, [])
    if not queue:
        return "The queue is empty. Use /play followed by a song name."
    lines = [f"Now playing: {queue[0]['title']} ({queue[0]['duration']})"]
    lines += [f"{i}. {t['title'][:100]} ({t['duration']})" for i, t in enumerate(queue[1:21], 1)]
    lines.append(f"\n{len(queue)-1} tracks waiting. Use /remove <position> or /move <from> <to>.")
    return "\n".join(lines)
