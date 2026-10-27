"""Text-first Telegram panels: uploads and database work cannot block readiness."""
import asyncio
import logging
from pyrogram.enums import ParseMode
from pyrogram.types import InputMediaPhoto
from helpers.panel_upload import upload_photo

log = logging.getLogger(__name__)
_pending = set()
_photo_ids = {}
_decorations = {}


def spawn(coroutine):
    task = asyncio.create_task(coroutine)
    _pending.add(task)
    def finished(done):
        _pending.discard(done)
        if not done.cancelled():
            error = done.exception()
            if error:
                log.warning('Background notification failed (%s)', type(error).__name__)
    task.add_done_callback(finished)
    return task


async def bounded(coroutine, seconds=10):
    # wait_for waits for cancellation cleanup; a stalled media session can keep
    # that cleanup blocked. Retain the task but return at our actual deadline.
    task = spawn(coroutine)
    try:
        done, _ = await asyncio.wait({task}, timeout=seconds)
    except asyncio.CancelledError:
        task.cancel()
        raise
    if not done:
        task.cancel()
        raise asyncio.TimeoutError
    return task.result()


async def decorate(message, text, buttons, image):
    stage = 'upload'
    try:
        file_id = _photo_ids.get(image)
        if not file_id:
            file_id = await bounded(upload_photo(message._client, message.chat.id, image), 60)
            _photo_ids[image] = file_id
        stage = 'attach'
        updated = await bounded(message.edit_media(
            InputMediaPhoto(file_id, caption=text, parse_mode=ParseMode.HTML),
            reply_markup=buttons,
        ), 20)
        if updated and updated.photo:
            _photo_ids[image] = updated.photo.file_id
        log.info('Panel artwork delivered · %s', image)
    except Exception as exc:
        # Expired/invalid file references must not poison later attempts.
        if type(exc).__name__ in ('FileReferenceExpired', 'FileReferenceInvalid', 'MediaEmpty'):
            _photo_ids.pop(image, None)
        log.warning('Panel artwork %s failed · %s (%s); text panel remains usable',
                    stage, image, type(exc).__name__)


def _message_key(message):
    return (message.chat.id, message.id)


def cancel_decoration(message):
    task = _decorations.pop(_message_key(message), None)
    if task:
        task.cancel()


def schedule_decoration(message, text, buttons, image):
    cancel_decoration(message)
    key = _message_key(message)
    task = spawn(decorate(message, text, buttons, image))
    _decorations[key] = task
    def finished(done):
        if _decorations.get(key) is done:
            _decorations.pop(key, None)
    task.add_done_callback(finished)
    return task


async def send_panel(client, chat_id, text, buttons=None, image='assets/alice-start-v2.png'):
    message = await bounded(client.send_message(chat_id, text, parse_mode=ParseMode.HTML, reply_markup=buttons), 10)
    log.info('Telegram panel delivered')
    schedule_decoration(message, text, buttons, image)
    return message


async def save_later(coroutine):
    try:
        await bounded(coroutine, 5)
    except Exception as exc:
        log.warning('Optional bookkeeping unavailable (%s)', type(exc).__name__)


async def close_notifications():
    tasks = list(_pending)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.wait(tasks, timeout=1)
