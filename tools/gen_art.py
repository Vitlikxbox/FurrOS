"""Generate FurrOS branding: logo, wallpapers, boot splashes, plymouth assets."""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ART = Path(r"D:\FurrOS\art")
OUT = Path(r"D:\FurrOS\brand")
OUT.mkdir(parents=True, exist_ok=True)

# Palette taken from the character: striped sweater, eyes, collar, hearts
BLACK = (18, 12, 16)
MAROON = (120, 28, 44)
RED = (226, 58, 68)
CYAN = (127, 240, 240)
PINK = (255, 140, 190)
CREAM = (255, 236, 214)
PURPLE = (190, 150, 255)
WHITE = (255, 255, 255)

F_TITLE = r"C:\Windows\Fonts\seguibl.ttf"
F_IMPACT = r"C:\Windows\Fonts\impact.ttf"
F_UI = r"C:\Windows\Fonts\segoeuib.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------- primitives ----------
def bolt(d, cx, cy, s, fill, outline=None, width=0):
    pts = [(-0.15, -1), (0.45, -1), (0.1, -0.15), (0.5, -0.15), (-0.35, 1), (-0.05, 0.15), (-0.45, 0.15)]
    pts = [(cx + x * s, cy + y * s) for x, y in pts]
    d.polygon(pts, fill=fill, outline=outline, width=width)


def paw(d, cx, cy, s, fill, outline=None, width=0, angle=0.0):
    def rot(x, y):
        a = math.radians(angle)
        return cx + (x * math.cos(a) - y * math.sin(a)) * s, cy + (x * math.sin(a) + y * math.cos(a)) * s

    def ell(x, y, rx, ry):
        px, py = rot(x, y)
        d.ellipse([px - rx * s, py - ry * s, px + rx * s, py + ry * s], fill=fill, outline=outline, width=width)

    ell(0, 0.35, 0.62, 0.52)
    for x, y in [(-0.72, -0.25), (-0.27, -0.72), (0.27, -0.72), (0.72, -0.25)]:
        ell(x, y, 0.22, 0.29)


def bone(d, cx, cy, s, fill, outline=None, width=0, angle=0.0):
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    L, T, R = 0.9 * s, 0.22 * s, 0.26 * s
    quad = [(cx - ux * L + vx * T, cy - uy * L + vy * T), (cx + ux * L + vx * T, cy + uy * L + vy * T),
            (cx + ux * L - vx * T, cy + uy * L - vy * T), (cx - ux * L - vx * T, cy - uy * L - vy * T)]
    for sgn in (-1, 1):
        for side in (-1, 1):
            bx = cx + sgn * ux * L + side * vx * R * 0.85
            by = cy + sgn * uy * L + side * vy * R * 0.85
            d.ellipse([bx - R, by - R, bx + R, by + R], fill=fill, outline=outline, width=width)
    d.polygon(quad, fill=fill)


def star(d, cx, cy, s, fill, outline=None, width=0, angle=0.0):
    pts = []
    for i in range(10):
        r = s if i % 2 == 0 else s * 0.45
        a = math.radians(angle + i * 36 - 90)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline, width=width)


def heart(d, cx, cy, s, fill):
    pts = []
    for i in range(80):
        t = 2 * math.pi * i / 80
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s / 17, cy + y * s / 17))
    d.polygon(pts, fill=fill)


def gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def stripes(img, color, alpha, width, angle_shift):
    """Sweater stripes, diagonal."""
    w, h = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x in range(-h, w + h, width * 2):
        d.polygon([(x, 0), (x + width, 0), (x + width - angle_shift, h), (x - angle_shift, h)], fill=color + (alpha,))
    img.alpha_composite(layer)


def scatter(img, seed, n, alpha=40):
    rnd = random.Random(seed)
    w, h = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        s = rnd.uniform(14, 46) * w / 1920
        kind = rnd.choice("pbshz")
        col = rnd.choice([CYAN, PINK, CREAM, RED, PURPLE]) + (alpha,)
        if kind == "p":
            paw(d, x, y, s, col, angle=rnd.uniform(-40, 40))
        elif kind == "b":
            bone(d, x, y, s, col, angle=rnd.uniform(0, 180))
        elif kind == "s":
            star(d, x, y, s, col, angle=rnd.uniform(0, 72))
        elif kind == "h":
            heart(d, x, y, s, col)
        else:
            bolt(d, x, y, s, col)
    img.alpha_composite(layer)


