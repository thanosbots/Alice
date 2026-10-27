"""Shared Telegram presentation; all variable text is escaped at the boundary."""
from html import escape
from helpers.version import VERSION
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton as Button, InlineKeyboardMarkup as Keyboard
from pyrogram.errors import MessageNotModified

FOOTER = '<i>A L I C E  ·  The listening room</i>'


def card(title, body, note=''):
    return f'<b>◇ {escape(title)}</b>\n\n{body}\n\n' + (f'{note}\n\n' if note else '') + FOOTER


def home(name, owner=False):
    if owner:
        return card('Welcome home, Rishabh Anand',
                    '<blockquote>♛ Creator of Alice\nYour room. Your signature sound.</blockquote>\n\n'
                    'Your listening room is ready. Choose a record or open your private owner desk.',
                    f'<b>Version</b> · {VERSION}\n<b>Your next selection</b> · <code>/play song name</code>')
    return card(name, '<blockquote>Your people. Your music. Your moment.</blockquote>\n\n'
                'A private listening room for your Telegram group.\n'
                'Discover a song, build a queue, settle in.',
                f'<b>Version</b> · {VERSION}\n<b>Begin with</b> <code>/play song name</code>')


def home_buttons(username, support, owner=False):
    return Keyboard([
        [Button('＋ Add to your group', url=f'https://t.me/{username}?startgroup=true')],
        [Button('♛ Your owner desk' if owner else '◇ Explore the guide', callback_data='alice_help')],
        [Button('Support', url=support), Button('Privacy', callback_data='alice_privacy')],
    ])


PAGES = {
    'listen': ('01 · Discover & listen', '<blockquote>/play song name\n/search song or artist</blockquote>\n'
               'Play a song directly or choose from five search results. You can also reply to an audio file with /play.\n\n'
               '<blockquote expandable><b>Your first session</b>\n'
               '1. Add the bot to your group.\n2. Give it the permissions needed to manage voice chats and invite the assistant.\n'
               '3. Open a voice chat and send /play.\n4. Join the voice chat to listen on your phone or computer.</blockquote>'),
    'controls': ('02 · The player', '<blockquote>/pause · /resume\n/skip · /stop</blockquote>\n'
                 'Group admins control the room. Everyone can request music and view the queue.\n\n'
                 '<b>/now</b> — current selection\n<b>/queue</b> — what comes next\n'
                 '<b>/next</b> — skip to the next song\n<b>/end</b> — close the session, just like /stop'),
    'queue': ('03 · Curate your queue', '<blockquote>/shuffle\n/repeat off | one | all</blockquote>\n'
              '<b>/remove 2</b> — remove upcoming song 2\n<b>/move 3 1</b> — move song 3 to next up\n'
              '<b>/clearqueue</b> — keep only the current song\n\n'
              '<blockquote expandable>Queue editing is for group admins. Positions begin at 1 for the next song. '
              'Repeat one replays the current song; repeat all rotates the whole queue. Skip still moves forward.</blockquote>'),
    'care': ('04 · A smoother session', '<blockquote>Start a voice chat. Invite the assistant. Press play.</blockquote>\n'
             'If audio pauses, check the host connection and your Telegram connection. '
             'Make sure the assistant is allowed to speak.\n\n'
             '<blockquote expandable>Audio is prepared locally before playback so the music source does not need to stay connected during a song. '
             'A stable, awake host is still needed. If a song cannot be prepared, try another result or send an audio file.</blockquote>'),
}


OWNER_PAGES = {
    'owner_stats': ('05 · Observatory', '<blockquote>/stats · /dbstats · /top</blockquote>\n'
                    '<b>/stats</b> — uptime, listeners, groups and active streams; includes Refresh.\n'
                    '<b>/dbstats</b> — stored users, groups and total plays.\n'
                    '<b>/top</b> — ten listeners with the most plays.\n\n'
                    '<b>/update</b> — check for a new version; confirm before installing.\n'
                    '<i>Only available in the owner’s private chat.</i>'),
    'owner_broadcast': ('06 · Announcements', '<blockquote>/broadcast users\n/broadcast groups</blockquote>\n'
                        'Reply to the message you want to copy, then choose the audience.\n\n'
                        '<b>Alias:</b> /bcast users or /bcast groups. Both / and ! prefixes work.\n\n'
                        '<blockquote expandable>This sends a real message to every stored recipient in the selected audience. '
                        'Review the message and target before running the command.</blockquote>'),
    'owner_database': ('07 · Library care', '<blockquote>/cleanusers\n/cleanchats</blockquote>\n'
                       '<b>/cleanusers</b> — remove confirmed deleted user accounts.\n'
                       '<b>/cleanchats</b> — remove confirmed inaccessible groups or groups where the bot is not an admin.\n\n'
                       '<blockquote expandable>These commands change stored records. Temporary connection problems '
                       'do not remove records. Cleanup is restricted to the owner’s private chat.</blockquote>'),
}


def help_screen(page=None, owner=False):
    pages = {**PAGES, **(OWNER_PAGES if owner else {})}
    if page in pages:
        title, body = pages[page]
        return card(title, body), Keyboard([[Button('‹ Guide', callback_data='alice_help'), Button('⌂ Lounge', callback_data='alice_home')]])
    rows = [
        [Button('01 · Discover', callback_data='guide_listen'), Button('02 · Playback', callback_data='guide_controls')],
        [Button('03 · Queue studio', callback_data='guide_queue'), Button('04 · Setup & care', callback_data='guide_care')],
    ]
    if owner:
        rows += [[Button('05 · Observatory', callback_data='guide_owner_stats')],
                 [Button('06 · Announcements', callback_data='guide_owner_broadcast'), Button('07 · Library care', callback_data='guide_owner_database')]]
    rows += [[Button('⌂ Lounge', callback_data='alice_home')]]
    return card('Rishabh’s private guide' if owner else 'The listening guide', '<blockquote>Every command. In its place.</blockquote>\n'
                '<b>For listeners</b> · discover music and see what’s next.\n'
                '<b>For group admins</b> · shape playback and curate the queue.\n\n'
                '<code>/start</code> opens the lounge. <code>/help</code> opens this guide.\n'
                '<code>/ping</code> — check response time and uptime.'), Keyboard(rows)


async def edit_panel(message, text, keyboard, image=None):
    from helpers.notifications import cancel_decoration, schedule_decoration
    cancel_decoration(message)
    try:
        if message.photo:
            await message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        else:
            await message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard, disable_web_page_preview=True)
    except MessageNotModified:
        pass
    if image:
        schedule_decoration(message, text, keyboard, image)


def track_card(track, position=0):
    return card(('♛ Creator’s selection' if track.get('is_owner') else 'Now playing') if position == 0 else f'Next in line · {position:02d}',
                f"<blockquote><b>{escape(str(track['title'])[:150])}</b>\n"
                f"{escape(str(track['duration']))} · Audio</blockquote>\n"
                f"Selected by {escape(str(track['requested_by'])[:80])}")
