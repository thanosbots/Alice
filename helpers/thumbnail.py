"""A local, typography-led album card matching the listening-room identity."""
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]

def font(size, bold=False):
    return ImageFont.truetype(str(ROOT / 'assets' / ('Montserrat-Bold.ttf' if bold else 'Montserrat-Regular.ttf')), size)

def fit_text(text, face, width):
    text = ' '.join(str(text).split())
    if face.getlength(text) <= width:
        return text
    while text and face.getlength(text + '…') > width:
        text = text[:-1]
    return text + '…'

def title_lines(text, face, width, count=3):
    words = ' '.join(str(text)[:500].split()).split(' ')
    lines = []
    while words and len(lines) < count:
        line = words.pop(0)
        while words and face.getlength(line + ' ' + words[0]) <= width:
            line += ' ' + words.pop(0)
        if len(lines) == count - 1 and words:
            line += ' ' + ' '.join(words)
            words.clear()
        lines.append(fit_text(line, face, width))
    return lines

def generate_thumbnail(cover_path, raw_title, raw_duration, played_s, requester, bot_name, output_path=None, owner=False):
    # The card intentionally has no fake playback-progress bar.
    identity = '\0'.join(map(str, (cover_path, raw_title, raw_duration, requester, bot_name)))
    output = Path(output_path) if output_path else ROOT / 'downloads' / ('card_' + hashlib.sha256(identity.encode()).hexdigest()[:24] + '.jpg')
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new('RGB', (1280, 720), '#10110f')
    draw = ImageDraw.Draw(canvas)
    gold, ivory, muted = '#c5a474', '#f4ecdd', '#96958a'
    draw.rectangle((30, 30, 1249, 689), outline='#3b372d')
    draw.text((76, 68), fit_text(f'{bot_name.upper()}  /  THE LISTENING ROOM', font(18), 1110), font=font(18), fill=gold)
    draw.line((76, 116, 1204, 116), fill='#3b372d')
    try:
        with Image.open(cover_path) as source:
            if source.width * source.height > 20_000_000:
                raise ValueError('Artwork too large')
            artwork = ImageOps.fit(ImageOps.exif_transpose(source).convert('RGB'), (450, 450))
    except (OSError, ValueError, Image.DecompressionBombError):
        artwork = Image.new('RGB', (450, 450), '#24231e')
        fallback = ImageDraw.Draw(artwork)
        for radius in range(40, 200, 20):
            fallback.ellipse((225-radius, 225-radius, 225+radius, 225+radius), outline='#7a684c', width=2)
        fallback.ellipse((215, 215, 235, 235), fill=gold)
    mask = Image.new('L', (450, 450), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 449, 449), radius=20, fill=255)
    canvas.paste(artwork, (76, 155), mask)
    draw.text((580, 158), 'THE CREATOR’S SELECTION' if owner else 'THE SELECTED RECORD', font=font(16), fill=gold)
    for index, line in enumerate(title_lines(raw_title, font(48, True), 620)):
        draw.text((576, 218 + index * 65), line, font=font(48, True), fill=ivory)
    draw.line((580, 445, 1200, 445), fill='#3b372d')
    draw.text((580, 475), f'{raw_duration}  /  AUDIO SESSION', font=font(21), fill=gold)
    draw.text((580, 536), 'CURATED BY THE CREATOR' if owner else 'SELECTED BY', font=font(14), fill=muted)
    draw.text((580, 563), fit_text('Rishabh Anand' if owner else requester, font(23), 620), font=font(23), fill=ivory)
    draw.text((76, 639), 'YOUR PEOPLE. YOUR MUSIC. YOUR MOMENT.', font=font(14), fill=muted)
    draw.text((1098, 639), 'ALICE', font=font(14), fill=gold)
    # One worker writes a given card at a time; publish only complete JPEGs.
    temporary = output.with_suffix('.tmp')
    canvas.save(temporary, format='JPEG', quality=90, optimize=True)
    temporary.replace(output)
    return str(output)