# ---------- logo ----------
LOGO_ASCII = r"""
$1         ▄███▄     ▄███▄
$1         █████     █████
$1  ▄███▄   ▀▀▀       ▀▀▀   ▄███▄
$1  █████                   █████
$1   ▀▀▀     ▄▄▄█████▄▄▄     ▀▀▀
$1        ▄██████$2▄▄▄▄$1██████▄
$1       ████████$2▄██▀$1████████
$1      ████████$2▄██████$1███████
$1      ██████████$2▄██▀$1████████
$1       ███████$2▄█▀$1██████████
$1        ▀██████████████████▀
$1           ▀▀▀▀▀▀▀▀▀▀▀▀▀
"""
PAW = (255, 244, 236)   # cream fur
BOLT = RED


def ascii_grid():
    """ASCII paw -> 2D grid of colours; every char is 1 px wide and 2 px tall (▀ top, ▄ bottom, █ both)."""
    rows = [l for l in LOGO_ASCII.strip("\n").split("\n")]
    cells = []
    for line in rows:
        col, x, out = PAW, 0, []
        i = 0
        while i < len(line):
            if line.startswith("$1", i):
                col = PAW; i += 2; continue
            if line.startswith("$2", i):
                col = BOLT; i += 2; continue
            out.append((line[i], col))
            i += 1
        cells.append(out)
    w = max(len(r) for r in cells)
    grid = [[None] * w for _ in range(len(cells) * 2)]
    for y, r in enumerate(cells):
        for x, (ch, col) in enumerate(r):
            if ch in "█▀":
                grid[y * 2][x] = col
            if ch in "█▄":
                grid[y * 2 + 1][x] = col
    # trim empty borders
    ys = [y for y, r in enumerate(grid) if any(r)]
    xs = [x for x in range(w) if any(grid[y][x] for y in range(len(grid)))]
    return [row[xs[0]:xs[-1] + 1] for row in grid[ys[0]:ys[-1] + 1]]


