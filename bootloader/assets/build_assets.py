"""Prepares what FurrBoot carries inside its .efi file:  python build_assets.py
- fonts: Dela Gothic One + static Nunito 800/900 (OFL, the loader can't use variable fonts)
- art: logo, Pixie, Danyok, lying Pixie as stickers (white outline + ink edge), in QOI format
Output: ../furrboot/assets/ (included with include_bytes!)."""
import struct
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "furrboot" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE.parent / "mockup"))
import make_mockup as mk  # noqa: E402  (sticker() and art() are shared with the mockups)


# Everything the four menu languages can show: Basic Latin + Latin-1 (EN, ES), Latin Extended-A (PL: ą ć ę ł ń ś ź ż),
# Cyrillic (RU), general punctuation (— … « »), №. Entry titles come from the system, so whole blocks, not just the
# letters in i18n.rs.
RANGES = [(0x20, 0x7E), (0xA0, 0xFF), (0x100, 0x17F), (0x400, 0x45F), (0x2010, 0x2027), (0x2030, 0x203A), (0x2116, 0x2116)]


def fonts():
    from fontTools import subset
    src = HERE.parent / "fonts"
    (OUT / "dela.ttf").write_bytes((src / "DelaGothicOne-Regular.ttf").read_bytes())
    # the full Nunito (OFL, D:\FurrOS\fonts): the old copy here was a trimmed web subset without Polish letters
    nunito = HERE.parent.parent / "fonts" / "Nunito.ttf"
    unicodes = [u for a, b in RANGES for u in range(a, b + 1)]
    opts = subset.Options()
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = ["*"]  # keep the copyright / OFL notice
    for w in (700, 800, 900):
        st = instancer.instantiateVariableFont(TTFont(nunito), {"wght": w})
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=unicodes)
        sub.subset(st)
        st.save(OUT / f"nunito-{w}.ttf")


def qoi(im, path):
    """Minimal QOI encoder (qoiformat.org): small, lossless, and the decoder is ~60 lines of Rust."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.tobytes()
    out = bytearray(b"qoif" + struct.pack(">II", w, h) + bytes([4, 0]))
    index = [(0, 0, 0, 0)] * 64
    prev = (0, 0, 0, 255)
    run = 0
    n = w * h
    for i in range(n):
        p = tuple(px[i * 4:i * 4 + 4])
        if p == prev:
            run += 1
            if run == 62 or i == n - 1:
                out.append(0xC0 | (run - 1)); run = 0
            continue
        if run:
            out.append(0xC0 | (run - 1)); run = 0
        h_ = (p[0] * 3 + p[1] * 5 + p[2] * 7 + p[3] * 11) % 64
        if index[h_] == p:
            out.append(h_)
        else:
            index[h_] = p
            if p[3] == prev[3]:
                dr, dg, db = (p[0] - prev[0] + 128) % 256 - 128, (p[1] - prev[1] + 128) % 256 - 128, (p[2] - prev[2] + 128) % 256 - 128
                dr_dg, db_dg = dr - dg, db - dg
                if -2 <= dr <= 1 and -2 <= dg <= 1 and -2 <= db <= 1:
                    out.append(0x40 | (dr + 2) << 4 | (dg + 2) << 2 | (db + 2))
                elif -32 <= dg <= 31 and -8 <= dr_dg <= 7 and -8 <= db_dg <= 7:
                    out += bytes([0x80 | (dg + 32), (dr_dg + 8) << 4 | (db_dg + 8)])
                else:
                    out += bytes([0xFE, p[0], p[1], p[2]])
            else:
                out += bytes([0xFF, *p])
        prev = p
    out += bytes([0] * 7 + [1])
    path.write_bytes(out)
    return len(out)


def art():
    sizes = {}
    # heights are for a 1080p screen; FurrBoot scales them for other resolutions
    sizes["logo"] = qoi(mk.art("logo", 64), OUT / "logo.qoi")
    # v2 splash panel: characters about half the screen tall, at (close to) their source size
    sizes["pixie"] = qoi(mk.sticker(mk.art("pixie", 640), 10), OUT / "pixie.qoi")
    sizes["danyok"] = qoi(mk.sticker(mk.art("danyok", 640), 10), OUT / "danyok.qoi")
    sizes["pixie_lying"] = qoi(mk.sticker(mk.art("pixie-lying", 320), 9), OUT / "pixie_lying.qoi")
    sketch = mk.Image.open(mk.FUR / "src/academy/web/img/danyok-sketch.png").convert("RGBA")
    sketch = sketch.resize((round(sketch.width * 640 / sketch.height), 640), mk.Image.LANCZOS)
    sizes["danyok_sketch"] = qoi(sketch, OUT / "danyok_sketch.qoi")  # already has a white outline
    return sizes


if __name__ == "__main__":
    fonts()
    s = art()
    total = sum(p.stat().st_size for p in OUT.iterdir())
    print("assets:", {p.name: p.stat().st_size for p in sorted(OUT.iterdir())}, "total", total)
