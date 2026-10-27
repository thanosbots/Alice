"""Owner-only release checks and one-use confirmation buttons."""
import logging
import secrets
from time import monotonic

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton as Button, InlineKeyboardMarkup as Keyboard

from core.clients import bot
from config import Config
from helpers.access import private_owner
from helpers import updater
from helpers.version import VERSION

log = logging.getLogger(__name__)
_pending = {}
CONFIRM_SECONDS = 600


def clear_pending():
    for offer in _pending.values():
        updater.discard_release(offer['release'])
    _pending.clear()


def failure_text(exc):
    log.warning('Update failed (%s)', type(exc).__name__)
    detail = str(exc) if isinstance(exc, updater.UpdateError) else type(exc).__name__
    return f'Update stopped: {detail}\nThe bot has not restarted. Run /update to try again.'


@bot.on_message(filters.command('update') & filters.user(Config.OWNER_ID) & filters.private)
async def update_command(client, message):
    if not private_owner(message.from_user, message.chat, Config.OWNER_ID):
        return
    if updater.lock.locked() or updater.restart_requested.is_set():
        return await message.reply_text('An update is already running.')
    async with updater.lock:
        clear_pending()
        status = await message.reply_text(f'Current version: {VERSION}\nChecking for a new release…')
        try:
            checked = await updater.check_update()
            if checked.release is None:
                return await status.edit_text(
                    f'You’re up to date.\nCurrent: {VERSION}\nRepository: {checked.latest_version}',
                    parse_mode=ParseMode.DISABLED)
            token = secrets.token_hex(8)
            _pending[token] = dict(release=checked.release, expires=monotonic() + CONFIRM_SECONDS,
                                   chat_id=status.chat.id, message_id=status.id)
            await status.edit_text(
                f'New version available!\n\nCurrent: {VERSION}\nNew: {checked.latest_version}\n'
                f'Release: {checked.release.revision[:12]}\n\n'
                'Confirm to install and restart. Music will stop at restart.\n'
                'Your configuration and sessions stay in place.\nThis confirmation expires in 10 minutes.',
                parse_mode=ParseMode.DISABLED,
                reply_markup=Keyboard([[Button('Confirm update', callback_data=f'alice_update:confirm:{token}'),
                                        Button('Cancel', callback_data=f'alice_update:cancel:{token}')]]))
        except Exception as exc:
            clear_pending()
            await status.edit_text(failure_text(exc), parse_mode=ParseMode.DISABLED)


@bot.on_callback_query(filters.regex(r'^alice_update:(confirm|cancel):([0-9a-f]{16})$'))
async def update_confirmation(client, query):
    if not query.message or not private_owner(query.from_user, query.message.chat, Config.OWNER_ID):
        return await query.answer('Only the owner can confirm an update in private chat.', show_alert=True)
    _, action, token = query.data.split(':')
    offer = _pending.get(token)
    if not offer or (query.message.chat.id, query.message.id) != (offer['chat_id'], offer['message_id']):
        return await query.answer('This confirmation is no longer active. Run /update again.', show_alert=True)
    if updater.lock.locked() or updater.restart_requested.is_set():
        return await query.answer('An update is already running.', show_alert=True)
    async with updater.lock:
        # Consume before the first await; double clicks cannot install twice.
        _pending.pop(token)
        if monotonic() >= offer['expires'] or action == 'cancel':
            updater.discard_release(offer['release'])
            await query.answer()
            text = 'Update cancelled.' if action == 'cancel' else 'Confirmation expired. Run /update again.'
            return await query.message.edit_text(text, reply_markup=None)
        await query.answer('Installing the confirmed release…')
        try:
            await query.message.edit_text('Installing the confirmed release…\nThis can take a few minutes.', reply_markup=None)
            version, interpreter, _ = await updater.install_update(offer['release'])
        except Exception as exc:
            await query.message.edit_text(failure_text(exc), parse_mode=ParseMode.DISABLED, reply_markup=None)
            return
        try:
            await query.message.edit_text(f'Updated to {version}. Restarting now.\nCode backup saved in .updates.',
                                          reply_markup=None)
        finally:
            updater.request_restart(interpreter)
