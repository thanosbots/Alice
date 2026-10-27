"""Upload small panel photos over the bot's existing Telegram connection."""
import hashlib
from pathlib import Path

from pyrogram import raw
from pyrogram.types import Photo

PART_SIZE = 512 * 1024
MAX_SIZE = 10 * 1024 * 1024


async def upload_photo(client, chat_id, image):
    path = Path(image)
    if not 0 < path.stat().st_size <= MAX_SIZE:
        raise ValueError('Panel image must be between 1 byte and 10 MiB')
    # These are small, local static assets. Avoid save_file's separate media
    # session and worker queue, whose cancellation can hold its semaphore.
    data = path.read_bytes()
    file_id = client.rnd_id()
    parts = (len(data) + PART_SIZE - 1) // PART_SIZE
    for part in range(parts):
        accepted = await client.invoke(raw.functions.upload.SaveFilePart(
            file_id=file_id, file_part=part,
            bytes=data[part * PART_SIZE:(part + 1) * PART_SIZE],
        ))
        if not accepted:
            raise RuntimeError('Telegram rejected a panel upload part')
    uploaded = await client.invoke(raw.functions.messages.UploadMedia(
        peer=await client.resolve_peer(chat_id),
        media=raw.types.InputMediaUploadedPhoto(file=raw.types.InputFile(
            id=file_id, parts=parts, name=path.name,
            md5_checksum=hashlib.md5(data).hexdigest(),
        )),
    ))
    photo = Photo._parse(client, uploaded.photo)
    if photo is None:
        raise RuntimeError('Telegram did not return a panel photo')
    return photo.file_id
