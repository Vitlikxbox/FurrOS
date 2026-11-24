"""Copy generated art into the archiso airootfs tree + make thumbnails and desktop previews."""
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_art as g  # noqa: E402

BRAND = Path(r"D:\FurrOS\brand")
ROOT = Path(r"D:\FurrOS\profile\airootfs")
SHARE = ROOT / "usr/share/furros"
BG = ROOT / "usr/share/backgrounds/furros"
WALLS = ROOT / "usr/share/wallpapers"

for d in (SHARE / "lapa", SHARE / "thumbs", SHARE / "previews", BG, ROOT / "usr/share/fonts/furros",
          ROOT / "usr/share/pixmaps"):
    d.mkdir(parents=True, exist_ok=True)

# wallpapers: plain files for every desktop + Plasma wallpaper packages
for p in sorted(BRAND.glob("furros-*.png")):
    if p.name.startswith(("furros-logo", "furros-lockup")) or p.stem in (
            "furros-pitbull-terrier", "furros-just-be-competent", "furros-bothered"):
        continue  # these became animated wallpapers
    shutil.copy2(p, BG / p.name)
    t = Image.open(p).convert("RGB")
    t.thumbnail((360, 203), Image.LANCZOS)
    t.save(SHARE / "thumbs" / p.name)
    pkg = "FurrOS" if p.stem == "furros-default" else "FurrOS-" + "".join(
        w.capitalize() for w in p.stem.removeprefix("furros-").split("-"))
    img_dir = WALLS / pkg / "contents/images"
    img_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, img_dir / "1920x1080.png")
    (WALLS / pkg / "metadata.json").write_text(
        '{"KPlugin": {"Id": "%s", "Name": "%s", "Authors": [{"Name": "FurrOS"}], "License": "Personal"}}\n'
        % (pkg, pkg.replace("-", " ")), encoding="utf-8")

for p in (BRAND.parent / "art" / "anim-out").glob("anim-*.png"):
    t = Image.open(p).convert("RGB")
    t.thumbnail((360, 203), Image.LANCZOS)
    t.save(SHARE / "thumbs" / p.name)

for p in (BRAND / "lapa").glob("*.png"):
    shutil.copy2(p, SHARE / "lapa" / p.name)
# FurrOS mascot by taroyadda: avatars (KDE and GNOME list these in the user settings) + the installer's picture
for d in (SHARE / "avatars", SHARE / "mascot", ROOT / "usr/share/plasma/avatars", ROOT / "usr/share/pixmaps/faces"):
    d.mkdir(parents=True, exist_ok=True)
for p in (BRAND / "avatars").glob("furros-*.png"):
    for d in (SHARE / "avatars", ROOT / "usr/share/plasma/avatars", ROOT / "usr/share/pixmaps/faces"):
        shutil.copy2(p, d / p.name)
shutil.copy2(BRAND / "mascot-taro" / "mascot-small.png", SHARE / "mascot" / "mascot-small.png")
# Pixie (mascot by dentola69): stickers for the welcome window; the source drawing stays out of the system
(SHARE / "pixie").mkdir(exist_ok=True)
for p in (BRAND / "pixie").glob("pixie-lying*.png"):
    if not p.stem.endswith("-src"):
        shutil.copy2(p, SHARE / "pixie" / p.name)
for name in ("furros-logo.png", "furros-lockup.png", "splash.png"):
    shutil.copy2(BRAND / name, SHARE / name)
# GDM shows its logo at the file's own size: a small lockup that sits under the user list
lock = Image.open(BRAND / "furros-lockup.png")
lock.resize((round(lock.width * 64 / lock.height), 64), Image.LANCZOS).save(SHARE / "furros-gdm-logo.png")
shutil.copy2(BRAND / "furros-logo.png", ROOT / "usr/share/pixmaps/furros.png")
for s in (16, 22, 24, 32, 48, 64, 128, 256):
    d = ROOT / f"usr/share/icons/hicolor/{s}x{s}/apps"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BRAND / f"furros-logo-{s}.png", d / "furros.png")
for f in Path(r"D:\FurrOS\fonts").glob("*"):
    shutil.copy2(f, ROOT / "usr/share/fonts/furros" / f.name)

# plymouth theme images
ply = ROOT / "usr/share/plymouth/themes/furros"
ply.mkdir(parents=True, exist_ok=True)
shutil.copy2(BRAND / "plymouth-logo.png", ply / "logo.png")
shutil.copy2(BRAND / "plymouth-wordmark.png", ply / "wordmark.png")
for i in range(8):
    shutil.copy2(BRAND / f"plymouth-paw{i}.png", ply / f"paw{i}.png")

