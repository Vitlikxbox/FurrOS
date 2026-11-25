"""Wallpaper for the BIOS boot menu (Limine): FurrOS comic look, kept dark on the left where Limine prints the
menu, Pixie on the right. 1024x768: the mode most old BIOS video cards offer; Limine stretches it to the screen.
    python bootloader/furros/make_limine_wallpaper.py   ->  bootloader/furros/limine-furros.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

FUR = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("limine-furros.png")
W, H = 1024, 768
BG, INK, PINK, CYAN, WINE = (30, 18, 24), (14, 8, 11), (255, 85, 119), (127, 240, 240), (120, 28, 52)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
# right panel: a slanted wine-coloured page with diagonal stripes, like FurrBoot's comic spread
panel = [(640, 0), (W, 0), (W, H), (560, H)]
d.polygon(panel, fill=WINE)
stripes = Image.new("L", (W, H), 0)
sd = ImageDraw.Draw(stripes)
for x in range(-H, W, 34):
    sd.line([(x, H), (x + H, 0)], fill=255, width=12)
mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(mask).polygon(panel, fill=255)
stripe_col = Image.new("RGB", (W, H), (140, 36, 64))
img.paste(stripe_col, (0, 0), Image.composite(stripes, Image.new("L", (W, H), 0), mask))
# halftone dots fading in on the dark side, under the menu they stay faint
for y in range(0, H, 14):
    for x in range(0, 600, 14):
        r = max(0, (x - 360) / 240) * 2.2
        if r > 0.3:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(52, 30, 40))
# ink border of the panel
d.line([(640, 0), (560, H)], fill=INK, width=10)
d.line([(646, 0), (566, H)], fill=PINK, width=3)

# Danyok (the FurrOS mascot since 25.11.2026) on the panel, with a white sticker edge
src = Image.open(FUR / "src/academy/web/img/danyok.png").convert("RGBA")
h = 600
pix = src.resize((round(src.width * h / src.height), h), Image.LANCZOS)
edge = pix.split()[3].filter(ImageFilter.MaxFilter(13))
sticker = Image.new("RGBA", pix.size, (255, 255, 255, 0))
sticker.putalpha(edge)
px, py = W - pix.width - 30, H - pix.height - 20
shadow = Image.new("RGBA", pix.size, INK + (255,))
shadow.putalpha(edge)
img.paste(shadow, (px + 10, py + 10), shadow)
img.paste(sticker, (px, py), sticker)
img.paste(pix, (px, py), pix)

# small FurrOS logo bottom left, out of the menu's way
logo = Image.open(FUR / "brand/furros-logo.png").convert("RGBA")
logo = logo.resize((72, round(logo.height * 72 / logo.width)), Image.LANCZOS)
img.paste(logo, (40, H - logo.height - 34), logo)
img.save(OUT, optimize=True)
print(OUT, OUT.stat().st_size)
