"""Prepare requests without holding the voice-control lock."""
import asyncio
import logging
import random
from pathlib import Path
from pyrogram import filters, errors
from pyrogram.enums import ParseMode
from pyrogram.raw.functions.phone import CreateGroupCall
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import MediaStream, AudioQuality
from config import Config
from core.clients import bot, assistant, voice
from database.chats import save_chat
from database.users import increment_play_count, save_user
from helpers.api import resolve_audio
from helpers.catalog import MusicError
from helpers.media import validate_audio
from helpers.player import controls
from helpers.style import track_card
from helpers.identity import is_owner, selection_name
from helpers.artwork import artwork_for, background_notice
from helpers.queue import enqueue, mark_active, queues, chat_locks, request_locks, request_versions

log = logging.getLogger(__name__)

@bot.on_message(filters.command('play') & filters.group)
async def play_command(client, message):
    await play_request(client, message)

async def play_request(client, message, query=None, requester=None):
    chat_id = message.chat.id
    version = request_versions[chat_id]
    # Preserve request order without delaying pause, skip, stop or stream-end events.
    async with request_locks[chat_id]:
        if version != request_versions[chat_id]:
            return
        await prepare_request(client, message, query, requester, version)

async def prepare_request(client, message, query, requester, version):
    chat_id = message.chat.id
    user = requester or message.from_user
    if not user:
        return await message.reply_text('Send /play from your personal account.')
    if len(queues.get(chat_id, [])) >= Config.MAX_QUEUE_SIZE:
        return await message.reply_text('The queue is full. Remove a song or wait for a free place.')
    reply = message.reply_to_message if query is None else None
    attachment = (reply.audio or reply.voice) if reply else None
    if not attachment and query is None and len(message.command) < 2:
        return await message.reply_text('◇ Set the mood\n\n/play song name\nOr reply to an audio file with /play.')
    status = await message.reply_text('♛ Welcome, Rishabh Anand. Preparing your selection…' if is_owner(user) else '◇ Finding your sound…')
    try:
        if attachment:
            if (attachment.file_size or 0) > Config.MAX_DOWNLOAD_MB * 1024 * 1024 or (attachment.duration or 0) > Config.MAX_TRACK_MINUTES * 60:
                raise MusicError('Choose a smaller or shorter audio file.')
            directory = Path('downloads')
            directory.mkdir(exist_ok=True)
            path = directory / f'telegram_{attachment.file_unique_id}.audio'
            # Per-message unique partial names and atomic publication avoid incomplete cache hits.
            if not path.exists():
                temporary = path.with_suffix(f'.{chat_id}.{message.id}.part')
                try:
                    downloaded = await reply.download(file_name=str(temporary.resolve()))
                    if not downloaded or not temporary.exists():
                        raise MusicError('Audio download did not complete. Please try again.')
                    if temporary.stat().st_size > Config.MAX_DOWNLOAD_MB * 1024 * 1024:
                        raise MusicError('This audio exceeds the download size limit.')
                    await validate_audio(temporary, Config.MAX_TRACK_MINUTES * 60)
                    temporary.replace(path)
                finally:
                    temporary.unlink(missing_ok=True)
            try:
                await validate_audio(path, Config.MAX_TRACK_MINUTES * 60)
            except MusicError:
                path.unlink(missing_ok=True)
                raise
            title = getattr(attachment, 'title', None) or getattr(attachment, 'file_name', None) or 'Your audio'
            seconds = attachment.duration or 0
            duration = f'{seconds // 60}:{seconds % 60:02d}'
            link, thumbnail = '', 'assets/lounge.jpg'
        else:
            path, title, duration, link, thumbnail = await resolve_audio(query or ' '.join(message.command[1:]))
        stream = MediaStream(str(path), video_flags=MediaStream.Flags.IGNORE, audio_parameters=AudioQuality.HIGH)
        async with chat_locks[chat_id]:
            if version != request_versions[chat_id]:
                return await status.edit('◇ Request cancelled. The session was stopped.')
            if len(queues.get(chat_id, [])) >= Config.MAX_QUEUE_SIZE:
                return await status.edit('The queue is full.')
            if not queues.get(chat_id):
                # Ensure the assistant is in the group before the first join attempt.
                try:
                    await assistant.get_chat_member(chat_id, assistant.id)
                except errors.UserNotParticipant:
                    invite = message.chat.username or await client.export_chat_invite_link(chat_id)
                    await assistant.join_chat(invite)
                try:
                    await voice.join_vc(chat_id, stream)
                except NoActiveGroupCall:
                    await client.invoke(CreateGroupCall(peer=await client.resolve_peer(chat_id), random_id=random.randint(1, 2**31-1)))
                    await voice.join_vc(chat_id, stream)
            requested_by = selection_name(user)
            position = await enqueue(chat_id, stream, title, duration, link, thumbnail, 'Audio', message.chat.title, '', requested_by)
            track = queues[chat_id][-1]
            track['is_owner'] = is_owner(user)
            if track['is_owner']:
                log.info('Creator selection · Rishabh Anand · %s', 'Playing' if position == 0 else 'Queued')
            thumbs = getattr(attachment, 'thumbs', None) if attachment else None
            if thumbs:
                track['telegram_thumbnail'] = thumbs[-1].file_id
            if position == 0:
                await mark_active(chat_id, 'Audio')
    except MusicError as exc:
        return await status.edit(str(exc), parse_mode=ParseMode.DISABLED)
    except Exception:
        log.warning('Could not prepare or start audio in chat %s', chat_id)
        return await status.edit('Unable to start this song. Open a voice chat, allow the assistant to join and speak, then try /play again.')

    # The next request and voice controls do not wait for cover downloads/rendering.
    background_notice(play_notice(client, message, status, track))
    try:
        await save_user(user.id, user.first_name)
        await increment_play_count(user.id)
        await save_chat(chat_id)
    except Exception:
        log.warning('Playback started; statistics could not be saved')


async def play_notice(client, message, status, track):
    temporary = None
    try:
        if track.get('telegram_thumbnail'):
            import uuid
            temporary = Path('downloads') / f'cover_{uuid.uuid4().hex}.jpg'
            try:
                await asyncio.wait_for(client.download_media(track['telegram_thumbnail'], file_name=str(temporary.resolve())), 5)
                if temporary.exists():
                    track['thumbnail'] = str(temporary.resolve())
            except Exception:
                pass
        artwork = await artwork_for(track)
        track['artwork_path'] = artwork
        queue = queues.get(message.chat.id, [])
        position = next((i for i, item in enumerate(queue) if item['media_stream'] is track['media_stream']), None)
        # An old preparation notice must not claim that a stopped/skipped song is playing.
        if position is None:
            try:
                await status.delete()
            except Exception:
                pass
            return
        caption = track_card(track, position)
        try:
            await message.reply_photo(artwork, caption=caption, parse_mode=ParseMode.HTML, reply_markup=controls())
            await status.delete()
        except Exception:
            await status.edit(caption, parse_mode=ParseMode.HTML, reply_markup=controls())
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
