"""Private, owner-only sanitized runtime logs."""
import asyncio
from io import BytesIO
from pyrogram import filters
from pyrogram.enums import ParseMode
from core.clients import bot
from config import Config
from helpers.access import private_owner
from helpers.diagnostics import log_snapshot


@bot.on_message(filters.command('logs') & filters.user(Config.OWNER_ID) & filters.private)
async def logs_command(client, message):
    if not private_owner(message.from_user, message.chat, Config.OWNER_ID):
        return
    args = message.command[1:]
    if len(args) > 1 or (args and (not args[0].isdigit() or not 1 <= int(args[0]) <= 500)):
        return await message.reply_text('Use /logs or /logs 200 (1–500 lines).')
    try:
        text = await asyncio.to_thread(log_snapshot, int(args[0]) if args else 100)
    except OSError:
        return await message.reply_text('Could not read the log file. Check its permissions.')
    if len(text.encode('utf-16-le')) <= 7000:
        await message.reply_text(text, parse_mode=ParseMode.DISABLED, disable_web_page_preview=True)
    else:
        document = BytesIO(text.encode('utf-8'))
        document.name = 'alice-diagnostics.txt'
        await message.reply_document(document, caption='Recent logs with known credentials redacted.')
