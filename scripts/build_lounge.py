"""Build the local typography-based listening-room cover; no runtime network fetch."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

ROOT = Path(__file__).resolve().parents[1]
def build():
    image = Image.new('RGB', (1280, 720), '#10110f')
    draw = ImageDraw.Draw(image)
    gold, ivory, muted = '#c5a474', '#f4ecdd', '#96958a'
    def font(size, bold=False):
        return ImageFont.truetype(str(ROOT / 'assets' / ('Montserrat-Bold.ttf' if bold else 'Montserrat-Regular.ttf')), size)
    draw.rectangle((30, 30, 1249, 689), outline='#3b372d', width=1)
    draw.text((76, 72), 'A L I C E   /   M U S I C   A T E L I E R', font=font(18), fill=gold)
    draw.line((76, 125, 1204, 125), fill='#3b372d')
    # A restrained record motif, engraved in warm gold.
    cx, cy = 1030, 375
    for radius in range(94, 286, 15):
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline='#353128', width=1)
    draw.ellipse((cx-75, cy-75, cx+75, cy+75), fill='#c5a474')
    draw.ellipse((cx-61, cy-61, cx+61, cy+61), outline='#685638', width=1)
    draw.ellipse((cx-8, cy-8, cx+8, cy+8), fill='#10110f')
    draw.text((76, 205), 'The listening', font=font(76, True), fill=ivory)
    draw.text((76, 296), 'room.', font=font(104, True), fill=ivory)
    draw.text((80, 444), 'Your people. Your music. Your moment.', font=font(23), fill=muted)
    draw.line((80, 523, 660, 523), fill='#3b372d')
    draw.text((80, 552), 'PRESS PLAY. STAY A WHILE.', font=font(17), fill=gold)
    draw.text((80, 631), 'PRIVATE SESSIONS  /  TELEGRAM', font=font(14), fill=muted)
    draw.text((1095, 631), 'VOL. 01', font=font(14), fill=gold)
    target = ROOT / 'assets/lounge.jpg'
    image.save(target, quality=92, optimize=True)
    return target
if __name__ == '__main__':
    print(build())