def logo(size=1024):
    grid = ascii_grid()
    gh, gw = len(grid), len(grid[0])
    # chars are ~2x taller than wide, so a cell is 1 wide : 1 tall after the half-block split
    cell = int(size * 0.84 / max(gw, gh))
    art = Image.new("RGBA", (gw * cell, gh * cell), (0, 0, 0, 0))
    d = ImageDraw.Draw(art)
    for y, row in enumerate(grid):
        for x, col in enumerate(row):
            if col:
                d.rectangle([x * cell, y * cell, (x + 1) * cell - 1, (y + 1) * cell - 1], fill=col + (255,))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox, oy = (size - art.width) // 2, (size - art.height) // 2
    alpha = Image.new("L", (size, size), 0)
    alpha.paste(art.split()[3], (ox, oy))
    ink = alpha.filter(ImageFilter.MaxFilter(max(3, (size // 40) | 1)))
    shadow = ink.filter(ImageFilter.GaussianBlur(size / 80))
    img.paste((0, 0, 0, 140), (size // 60, size // 45), shadow)
    img.paste(BLACK + (255,), (0, 0), ink)
    img.alpha_composite(art, (ox, oy))
    return img


def logo_old(size=1024):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, s = size / 2, size * 0.36
    # shadow
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    paw(ImageDraw.Draw(sh), c + size * 0.02, c + size * 0.03, s, (0, 0, 0, 160))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size / 60)))
    paw(d, c, c, s, BLACK)
    paw(d, c, c, s * 0.9, CYAN)
    # lightning bolt in the main pad (the red streak from the hair)
    bolt(d, c, c + s * 0.35, s * 0.42, BLACK)
    bolt(d, c, c + s * 0.35, s * 0.34, RED)
    # bone clip on top-right toe
    bone(d, c + s * 0.62, c - s * 0.86, s * 0.26, BLACK, angle=-35)
    bone(d, c + s * 0.62, c - s * 0.86, s * 0.21, CREAM, angle=-35)
    return img


def wordmark(h=220):
    f = font(F_TITLE, h)
    t1, t2 = "Furr", "OS"
    w1 = f.getlength(t1)
    w2 = f.getlength(t2)
    img = Image.new("RGBA", (int(w1 + w2 + h * 0.4), int(h * 1.45)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    o = max(4, h // 18)
    for txt, x, col in [(t1, h * 0.1, WHITE), (t2, h * 0.1 + w1, RED)]:
        d.text((x, h * 0.05), txt, font=f, fill=col, stroke_width=o, stroke_fill=BLACK)
    return img


def lockup(h=220):
    lg = logo(int(h * 1.9))
    wm = wordmark(h)
    img = Image.new("RGBA", (lg.width + wm.width, max(lg.height, wm.height)), (0, 0, 0, 0))
    img.alpha_composite(lg, (0, (img.height - lg.height) // 2))
    img.alpha_composite(wm, (lg.width - int(h * 0.15), (img.height - wm.height) // 2 + int(h * 0.05)))
    return img


def paste_center(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


# ---------- wallpapers ----------
def wall_default(w=1920, h=1080, name="furros-default"):
    img = gradient(w, h, (40, 10, 22), BLACK).convert("RGBA")
    stripes(img, MAROON, 70, int(w / 16), int(w / 10))
    scatter(img, 7, 140, 45)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([w * 0.25, h * 0.15, w * 0.75, h * 0.85], fill=CYAN + (45,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(w / 12)))
    lk = lockup(int(h * 0.16))
    paste_center(img, lk, w / 2, h * 0.47)
    sub = font(F_UI, int(h * 0.028))
    d = ImageDraw.Draw(img)
    txt = "~ arch-based  •  good dogs only ~"
    d.text((w / 2, h * 0.66), txt, font=sub, fill=CREAM, anchor="mm", stroke_width=3, stroke_fill=BLACK)
    img.convert("RGB").save(OUT / f"{name}.png")
    return img


def wall_pink(w=1920, h=1080):
    img = gradient(w, h, (255, 214, 232), (230, 190, 255)).convert("RGBA")
    rnd = random.Random(3)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(0, h + 120, 120):
        for x in range(0, w + 120, 120):
            heart(d, x + (60 if (y // 120) % 2 else 0), y, 30, (255, 255, 255, 90))
    img.alpha_composite(layer)
    scatter(img, 11, 40, 90)
    lk = lockup(int(h * 0.15))
    paste_center(img, lk, w / 2, h / 2)
    img.convert("RGB").save(OUT / "furros-bubblegum.png")


def wall_from_thumb(src, name, w=1920, h=1080, accent=CYAN):
    th = Image.open(src).convert("RGB")
    # blurred fill + sharp art on the left/center
    bg = th.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28)).convert("RGBA")
    dark = Image.new("RGBA", (w, h), BLACK + (110,))
    bg.alpha_composite(dark)
    art = th.resize((int(h * 0.86 * th.width / th.height), int(h * 0.86)), Image.LANCZOS).convert("RGBA")
    # sticker frame
    frame = Image.new("RGBA", (art.width + 24, art.height + 24), WHITE + (255,))
    frame.alpha_composite(art, (12, 12))
    fr = frame.rotate(-2.5, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", fr.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 170), mask=fr.split()[3])
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (int((w - fr.width) / 2) + 14, int((h - fr.height) / 2) + 18))
    bg.alpha_composite(fr, (int((w - fr.width) / 2), int((h - fr.height) / 2)))
    scatter(bg, hash(name) % 1000, 30, 120)
    lk = lockup(54)
    bg.alpha_composite(lk, (w - lk.width - 30, h - lk.height - 20))
    bg.convert("RGB").save(OUT / f"{name}.png")


LAPA_POSES = {
    "wave": "06 26 2026.png",
    "grr": "06 06 2026.png",
    "timer": "photo_2026-09-05_20-58-48.jpg",
    "hoodie": "photo_2026-09-05_20-53-15.jpg",
    "sip": "photo_2026-09-05_20-49-40.jpg",
    "heart": "photo_2026-09-30_10-42-28.jpg",  # wallpaper only: the shirt text is too much for the installer/site
}


def cutout(src, max_side=1400):
    """Remove the white paper around line art and the handwritten captions."""
    import numpy as np
    from scipy import ndimage

    im = Image.open(src).convert("RGB")
    im.thumbnail((max_side, max_side), Image.LANCZOS)
    a = np.asarray(im).astype(np.int16)
    white = (a.min(axis=2) > 232)
    lab, _ = ndimage.label(white)
    h, w = white.shape
    # background = white regions touching top/left/right edges (figures are cut at the bottom)
    seeds = set(np.unique(lab[0, :])) | set(np.unique(lab[:, 0])) | set(np.unique(lab[:, -1]))
    seeds.discard(0)
    bg = np.isin(lab, list(seeds))
    fg = ~bg
    flab, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(fg, flab, range(1, n + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * 0.12]
        fg = np.isin(flab, keep)
    fg = ndimage.binary_fill_holes(fg)
    alpha = (fg * 255).astype(np.uint8)
    out = im.convert("RGBA")
    out.putalpha(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.7)))
    return out.crop(out.getbbox())


def sticker(img, border=14, ink=4):
    """White die-cut border + thin ink line + soft shadow, like a vinyl sticker."""
    a = img.split()[3]
    pad = border + ink + 30
    canvas = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    big = Image.new("L", canvas.size, 0)
    big.paste(a, (pad, pad))
    white = big.filter(ImageFilter.MaxFilter(border * 2 + 1))
    inkm = white.filter(ImageFilter.MaxFilter(ink * 2 + 1))
    shadow = inkm.filter(ImageFilter.GaussianBlur(12))
    canvas.paste((0, 0, 0, 150), (8, 12), shadow)
    canvas.paste(BLACK + (255,), (0, 0), inkm)
    canvas.paste(WHITE + (255,), (0, 0), white)
    canvas.alpha_composite(img, (pad, pad))
    return canvas


def dalmatian_bg(w, h, seed=1):
    img = gradient(w, h, (44, 22, 34), (16, 10, 14)).convert("RGBA")
    rnd = random.Random(seed)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(int(w * h / 9000)):
        x, y = rnd.uniform(-40, w + 40), rnd.uniform(-40, h + 40)
        r = rnd.uniform(6, 34) * w / 1920
        d.ellipse([x - r, y - r * rnd.uniform(0.7, 1.1), x + r, y + r], fill=(255, 236, 236, rnd.randint(8, 20)))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5)))
    scatter(img, seed + 40, 26, 55)
    return img


def lapa_assets():
    folder = ART / "lapa"
    if not folder.exists():
        return
    mdir = OUT / "lapa"
    mdir.mkdir(exist_ok=True)
    for i, (pose, fname) in enumerate(LAPA_POSES.items()):
        src = folder / fname
        if not src.exists():
            continue
        cut = cutout(src)
        st = sticker(cut)
        st.save(mdir / f"lapa-{pose}.png")
        small = st.copy()
        small.thumbnail((520, 520), Image.LANCZOS)
        small.save(mdir / f"lapa-{pose}-small.png")
        # wallpaper: sticker on the right, FurrOS lockup on the left. Small sources are scaled up too;
        # art cut off at the bottom of the drawing sits lower so its straight edge stays off screen
        w, h = 1920, 1080
        bg = dalmatian_bg(w, h, seed=i + 3)
        cut_bottom = (cut.getchannel("A").crop((0, cut.height - 1, cut.width, cut.height)).histogram()[255]
                      > cut.width * 0.2)
        k = min(w * 0.5 / st.width, h * (1.04 if cut_bottom else 0.92) / st.height)
        s = st.resize((round(st.width * k), round(st.height * k)), Image.LANCZOS)
        rot = s.rotate(-3 if i % 2 else 3, expand=True, resample=Image.BICUBIC)
        drop = int(h * (0.09 if cut_bottom else 0.0))
        bg.alpha_composite(rot, (w - rot.width - int(w * 0.04), h - rot.height + drop))
        lk = lockup(int(h * 0.11))
        bg.alpha_composite(lk, (int(w * 0.06), int(h * 0.36)))
        d = ImageDraw.Draw(bg)
        d.text((int(w * 0.075), int(h * 0.36) + lk.height + 10), "Лапа одобряет  •  Lapa approves",
               font=font(F_UI, 34), fill=CREAM, stroke_width=3, stroke_fill=BLACK)
        bg.convert("RGB").save(OUT / f"furros-lapa-{pose}.png")


# Velvet (art: sxshely) and Mimi (art: crispytyph), 25.11.2026: cut out without a sticker rim (the user's choice)
# in brand/замена-тарояды/cut. (cutout, wallpaper name, caption, full body?)
CHARACTERS = [
    ("velvet.png", "furros-velvet", "Велвет одобряет  •  Velvet approves", True),
    ("velvet-2.png", "furros-velvet-2", "Велвет одобряет  •  Velvet approves", False),
    ("mimi.png", "furros-mimi", "Мими одобряет  •  Mimi approves", True),
]


def character_walls():
    """Static wallpapers with Velvet and Mimi: the plain cutout (no white rim) on the FurrOS background."""
    for i, (src_name, name, caption, full_body) in enumerate(CHARACTERS):
        src = OUT / "замена-тарояды" / "cut" / src_name
        if not src.exists():
            continue
        st = Image.open(src).convert("RGBA")
        w, h = 1920, 1080
        bg = dalmatian_bg(w, h, seed=i + 21)
        # a full figure stands inside the frame; a half figure is cut by the bottom edge, so it sits lower
        k = min(w * 0.5 / st.width, h * (0.86 if full_body else 1.0) / st.height)
        s = st.resize((round(st.width * k), round(st.height * k)), Image.LANCZOS)
        # the white sticker rim, like the other characters (the user asked for it after seeing them without)
        s = sticker(s, border=12, ink=4)
        x = w - s.width - int(w * 0.05)
        y = h - s.height + (0 if full_body else int(h * 0.09))
        bg.alpha_composite(s, (x, y))
        lk = lockup(int(h * 0.11))
        bg.alpha_composite(lk, (int(w * 0.06), int(h * 0.36)))
        d = ImageDraw.Draw(bg)
        d.text((int(w * 0.075), int(h * 0.36) + lk.height + 10), caption,
               font=font(F_UI, 34), fill=CREAM, stroke_width=3, stroke_fill=BLACK)
        bg.convert("RGB").save(OUT / f"{name}.png")


def syslinux_splash():
    w, h = 640, 480
    img = gradient(w, h, (40, 10, 22), BLACK).convert("RGBA")
    stripes(img, MAROON, 60, 40, 64)
    scatter(img, 5, 40, 40)
    lk = lockup(52)
    paste_center(img, lk, w / 2, 70)
    img.convert("RGB").save(OUT / "splash.png")


def plymouth():
    lg = logo(360)
    lg.save(OUT / "plymouth-logo.png")
    wm = wordmark(70)
    wm.save(OUT / "plymouth-wordmark.png")
    for i in range(8):
        im = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
        paw(ImageDraw.Draw(im), 20, 22, 15, (PAW if i % 2 == 0 else RED) + (255,))
        im.save(OUT / f"plymouth-paw{i}.png")


def sddm_bg():
    img = wall_default(1920, 1080, "sddm-background")


def icons():
    lg = logo(512)
    lg.save(OUT / "furros-logo.png")
    for s in (16, 22, 24, 32, 48, 64, 128, 256):
        lg.resize((s, s), Image.LANCZOS).save(OUT / f"furros-logo-{s}.png")
    lockup(160).save(OUT / "furros-lockup.png")


if __name__ == "__main__":
    icons()
    wall_default()
    wall_pink()
    thumbs = {
        "yt_wP_7-zq_zio.jpg": "furros-just-be-competent",
        "yt_xjqfhoIGWSE.jpg": "furros-pitbull-terrier",
        "yt_sTMv_SLr0eg.jpg": "furros-bothered",
    }
    for src, name in thumbs.items():
        wall_from_thumb(ART / src, name)
    # any extra art the user drops into art/taro becomes a wallpaper too
    lapa_assets()
    for folder in ("taro",):
        files = sorted((ART / folder).glob("*.*")) if (ART / folder).exists() else []
        for i, p in enumerate(files):
            try:
                wall_from_thumb(p, f"furros-{folder}-{i + 1}")
            except Exception as e:  # noqa: BLE001
                print("skip", p, e, file=sys.stderr)
    syslinux_splash()
    plymouth()
    sddm_bg()
    print("ok", sorted(p.name for p in OUT.iterdir()))
