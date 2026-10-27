from time import perf_counter

from pyrogram import filters
from pyrogram.enums import ParseMode

from core.clients import bot
from helpers.notifications import bounded
from helpers.style import card, edit_panel
from helpers.utils import uptime
from helpers.version import VERSION


@bot.on_message(filters.command('ping'))
async def ping_command(client, message):
    started = perf_counter()
    reply = await bounded(client.send_message(
        message.chat.id, card('Ping?', 'Checking the signal…'),
        parse_mode=ParseMode.HTML,
    ))
    elapsed_ms = (perf_counter() - started) * 1000
    text = card('PONG!',
                '<blockquote>Loud and clear. I’m here.</blockquote>\n'
                f'<b>Version</b> · {VERSION}\n'
                f'<b>Telegram response</b> · {elapsed_ms:.0f} ms\n'
                f'<b>Uptime</b> · {uptime()}')
    await edit_panel(reply, text, None, image='assets/alice-ping-v2.png')
