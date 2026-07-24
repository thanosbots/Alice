import inspect

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from config import _C
from core.clients import _b1
from database.chats import _asc
from database.users import _asu


# ── button colours (Bot API 9.4) ──────────────────────────────────────
#
# Telegram sirf 3 styles deta hai: "primary" (neela), "success" (hara),
# "danger" (laal). Purani Pyrogram builds `style` kwarg accept nahi karti,
# isiliye pehle signature check karke hi bhejte hain — warna TypeError.
try:
    _HAS_STYLE = "style" in inspect.signature(
        InlineKeyboardButton.__init__
    ).parameters
except (TypeError, ValueError):
    _HAS_STYLE = False


def _btn(_text: str, _style: str = None, **_kw) -> InlineKeyboardButton:
    if _style and _HAS_STYLE:
        _kw["style"] = _style
    return InlineKeyboardButton(_text, **_kw)


# ── helpers ───────────────────────────────────────────────────────────

def _esc(_t) -> str:
    """HTML parse mode use kar rahe hain, to naam ke < > & escape karo."""
    return (
        str(_t or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _mention(_u) -> str:
    return f'<a href="tg://user?id={_u.id}">{_esc(_u.first_name or "there")}</a>'


def _start_caption(_bot_name: str, _u) -> str:
    return (
        f"✦  <b>Hello, {_mention(_u)}</b>  ✦\n\n"
        f"I'm <b>{_esc(_bot_name)}</b> — a music companion for your Telegram "
        f"voice chats. Crystal-clear audio, instant playback, zero babysitting.\n\n"
        "<blockquote><b>⚡  What I Can Do</b>\n"
        "›  Stream HD audio &amp; video in voice chats\n"
        "›  Instant start — no buffering, no lag\n"
        "›  Full queue control: skip, loop, shuffle\n"
        "›  Online 24/7, never sleeps</blockquote>\n\n"
        "<blockquote><b>🚀  Get Started</b>\n"
        "›  Add me to your group\n"
        "›  Start a voice chat\n"
        "›  Send <code>/play song name</code></blockquote>\n\n"
        f"<i>version</i>  <code>{_esc(_C._v)}</code>"
    )


def _start_buttons(_bot_name: str, _bot_un: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            # Main action — isi ek button ko neela rakha hai
            [
                _btn(
                    f"➕  Add {_bot_name} to your group",
                    "primary",
                    url=f"https://t.me/{_bot_un}?startgroup=true",
                )
            ],
            [
                _btn("📖  Help", callback_data="alice_help"),
                _btn("🔒  Privacy", callback_data="alice_privacy"),
            ],
            [
                _btn("💬  Support", "success", url=_C.SUPPORT_GROUP),
                _btn("📢  Updates", url=_C.SUPPORT_CHANNEL),
            ],
            [_btn("⚙️  Source Code", url="https://github.com/thanosbots/Alice")],
        ]
    )


async def _safe_edit(_q: CallbackQuery, _text: str, _markup) -> None:
    """Start message ek PHOTO hai — us par edit_text kaam nahi karta."""
    try:
        if _q.message.photo:
            await _q.message.edit_caption(
                caption=_text, parse_mode=ParseMode.HTML, reply_markup=_markup
            )
        else:
            await _q.message.edit_text(
                text=_text,
                parse_mode=ParseMode.HTML,
                reply_markup=_markup,
                disable_web_page_preview=True,
            )
    except Exception:
        pass


# ── /start (private) ──────────────────────────────────────────────────

@_b1.on_message(filters.command(["start"], ["/"]) & filters.private)
async def _sp(_c, _m):
    _u = _m.from_user
    await _asu(_u.id, _u.first_name)

    _bot_name = _c.me.first_name if _c.me else "Music Bot"
    _bot_un = _c.me.username if _c.me else _b1.username

    await _m.reply_photo(
        _C.START_IMAGE_URL,
        caption=_start_caption(_bot_name, _u),
        parse_mode=ParseMode.HTML,
        reply_markup=_start_buttons(_bot_name, _bot_un),
    )

    # Log group — ye fail ho to /start nahi tootna chahiye
    try:
        _full = f"{_u.first_name or ''} {_u.last_name or ''}".strip()
        _un = f"@{_u.username}" if _u.username else "N/A"
        await _c.send_message(
            _C.LOG_GROUP_ID,
            text=(
                f"<b>🎵  New User</b>\n\n"
                f"<b>Name:</b> {_esc(_full)}\n"
                f"<b>Username:</b> {_esc(_un)}\n"
                f"<b>ID:</b> <code>{_u.id}</code>"
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


# ── added to a new group ──────────────────────────────────────────────

@_b1.on_message(filters.new_chat_members)
async def _ba(_c, _m):
    if not any(_x.id == _b1.id for _x in _m.new_chat_members):
        return

    await _asc(_m.chat.id)
    _bot_name = _c.me.first_name if _c.me else "Music Bot"

    _cap = (
        f"✦  <b>Thanks for adding me to {_esc(_m.chat.title)}</b>  ✦\n\n"
        f"<b>{_esc(_bot_name)}</b> is ready to stream music in this group's "
        f"voice chat.\n\n"
        "<blockquote><b>🎧  Playback</b>\n"
        "›  <code>/play</code> — play audio\n"
        "›  <code>/vplay</code> — play video\n"
        "›  <code>/pause</code> · <code>/resume</code> · <code>/skip</code>\n"
        "›  <code>/end</code> — stop and leave</blockquote>\n\n"
        "<blockquote>⚠️  Make me an <b>admin</b> with "
        "<b>Manage Voice Chats</b> so I can start the call myself.</blockquote>"
    )

    await _m.reply_text(
        text=_cap,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [[_btn("📖  Help Menu", "primary", callback_data="alice_help")]]
        ),
    )


# ── callbacks ─────────────────────────────────────────────────────────

@_b1.on_callback_query(filters.regex("^alice_privacy$"))
async def _privacy_callback(_c: Client, _q: CallbackQuery):
    _bot_name = _c.me.first_name if _c.me else "Music Bot"

    _text = (
        f"🔒  <b>Privacy Policy — {_esc(_bot_name)}</b>\n\n"
        "<blockquote><b>What we store</b>\n"
        "›  Your user ID and group IDs, to manage playback and stats\n"
        "›  Your first name, to show who requested a track</blockquote>\n\n"
        "<blockquote><b>What we never do</b>\n"
        "›  Read or log your messages\n"
        "›  Sell or share your data with anyone</blockquote>\n\n"
        "<i>By using this bot, you agree to the above.</i>"
    )

    await _safe_edit(
        _q,
        _text,
        InlineKeyboardMarkup([[_btn("‹  Back", callback_data="alice_home")]]),
    )
    await _q.answer()


@_b1.on_callback_query(filters.regex("^alice_home$"))
async def _home_callback(_c: Client, _q: CallbackQuery):
    _bot_name = _c.me.first_name if _c.me else "Music Bot"
    _bot_un = _c.me.username if _c.me else _b1.username

    await _safe_edit(
        _q,
        _start_caption(_bot_name, _q.from_user),
        _start_buttons(_bot_name, _bot_un),
    )
    await _q.answer()