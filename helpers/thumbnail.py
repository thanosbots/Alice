import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

def truncate(text, font, max_width):
    if font.getbbox(text)[2] <= max_width:
        return text
    for i in range(len(text), 0, -1):
        truncated = text[:i] + "..."
        if font.getbbox(truncated)[2] <= max_width:
            return truncated
    return "..."

def format_time(seconds):
    try:
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"
    except:
        return "00:00"

def parse_duration(duration_input):
    if isinstance(duration_input, (int, float)):
        return int(duration_input)
    if isinstance(duration_input, str):
        try:
            parts = duration_input.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            return 0
    return 0

def clean_text(text):
    """Removes weird fonts and emojis so it doesn't print [] boxes"""
    if not text:
        return "Music Bot"
    # Keep only standard English letters, numbers, and basic punctuation
    clean = re.sub(r'[^\x00-\x7F]+', '', text).strip()
    return clean if clean else "Music Bot"

def generate_thumbnail(cover_path, raw_title, raw_duration, played_s, requester, bot_name):
    """Generates the Abstract Fluid Aura with fixed Dark Glass Panel."""
    
    CANVAS_W, CANVAS_H = 1280, 720
    
    ASSET_DIR = "assets"
    FONT_BOLD = os.path.join(ASSET_DIR, "Montserrat-Bold.ttf") 
    FONT_REG = os.path.join(ASSET_DIR, "Montserrat-Regular.ttf")
    FONT_ITA = os.path.join(ASSET_DIR, "Montserrat-Italic.ttf")

    WHITE = (255, 255, 255)
    GREY = (200, 200, 200)
    CYAN_GLOW = (0, 255, 255)
    
    # Auto-Fix Text
    if " - " in str(raw_title):
        title = raw_title.split(" - ")[0].strip()
        artist = raw_title.split(" - ")[1].strip()
    else:
        title = str(raw_title)
        artist = "Unknown Artist"

    duration_s = parse_duration(raw_duration)
    
    # Clean the bot name to prevent [] boxes
    safe_bot_name = clean_text(bot_name)

    # 1. ABSTRACT BACKGROUND
    try:
        source_cover = Image.open(cover_path).convert('RGBA')
    except:
        source_cover = Image.new('RGBA', (500, 500), (40, 40, 40, 255))

    aspect_ratio = CANVAS_W / CANVAS_H
    src_w, src_h = source_cover.size
    src_ratio = src_w / src_h

    if src_ratio > aspect_ratio:
        new_h = src_h
        new_w = int(new_h * aspect_ratio)
        left = (src_w - new_w) // 2
        bg_crop = source_cover.crop((left, 0, left + new_w, new_h))
    else:
        new_w = src_w
        new_h = int(new_w / aspect_ratio)
        top = (src_h - new_h) // 2
        bg_crop = source_cover.crop((0, top, new_w, top + new_h))
        
    background = bg_crop.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    
    # Blur and boost colors
    enhancer = ImageEnhance.Color(background)
    background = enhancer.enhance(1.8)
    background = background.filter(ImageFilter.GaussianBlur(radius=50))
    
    # 2. PROPER TRANSPARENT DARK GLASS PANEL (FIXED)
    # We create a completely separate transparent layer to draw shapes
    shape_layer = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    shape_draw = ImageDraw.Draw(shape_layer)
    
    PANEL_X, PANEL_Y = 60, 60
    PANEL_W, PANEL_H = 1160, 600
    
    # Draw dark translucent rectangle
    shape_draw.rounded_rectangle(
        (PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H), 
        radius=40, 
        fill=(0, 0, 0, 140),          # 140 is the darkness level (0-255)
        outline=(255, 255, 255, 60),  # Light border
        width=2
    )
    
    # Merge the shapes onto the background
    background = Image.alpha_composite(background, shape_layer)
    
    # Now setup the canvas to draw text on the merged background
    canvas = ImageDraw.Draw(background)

    # 3. ALBUM ART INSIDE PANEL
    ART_SIZE = 480
    art_x, art_y = PANEL_X + 60, PANEL_Y + 60
    
    album_art = source_cover.resize((ART_SIZE, ART_SIZE), Image.LANCZOS)
    mask = Image.new('L', (ART_SIZE, ART_SIZE), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((0, 0, ART_SIZE, ART_SIZE), radius=30, fill=255)
    
    rounded_art = ImageOps.fit(album_art, mask.size, centering=(0.5, 0.5))
    rounded_art.putalpha(mask)
    background.paste(rounded_art, (art_x, art_y), rounded_art)

    # 4. TEXT
    TEXT_X = art_x + ART_SIZE + 60
    MAX_TEXT_WIDTH = (PANEL_X + PANEL_W) - TEXT_X - 60

    try:
        font_ita_small = ImageFont.truetype(FONT_ITA, 35)
        font_bold_large = ImageFont.truetype(FONT_BOLD, 90)
        font_reg_med = ImageFont.truetype(FONT_REG, 50)
        font_reg_small = ImageFont.truetype(FONT_REG, 30)
    except:
        font_ita_small = font_bold_large = font_reg_med = font_reg_small = ImageFont.load_default()

    # Dynamic Bot Name (Cleaned)
    canvas.text((TEXT_X, art_y + 30), f"{safe_bot_name} • Now Playing", font=font_ita_small, fill=CYAN_GLOW)
    
    # Title & Artist (Now visible over the dark panel)
    trunc_title = truncate(title.upper(), font_bold_large, MAX_TEXT_WIDTH)
    canvas.text((TEXT_X, art_y + 100), trunc_title, font=font_bold_large, fill=WHITE)
    
    trunc_artist = truncate(artist.upper(), font_reg_med, MAX_TEXT_WIDTH)
    canvas.text((TEXT_X, art_y + 210), trunc_artist, font=font_reg_med, fill=GREY)

    # 5. PROGRESS BAR (FIXED)
    BAR_WIDTH = MAX_TEXT_WIDTH
    BAR_HEIGHT = 8
    BAR_X = TEXT_X
    BAR_Y = art_y + 360
    
    # Background line
    canvas.rounded_rectangle((BAR_X, BAR_Y, BAR_X + BAR_WIDTH, BAR_Y + BAR_HEIGHT), radius=BAR_HEIGHT//2, fill=(255,255,255,80))
    
    if duration_s > 0:
        percent = played_s / duration_s
        progress_w = int(BAR_WIDTH * percent)
        # Prevent it from being 0 width
        if progress_w < BAR_HEIGHT:
            progress_w = BAR_HEIGHT
            
        # Filled line
        canvas.rounded_rectangle((BAR_X, BAR_Y, BAR_X + progress_w, BAR_Y + BAR_HEIGHT), radius=BAR_HEIGHT//2, fill=CYAN_GLOW)
        
        # Dot
        DOT_SIZE = 30
        dot_x = BAR_X + progress_w - (DOT_SIZE // 2)
        dot_y = BAR_Y + (BAR_HEIGHT // 2) - (DOT_SIZE // 2)
        canvas.ellipse((dot_x, dot_y, dot_x + DOT_SIZE, dot_y + DOT_SIZE), fill=WHITE, outline=CYAN_GLOW, width=3)

    canvas.text((BAR_X, BAR_Y + 25), format_time(played_s), font=font_reg_small, fill=WHITE)
    canvas.text((BAR_X + BAR_WIDTH - font_reg_small.getbbox(format_time(duration_s))[2], BAR_Y + 25), format_time(duration_s), font=font_reg_small, fill=WHITE)

    # 6. REQUESTER
    req_text = f"Requested by: {requester}"
    canvas.text((TEXT_X, art_y + 440), req_text, font=font_reg_small, fill=GREY)

    output_path = "downloads/final_thumb.png"
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    background.save(output_path, "PNG")
    return output_path