# grub theme background
grub = ROOT / "usr/share/grub/themes/furros"
grub.mkdir(parents=True, exist_ok=True)
Image.open(BRAND / "furros-default.png").convert("RGB").save(grub / "background.png")


# ---------- desktop layout previews (schematic, drawn in FurrOS colours) ----------
W, H = 480, 270
INK = (14, 8, 11)
WIN = (42, 26, 34)
BAR = (24, 14, 19)
CY, PK, RD, CR = g.CYAN, g.PINK, g.RED, g.CREAM
wall = Image.open(BRAND / "furros-default.png").convert("RGBA").resize((W, H), Image.LANCZOS)


def window(d, box, title=True, accent=CY, radius=8):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=radius, fill=WIN, outline=INK, width=2)
    if title:
        d.rounded_rectangle((x0, y0, x1, y0 + 16), radius=radius, fill=(60, 30, 44), outline=INK, width=2)
        for i, c in enumerate((RD, (255, 190, 90), (120, 230, 160))):
            d.ellipse((x1 - 14 - i * 12, y0 + 4, x1 - 6 - i * 12, y0 + 12), fill=c)
    for i in range(3):
        yy = y0 + (26 if title else 10) + i * 12
        if yy + 6 < y1:
            d.rounded_rectangle((x0 + 10, yy, x0 + 10 + (x1 - x0 - 20) * (0.8 - i * 0.2), yy + 6), radius=3,
                                fill=(90, 60, 72))
    d.rectangle((x0 + 10, y1 - 10, x0 + 40, y1 - 6), fill=accent)


def dots(d, x, y, n, step=18, r=6, colors=(CY, PK, CR, RD)):
    for i in range(n):
        c = colors[i % len(colors)]
        d.rounded_rectangle((x + i * step, y, x + i * step + r * 2, y + r * 2), radius=3, fill=c)


