import colorsys
import os
import re
import unicodedata
import uuid

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
ASSET_DIR = "assets"
FONT_BOLD = os.path.join(ASSET_DIR, "Montserrat-Bold.ttf")
FONT_SEMI = os.path.join(ASSET_DIR, "Montserrat-SemiBold.ttf")   # optional
FONT_REG = os.path.join(ASSET_DIR, "Montserrat-Regular.ttf")
FONT_ITA = os.path.join(ASSET_DIR, "Montserrat-Italic.ttf")

OUT_DIR = "downloads"

CANVAS_W, CANVAS_H = 1280, 720

WHITE = (255, 255, 255)
SOFT = (216, 220, 228)
MUTED = (150, 158, 172)

_FONT_CACHE = {}


def _font(path, size):
    """Font loader with cache + graceful fallback chain."""
    key = (path, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    candidates = [
        path,
        FONT_REG,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    f = None
    for c in candidates:
        try:
            f = ImageFont.truetype(c, size)
            break
        except Exception:
            continue
    if f is None:
        f = ImageFont.load_default()

    _FONT_CACHE[key] = f
    return f


# ---------------------------------------------------------------------------
# Text hygiene
# ---------------------------------------------------------------------------
def _fix_mojibake(s: str) -> str:
    """
    'JoÃ£o Faria' -> 'João Faria'
    Ye tab hota hai jab UTF-8 bytes ko latin-1 samajh ke decode kiya jaye.
    Sirf tab apply karo jab clear signature dikhe, warna sahi text tootega.
    """
    if not any(m in s for m in ("Ã", "â€", "Â", "ð")):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


_LATIN_NAME = re.compile(
    r"\bLATIN\b.*\bLETTER\b\s+"
    r"(?:SMALL CAPITAL\s+|TURNED\s+|REVERSED\s+|SCRIPT\s+|INSULAR\s+"
    r"|SIDEWAYS\s+|BROKEN\s+|DOTLESS\s+|STRETCHED\s+)*"
    r"([A-Z])(?:\s+WITH\b.*)?$"
)


def _fold_char(ch):
    """
    Fancy Unicode ko normal letter banata hai.

    NFKC math alphanumerics (𝗔) handle kar leta hai, PAR small-caps
    (ᴍᴜsɪᴄ) ko nahi — wo Unicode ke hisaab se asli letters hain.
    Isiliye pichhli baar bot name boxes mein render hua tha.
    Yahan character ka Unicode NAME padh ke base letter nikaalte hain:
    "LATIN LETTER SMALL CAPITAL M" -> "M"
    """
    if ch.isascii():
        return ch
    if "\u00c0" <= ch <= "\u024f":      # accented Latin — Montserrat support karta hai
        return ch
    try:
        nm = unicodedata.name(ch)
    except ValueError:
        return ""
    m = _LATIN_NAME.match(nm)
    if m:
        base = m.group(1)
        return base if ("CAPITAL" in nm) else base.lower()
    d = unicodedata.normalize("NFKD", ch)
    d = "".join(c for c in d if not unicodedata.combining(c))
    return d if d.isascii() else ""


def clean_title(t, trim_credits=True):
    """
    'Dilbar___Satyameva_Jayate___John_Abraham.mp3'
        -> 'Dilbar Satyameva Jayate John Abraham'
    'Gali Gali | Neha Kakkar | Tanishk Bagchi'  -> 'Gali Gali'

    Filename-style titles mein space nahi hota, isliye wrap fail ho jata tha.
    trim_credits: pehle '|' ke baad ka hissa credits hota hai (singer, composer,
    label) — artist alag field mein already aa raha hai, to wo hata dete hain.
    """
    t = re.sub(r"\.(mp3|m4a|mp4|webm|opus|flac|wav|aac)$", "", t, flags=re.I)
    t = re.sub(r"[_]+", " ", t)
    if trim_credits and "|" in t:
        head = t.split("|")[0].strip()
        if len(head) >= 4:
            t = head
    t = t.replace("|", "\u2022")
    t = re.sub(r"\s{2,}", " ", t).strip(" -\u2013\u2014\u2022")
    return t or "Unknown Track"


def sanitize(text, fallback="Unknown"):
    """
    PURANA clean_text() saara non-ASCII udaa deta tha, isiliye bot name
    '𝗔𝗹𝗶𝗰𝗲' se sirf 's' bacha tha.

    Ab: mojibake repair -> NFKC normalize (fancy unicode letters ko normal
    letters mein badalta hai) -> sirf emoji/symbols drop, accented letters
    (ão, ü, é) rakhe jaate hain kyunki Montserrat unhe support karta hai.
    """
    if text is None:
        return fallback
    s = _fix_mojibake(str(text))
    s = unicodedata.normalize("NFKC", s)

    out = []
    for ch in s:
        cat = unicodedata.category(ch)
        if cat == "Zs":
            out.append(" ")
        elif cat[0] in ("L", "N", "P") or ch in "|&+~":
            # '|' category Sm (symbol) hai, P nahi — isliye alag se allow karna
            # pada, warna "Gali Gali | Neha Kakkar" ek shabd ban jaata tha.
            out.append(_fold_char(ch) if ch not in "|&+~" else ch)
    s = " ".join("".join(out).split())
    return s or fallback


def parse_duration(v):
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        try:
            parts = [int(p) for p in v.split(":")]
            total = 0
            for p in parts:
                total = total * 60 + p
            return total
        except Exception:
            return 0
    return 0


def format_time(seconds):
    try:
        seconds = int(seconds)
    except Exception:
        return "00:00"
    if seconds >= 3600:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}"
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def format_count(n):
    try:
        n = int(n)
    except Exception:
        return None
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def _w(font, text):
    try:
        return font.getlength(text)
    except Exception:
        return font.getbbox(text)[2]


def _fit_font(path, text, max_w, start, minimum):
    """Text ko truncate karne ke bajaye font shrink karta hai."""
    size = start
    while size > minimum:
        f = _font(path, size)
        if _w(f, text) <= max_w:
            return f, size
        size -= 2
    return _font(path, minimum), minimum


def _clamp(text, font, max_w):
    """Line ko zabardasti fit karo — overflow kabhi canvas se bahar na jaye."""
    if _w(font, text) <= max_w:
        return text
    t = text
    while t and _w(font, t + "\u2026") > max_w:
        t = t[:-1]
    return (t.rstrip() + "\u2026") if t else "\u2026"


def _wrap(text, font, max_w, max_lines=2):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if _w(font, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)

    if len(lines) == max_lines and words:
        if len(" ".join(lines)) < len(text):
            lines[-1] = _clamp(lines[-1] + "\u2026", font, max_w)

    lines = lines or [text]
    # HARD CLAMP: single-word titles (Dilbar___Satyameva_Jayate) wrap nahi hote,
    # isliye har line ko individually clamp karna zaroori hai.
    return [_clamp(ln, font, max_w) for ln in lines]


def _tracked(draw, xy, text, font, fill, tracking=0.0):
    """Letter-spaced text — chhota sa detail jo premium feel deta hai."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += _w(font, ch) + tracking
    return x - xy[0]


def _tracked_w(font, text, tracking=0.0):
    if not text:
        return 0
    return sum(_w(font, c) for c in text) + tracking * (len(text) - 1)


# ---------------------------------------------------------------------------
# Colour
# ---------------------------------------------------------------------------
def _accent_from(img):
    """
    Album art se sabse vibrant colour nikalta hai.
    Hardcoded cyan ki jagah har gaane ka apna accent — sabse bada visual upgrade.
    """
    try:
        small = img.convert("RGB").resize((80, 80), Image.LANCZOS)
        method = getattr(Image, "Quantize", Image).FASTOCTREE
        pal = small.quantize(colors=12, method=method).convert("RGB")
        colors = pal.getcolors(80 * 80) or []

        best, best_score = None, -1.0
        for count, (r, g, b) in colors:
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if v < 0.22 or s < 0.18:          # too dark / too grey
                continue
            score = (s ** 1.4) * v * (count ** 0.32)
            if score > best_score:
                best_score, best = score, (r, g, b)

        if best is None:
            return (0, 224, 255)

        h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in best])
        s = min(1.0, s * 1.30)
        v = max(v, 0.88)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))
    except Exception:
        return (0, 224, 255)


def _mix(c, other, t):
    return tuple(int(c[i] + (other[i] - c[i]) * t) for i in range(3))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def generate_thumbnail(
    cover_path,
    raw_title,
    raw_duration,
    played_s,
    requester,
    bot_name,
    artist=None,
    genre=None,
    views=None,
    likes=None,
):
    # ---- source art -------------------------------------------------------
    try:
        cover = Image.open(cover_path).convert("RGB")
    except Exception:
        cover = Image.new("RGB", (600, 600), (34, 36, 44))

    accent = _accent_from(cover)
    accent_dim = _mix(accent, (0, 0, 0), 0.45)

    # ---- text prep --------------------------------------------------------
    title_raw = clean_title(sanitize(raw_title, "Unknown Track"))
    if artist:
        artist_txt = sanitize(artist, "Unknown Artist")
        title = title_raw
    elif " - " in title_raw:
        left, right = title_raw.split(" - ", 1)
        title, artist_txt = left.strip(), right.strip()
    else:
        title, artist_txt = title_raw, "Unknown Artist"

    bot = sanitize(bot_name, "Music")
    req = sanitize(requester, "Someone")
    duration_s = parse_duration(raw_duration)
    played_s = max(0, parse_duration(played_s))

    # ---- background -------------------------------------------------------
    # Blur ko chhote canvas par karke upscale karte hain — dikhne mein same,
    # par ~15x sasta. Tumhare CPU headroom ko dekhte hue ye maayne rakhta hai.
    bg_small = ImageOps.fit(cover, (320, 180), Image.LANCZOS, centering=(0.5, 0.4))
    bg_small = ImageEnhance.Color(bg_small).enhance(1.7)
    bg_small = bg_small.filter(ImageFilter.GaussianBlur(radius=14))
    base = bg_small.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).convert("RGBA")

    # darkening + vignette
    shade = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for i in range(CANVAS_H):
        a = int(70 + 90 * (i / CANVAS_H))
        sd.line([(0, i), (CANVAS_W, i)], fill=(6, 8, 14, a))
    base = Image.alpha_composite(base, shade)

    vig = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    ImageDraw.Draw(vig).ellipse(
        (-260, -200, CANVAS_W + 260, CANVAS_H + 200), fill=190
    )
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 150))
    base = Image.composite(base, Image.alpha_composite(base, dark), vig)

    # ---- glass panel ------------------------------------------------------
    PX0, PY0, PX1, PY1 = 44, 44, CANVAS_W - 44, CANVAS_H - 44

    glass = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.rounded_rectangle((PX0, PY0, PX1, PY1), radius=38, fill=(10, 12, 20, 158))
    gd.rounded_rectangle(
        (PX0, PY0, PX1, PY1), radius=38, outline=(255, 255, 255, 46), width=2
    )
    gd.line([(PX0 + 40, PY0 + 2), (PX1 - 40, PY0 + 2)], fill=(255, 255, 255, 70), width=2)
    base = Image.alpha_composite(base, glass)

    # ---- album art --------------------------------------------------------
    ART = 448
    ax, ay = PX0 + 52, PY0 + (PY1 - PY0 - ART) // 2

    # accent glow behind art
    glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(
        (ax - 6, ay - 6, ax + ART + 6, ay + ART + 6), radius=34, fill=accent + (120,)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(26))
    base = Image.alpha_composite(base, glow)

    # aspect-correct crop (PEHLE yahan resize((480,480)) tha jo squish karta tha)
    art = ImageOps.fit(cover, (ART, ART), Image.LANCZOS, centering=(0.5, 0.5))
    mask = Image.new("L", (ART, ART), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, ART - 1, ART - 1), radius=28, fill=255)
    art = art.convert("RGBA")
    art.putalpha(mask)
    base.paste(art, (ax, ay), art)

    ring = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle(
        (ax, ay, ax + ART, ay + ART), radius=28, outline=accent + (150,), width=2
    )
    base = Image.alpha_composite(base, ring)

    draw = ImageDraw.Draw(base)

    # ---- text column ------------------------------------------------------
    TX = ax + ART + 56
    TW = PX1 - 52 - TX

    f_eyebrow = _font(FONT_BOLD, 24)
    eyebrow = f"{bot.upper()}  •  NOW PLAYING"
    while _tracked_w(f_eyebrow, eyebrow, 2.2) > TW and len(eyebrow) > 12:
        bot = bot[:-1].strip()
        eyebrow = f"{bot.upper()}  •  NOW PLAYING"

    # Har size par wrap try karo; jo pehle poora fit ho jaye wahi lo.
    _t_up = title.upper()
    f_title, ts, title_lines = None, 34, None
    for _sz in range(66, 33, -2):
        _f = _font(FONT_BOLD, _sz)
        _lines = _wrap(_t_up, _f, TW, max_lines=2)
        if all(_w(_f, ln) <= TW for ln in _lines) and not _lines[-1].endswith("\u2026"):
            f_title, ts, title_lines = _f, _sz, _lines
            break
    if f_title is None:
        f_title, ts = _font(FONT_BOLD, 34), 34
        title_lines = _wrap(_t_up, f_title, TW, max_lines=2)

    f_artist, _ = _fit_font(FONT_REG, artist_txt.upper(), TW, 38, 24)
    f_small = _font(FONT_REG, 25)
    f_badge = _font(FONT_BOLD, 21)

    badges = []
    if genre:
        badges.append(sanitize(genre, "").upper())
    v = format_count(views)
    if v:
        badges.append(f"{v} PLAYS")
    l = format_count(likes)
    if l:
        badges.append(f"{l} LIKES")
    badges = [b for b in badges if b][:3]

    line_h = int(ts * 1.14)
    block = 30 + 18 + line_h * len(title_lines) + 10 + 46
    if badges:
        block += 22 + 36
    block += 34 + 10 + 14 + 26 + 24 + 26

    y = ay + max(0, (ART - block) // 2)

    # eyebrow
    _tracked(draw, (TX, y), eyebrow, f_eyebrow, accent, tracking=2.2)
    y += 30 + 18

    # title (soft shadow for depth)
    sh = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(sh)
    yy = y
    for ln in title_lines:
        shd.text((TX + 2, yy + 4), ln, font=f_title, fill=(0, 0, 0, 170))
        yy += line_h
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(7)))
    draw = ImageDraw.Draw(base)

    for ln in title_lines:
        draw.text((TX, y), ln, font=f_title, fill=WHITE)
        y += line_h
    y += 10

    draw.text((TX, y), artist_txt.upper(), font=f_artist, fill=SOFT)
    y += 46

    # badges
    if badges:
        y += 22
        bx = TX
        pill = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        for b in badges:
            bw = int(_w(f_badge, b)) + 30
            if bx + bw > PX1 - 52:
                break
            pd.rounded_rectangle((bx, y, bx + bw, y + 36), radius=18,
                                 fill=accent_dim + (110,), outline=accent + (130,), width=1)
            bx += bw + 12
        base = Image.alpha_composite(base, pill)
        draw = ImageDraw.Draw(base)

        bx = TX
        for b in badges:
            bw = int(_w(f_badge, b)) + 30
            if bx + bw > PX1 - 52:
                break
            draw.text((bx + 15, y + 8), b, font=f_badge, fill=accent)
            bx += bw + 12
        y += 36
    y += 34

    # ---- progress bar -----------------------------------------------------
    BH = 9
    bar = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    bd.rounded_rectangle((TX, y, TX + TW, y + BH), radius=BH // 2, fill=(255, 255, 255, 62))
    base = Image.alpha_composite(base, bar)
    draw = ImageDraw.Draw(base)

    pct = (played_s / duration_s) if duration_s > 0 else 0.0
    pct = min(1.0, max(0.0, pct))
    pw = max(BH, int(TW * pct))

    # gradient fill accent -> lighter accent
    grad = Image.new("RGB", (max(pw, 1), 1))
    gp = grad.load()
    light = _mix(accent, WHITE, 0.45)
    for i in range(max(pw, 1)):
        gp[i, 0] = _mix(accent, light, i / max(pw - 1, 1))
    grad = grad.resize((max(pw, 1), BH), Image.NEAREST).convert("RGBA")
    gm = Image.new("L", (max(pw, 1), BH), 0)
    ImageDraw.Draw(gm).rounded_rectangle((0, 0, max(pw, 1) - 1, BH - 1), radius=BH // 2, fill=255)
    grad.putalpha(gm)
    base.paste(grad, (TX, y), grad)
    draw = ImageDraw.Draw(base)

    DOT = 26
    dx = TX + pw - DOT // 2
    dy = y + BH // 2 - DOT // 2
    halo = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse(
        (dx - 8, dy - 8, dx + DOT + 8, dy + DOT + 8), fill=accent + (110,)
    )
    base = Image.alpha_composite(base, halo.filter(ImageFilter.GaussianBlur(9)))
    draw = ImageDraw.Draw(base)
    draw.ellipse((dx, dy, dx + DOT, dy + DOT), fill=WHITE, outline=accent, width=3)

    y += BH + 14
    draw.text((TX, y), format_time(played_s), font=f_small, fill=SOFT)
    dur_txt = format_time(duration_s)
    draw.text((TX + TW - _w(f_small, dur_txt), y), dur_txt, font=f_small, fill=SOFT)
    y += 26 + 24

    draw.text((TX, y), "REQUESTED BY", font=_font(FONT_BOLD, 18), fill=MUTED)
    rq_x = TX + _w(_font(FONT_BOLD, 18), "REQUESTED BY ") + 8
    draw.text((rq_x, y - 3), req, font=_font(FONT_BOLD, 23), fill=accent)

    # ---- save -------------------------------------------------------------
    # PEHLE ye hardcoded "downloads/final_thumb.png" tha — do groups ek saath
    # play karein to ek dusre ki thumbnail overwrite kar dete the.
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"thumb_{uuid.uuid4().hex[:12]}.png")
    base.convert("RGB").save(out, "PNG", optimize=True)
    return out