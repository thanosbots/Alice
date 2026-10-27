"""Alice Music Bot · Created by Rishabh Anand."""
import asyncio
import logging
import os
import shutil
from pyrogram import idle
from config import Config
from core.clients import bot, assistant, voice
from core.decorators import register_voice_handlers
from helpers.api import close_catalog
from helpers.terminal import banner, configure_logging
from helpers.artwork import close_artwork
from helpers.style import card
from helpers import updater
from helpers.notifications import send_panel, spawn, close_notifications
from helpers.version import BOT_NAME, VERSION

configure_logging()
log = logging.getLogger('Alice')

async def startup_notice():
    text = card('The listening room is open',
        '<blockquote>ALICE · Music atelier\nCreated by Rishabh Anand</blockquote>\n'
        f'<b>Version</b> · {VERSION}\n'
        '<b>Bot</b> · Connected\n<b>Assistant</b> · Connected\n<b>Voice engine</b> · Ready\n\n'
        '♛ Rishabh, your room is ready for its next record.',
        '<i>Audio · 48 kHz stereo</i>')
    if not Config.LOG_GROUP_ID:
        log.warning('No LOG_GROUP_ID configured; startup notice skipped')
        return
    log.info('Sending startup confirmation to the configured log group…')
    try:
        await send_panel(bot, Config.LOG_GROUP_ID, text)
        log.info('Startup confirmation delivered to log group')
    except Exception as exc:
        log.warning('Startup notice failed (%s). Check LOG_GROUP_ID, bot membership and send permissions.', type(exc).__name__)


async def run_bot():
    banner(BOT_NAME, VERSION)
    if not all(shutil.which(tool) for tool in ('ffmpeg', 'ffprobe')):
        raise RuntimeError('FFmpeg and FFprobe are required before starting the bot.')
    for directory in ('cache', 'downloads', 'alice_cache'):
        os.makedirs(directory, exist_ok=True)
    bot_started = assistant_started = False
    try:
        log.info('Connecting Telegram bot…')
        await bot.start()
        bot_started = True
        log.info('Bot connected · Rishabh Anand’s Alice')
        log.info('Connecting assistant…')
        await assistant.start()
        assistant_started = True
        log.info('Assistant connected')
        log.info('Preparing voice engine…')
        await voice.start()
        await register_voice_handlers(voice)
        banner(BOT_NAME, VERSION, ready=True)
        log.info('All systems ready · Creator: Rishabh Anand')
        spawn(startup_notice())
        log.info('Command listener active · /start works in groups and private chat')
        idle_task = asyncio.create_task(idle())
        restart_task = asyncio.create_task(updater.restart_requested.wait())
        try:
            await asyncio.wait({idle_task, restart_task}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in (idle_task, restart_task):
                task.cancel()
            await asyncio.gather(idle_task, restart_task, return_exceptions=True)
    except Exception:
        log.exception('Alice could not complete this session')
        raise
    finally:
        log.info('Closing the listening room…')
        # Attempt every cleanup even if one component fails.
        for label, closer in (
            ('Notifications', close_notifications), ('Artwork', close_artwork), ('Catalog', close_catalog), ('Voice', voice.stop),
            ('Assistant', assistant.stop if assistant_started else None),
            ('Bot', bot.stop if bot_started else None),
        ):
            if closer:
                try:
                    if updater.restart_requested.is_set():
                        cleanup = asyncio.create_task(closer())
                        done, _ = await asyncio.wait({cleanup}, timeout=15)
                        if not done:
                            cleanup.cancel()
                            log.warning('%s cleanup timed out during update restart', label)
                        else:
                            cleanup.result()
                    else:
                        await closer()
                except Exception:
                    log.warning('%s cleanup could not finish', label)
        log.info('Session closed · Until the next record, Rishabh')

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run_bot())
    if updater.restart_requested.is_set() and updater.restart_python:
        os.execv(updater.restart_python, [updater.restart_python, str(updater.ROOT / 'main.py')])