def preview(did):
    im = wall.copy()
    d = ImageDraw.Draw(im)
    if did == "kde":
        window(d, (70, 40, 330, 200))
        window(d, (210, 80, 430, 220), accent=PK)
        d.rectangle((0, H - 26, W, H), fill=BAR)
        d.ellipse((8, H - 22, 26, H - 4), fill=CY)
        dots(d, 40, H - 19, 6, 22, 7)
        d.text((W - 48, H - 21), "12:00", fill=CR)
    elif did == "gnome":
        d.rectangle((0, 0, W, 18), fill=BAR)
        d.text((8, 3), "Обзор", fill=CR)
        d.text((W / 2 - 16, 3), "12:00", fill=CR)
        window(d, (90, 40, 390, 230), title=True, radius=12)
        d.rounded_rectangle((150, H - 34, 330, H - 6), radius=12, fill=(24, 14, 19, 230))
        dots(d, 162, H - 27, 7, 23, 7)
    elif did == "cosmic":
        d.rectangle((0, 0, W, 18), fill=BAR)
        d.text((W / 2 - 16, 3), "12:00", fill=CR)
        window(d, (20, 30, 235, 225), radius=10)
        window(d, (245, 30, 460, 125), radius=10, accent=PK)
        window(d, (245, 132, 460, 225), radius=10, accent=CR)
        d.rounded_rectangle((170, H - 36, 310, H - 8), radius=14, fill=BAR, outline=CY, width=2)
        dots(d, 182, H - 29, 5, 25, 7)
    elif did in ("cinnamon", "xfce", "mate", "lxqt"):
        top = did in ("xfce", "mate")
        bottom = did in ("cinnamon", "lxqt", "mate")
        if top:
            d.rectangle((0, 0, W, 20), fill=BAR)
            d.text((8, 4), "Меню", fill=CY)
            d.text((W - 46, 4), "12:00", fill=CR)
        if bottom:
            d.rectangle((0, H - 26, W, H), fill=BAR)
            d.rounded_rectangle((6, H - 22, 50, H - 4), radius=4, fill=CY)
            dots(d, 62, H - 19, 4, 60, 7, colors=((80, 50, 64),))
        if did == "xfce":
            d.rounded_rectangle((170, H - 30, 310, H - 6), radius=6, fill=BAR)
            dots(d, 180, H - 25, 6, 21, 7)
        for i in range(3):
            d.rounded_rectangle((14, 34 + i * 46, 46, 66 + i * 46), radius=6, fill=(255, 236, 236, 60))
        window(d, (90, 40, 360, 210), radius=4)
        window(d, (220, 90, 450, 225), radius=4, accent=PK)
    elif did == "budgie":
        d.rectangle((0, 0, W, 22), fill=BAR)
        d.ellipse((6, 4, 20, 18), fill=CY)
        d.text((W / 2 - 16, 5), "12:00", fill=CR)
        window(d, (40, 40, 320, 230), radius=8)
        d.rectangle((W - 120, 22, W, H), fill=(30, 16, 24))
        for i in range(4):
            d.rounded_rectangle((W - 110, 34 + i * 50, W - 10, 74 + i * 50), radius=8, fill=WIN)
    elif did == "deepin":
        window(d, (80, 30, 400, 200), radius=10)
        d.rounded_rectangle((120, H - 44, 360, H - 8), radius=14, fill=(24, 14, 19), outline=(90, 60, 72), width=2)
        dots(d, 134, H - 36, 8, 28, 10)
    elif did == "niri":
        d.rounded_rectangle((8, 4, W - 8, 20), radius=8, fill=BAR)
        d.text((W / 2 - 14, 6), "12:00", fill=CR)
        window(d, (-120, 28, 60, H - 10), title=False, radius=10)
        window(d, (75, 28, 300, H - 10), title=False, radius=10, accent=PK)
        d.rounded_rectangle((75, 28, 300, H - 10), radius=10, outline=CY, width=3)
        window(d, (315, 28, 560, H - 10), title=False, radius=10, accent=CR)
        d.polygon([(W - 30, H / 2 - 12), (W - 14, H / 2), (W - 30, H / 2 + 12)], fill=CY)
    elif did in ("hyprland", "sway", "i3", "bspwm", "awesome", "qtile"):
        gap = 10 if did == "hyprland" else 2
        rad = 12 if did == "hyprland" else 0
        top = 26 if did == "hyprland" else 2
        bot = H - (2 if did == "hyprland" else 20)
        if did in ("bspwm", "awesome"):
            gap, rad, top, bot = (8, 4, 24, H) if did == "bspwm" else (0, 0, 20, H)
            d.rectangle((0, 0, W, 18), fill=BAR)
            dots(d, 6, 4, 6, 16, 5, colors=(CY, (60, 40, 50), PK))
            d.text((W - 46, 3), "12:00", fill=CR)
        if did == "hyprland":
            d.rounded_rectangle((gap, 4, W - gap, 20), radius=8, fill=BAR, outline=CY, width=1)
            dots(d, gap + 8, 8, 5, 14, 4)
            d.text((W / 2 - 14, 6), "12:00", fill=CR)
        elif did not in ("bspwm", "awesome"):
            d.rectangle((0, H - 18, W, H), fill=BAR)
            dots(d, 4, H - 15, 4, 16, 6, colors=(CY, (60, 40, 50)))
            d.text((W - 46, H - 15), "12:00", fill=CR)
        mid = W // 2
        window(d, (gap, top, mid - gap // 2, bot - gap), title=False, radius=rad)
        window(d, (mid + gap // 2, top, W - gap, (top + bot) // 2 - gap // 2), title=False, radius=rad, accent=PK)
        window(d, (mid + gap // 2, (top + bot) // 2 + gap // 2, W - gap, bot - gap), title=False, radius=rad,
               accent=CR)
        if did == "hyprland":
            d.rounded_rectangle((gap, top, mid - gap // 2, bot - gap), radius=rad, outline=CY, width=3)
        # terminal-ish text
        f = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 11)
        d.text((gap + 10, top + 10), "furry@furros ~ $ fastfetch", fill=CY, font=f)
    elif did == "console":
        im = Image.new("RGBA", (W, H), (12, 8, 10, 255))
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 13)
        lines = ["FurrOS 1.0  tty1", "", "furros login: furry", "Password:",
                 "", "furry@furros ~ $ bark", "Гав! ", "furry@furros ~ $ _"]
        for i, l in enumerate(lines):
            d.text((16, 16 + i * 20), l, fill=CY if "$" in l else CR, font=f)
    im = im.convert("RGB")
    im.save(SHARE / "previews" / f"{did}.png")


sys.path.insert(0, r"D:\FurrOS\src\installer")
import catalog  # noqa: E402

for de in catalog.DESKTOPS:
    preview(de["id"])
print("staged")
