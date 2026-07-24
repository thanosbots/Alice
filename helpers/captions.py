"""
Saari player captions ek jagah.

Kyun alag file: captions abhi teen jagah duplicate hain (play, queue-add,
next-song). Alag-alag hone se format drift ho jaata hai — jaise next-song
wali caption abhi bhi seconds ko "Minutes" likh rahi hai.

HTML parse mode use karo, Markdown nahi. Wajah: titles mein underscore hota
hai (DILBAR_Satyameva_Jayate), jo Markdown mein italic marker ban jaata hai
aur caption tod deta hai. HTML mein escape karna reliable hai.

    from pyrogram.enums import ParseMode
    await _m.reply_photo(photo=..., caption=..., parse_mode=ParseMode.HTML)
"""

import html

from helpers.thumbnail import clean_title, sanitize

# ---------------------------------------------------------------------------
# STYLE: "card" | "minimal" | "neon"
# ---------------------------------------------------------------------------
STYLE = "card"

SHOW_FOOTER = False          # "Powered by ..." wapas chahiye to True


def _e(t):
    """HTML escape — bina iske '&' ya '<' wale titles caption tod dete hain."""
    return html.escape(str(t if t is not None else ""), quote=False)


def _dur(sec):
    try:
        sec = int(float(sec))
    except (TypeError, ValueError):
        return "00:00"
    if sec >= 3600:
        h, r = divmod(sec, 3600)
        m, s = divmod(r, 60)
        return f"{h}:{m:02d}:{s:02d}"
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"


def _title(meta):
    return clean_title(sanitize(meta.get("title") or "Unknown Track", "Unknown Track"))


def _artist(meta):
    a = meta.get("artist")
    return sanitize(a, "") if a else ""


def _linked(meta):
    t = _e(_title(meta))
    link = meta.get("link")
    if link and str(link).startswith("http"):
        return f'<a href="{_e(link)}">{t}</a>'
    return t


def _bar(played, total, width=14):
    """▰▰▰▱▱▱ style progress — 0 par bhi saaf dikhta hai."""
    try:
        pct = max(0.0, min(1.0, float(played) / float(total)))
    except (TypeError, ValueError, ZeroDivisionError):
        pct = 0.0
    filled = int(round(width * pct))
    return "▰" * filled + "▱" * (width - filled)


def _body(meta, requester, played=None):
    rows = [f"⏱  <b>Duration</b>   <code>{_dur(meta.get('duration'))}</code>"]

    g = meta.get("genre")
    if g:
        rows.append(f"💿  <b>Genre</b>      <code>{_e(sanitize(g, ''))}</code>")

    rows.append(f"👤  <b>Added by</b>   {_e(requester)}")

    if played is not None and meta.get("duration"):
        rows.insert(
            0,
            f"<code>{_bar(played, meta['duration'])}</code>  "
            f"{_dur(played)} / {_dur(meta.get('duration'))}",
        )
    return rows


def _wrap(header, meta, rows):
    t = _linked(meta)
    a = _artist(meta)

    if STYLE == "minimal":
        out = [header, "", f"🎵 <b>{t}</b>"]
        if a:
            out.append(f"🎤 <i>{_e(a)}</i>")
        out += ["", "   ".join(r.replace("<b>", "").replace("</b>", "") for r in rows)]

    elif STYLE == "neon":
        out = [
            "╭━━━━━━━━━━━━━━━━━━╮",
            f"   {header}",
            "╰━━━━━━━━━━━━━━━━━━╯",
            "",
            f"🎵 <b>{t}</b>",
        ]
        if a:
            out.append(f"🎤 <i>{_e(a)}</i>")
        out.append("")
        out += [f"│ {r}" for r in rows]
        out.append("╰──────────────────")

    else:  # card
        out = [header, "", f"🎵 <b>{t}</b>"]
        if a:
            out.append(f"🎤 <i>{_e(a)}</i>")
        out += ["", "<blockquote>" + "\n".join(rows) + "</blockquote>"]

    if SHOW_FOOTER:
        out += ["", "<i>🎧 Alice Music</i>"]
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------
def now_playing(meta, requester, played=None):
    return _wrap("✦  <b>ɴᴏᴡ ᴘʟᴀʏɪɴɢ</b>", meta, _body(meta, requester, played))


def queued(meta, requester, position):
    header = f"✅  <b>ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ</b>  ·  <code>#{position}</code>"
    return _wrap(header, meta, _body(meta, requester))


def up_next(meta, requester):
    return _wrap("⏭  <b>ᴜᴘ ɴᴇxᴛ</b>", meta, _body(meta, requester))