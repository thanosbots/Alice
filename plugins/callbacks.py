from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup as Keyboard, InlineKeyboardButton as Button
from config import Config
from core.clients import bot
from helpers.access import private_owner
from helpers.notifications import send_panel, cancel_decoration
from helpers.style import home, home_buttons, help_screen, edit_panel, card

@bot.on_message(filters.command('help'))
async def help_command(client, message):
    text, keyboard = help_screen(owner=private_owner(message.from_user, message.chat, Config.OWNER_ID))
    await send_panel(client, message.chat.id, text, keyboard, image='assets/alice-help-v2.png')

@bot.on_callback_query(filters.regex(r'^(alice_home|alice_help|alice_privacy|guide_\w+|hcat_.*)$'))
async def navigation(client, query):
    if not query.message:
        return await query.answer()
    owner = private_owner(query.from_user, query.message.chat, Config.OWNER_ID)
    data = query.data
    if (data.startswith('guide_owner_') or data.startswith('hcat_')) and not owner:
        return await query.answer('This page is unavailable.', show_alert=True)
    await query.answer()
    if data == 'alice_home':
        text = home(client.me.first_name if client.me else 'Alice', owner=owner)
        keyboard = home_buttons(bot.username, Config.SUPPORT_GROUP, owner=owner)
    elif data == 'alice_privacy':
        text = card('Privacy, plainly', '<blockquote>Your listening room, explained.</blockquote>\n'
                    'The bot stores user and group IDs, names, and play counts. '
                    'Queues are held in memory; downloaded audio and artwork are cached on the host. '
                    'Start and playback notices may be sent to the configured operator log group. '
                    'Search terms are sent to the music service to find tracks.\n\nContact the operator for data removal.')
        keyboard = Keyboard([[Button('‹ Lounge', callback_data='alice_home')]])
    else:
        # Old category callbacks never reveal the former unrestricted registry.
        legacy = {'hcat_📊 Analytics': 'owner_stats', 'hcat_🗄 DB Admin': 'owner_database',
                  'hcat_📣 Broadcast': 'owner_broadcast', 'hcat_🎛 Player': 'controls'}
        page = legacy.get(data, data[6:] if data.startswith('guide_') else None)
        text, keyboard = help_screen(page, owner=owner)
    await edit_panel(query.message, text, keyboard, image=(
        'assets/alice-start-v2.png' if data in ('alice_home', 'alice_privacy')
        else 'assets/alice-help-v2.png'))

@bot.on_callback_query(filters.regex('^alice_close$'))
async def close_panel(client, query):
    await query.answer()
    if query.message:
        cancel_decoration(query.message)
        await query.message.delete()
