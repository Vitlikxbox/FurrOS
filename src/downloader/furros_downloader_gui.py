#!/usr/bin/env python3
"""FurrOS Downloader — the window. Lapa, Velvet and Danyok walk the person through downloading the FurrOS ISO:
a short intro scene, the download with a paw-print progress bar and Velvet's tips, Danyok gluing the parts together,
the check, and a little celebration. On Linux it can also write the ISO to a USB stick.

    python3 furros_downloader_gui.py              the latest public build
    python3 furros_downloader_gui.py --demo       the whole show without downloading anything (for screenshots)
    python3 furros_downloader_gui.py --repo owner/name --tag test-xxxx   (GITHUB_TOKEN for a private repository)
"""
import argparse
import math
import os
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import (QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRectF, Qt, QThread, QTimer,
                            QUrl, QVariantAnimation, Signal)
from PySide6.QtGui import (QColor, QConicalGradient, QDesktopServices, QFont, QFontDatabase, QIcon, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QGraphicsDropShadowEffect,
                               QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStackedLayout,
                               QVBoxLayout, QWidget)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import furros_dl_core as core  # noqa: E402
import furros_dl_i18n as I18N  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "assets"
C = dict(bg="#1E1218", bg2="#2A1A22", surface="#2A1A22", surface2="#3A2430", text="#FFECEC", dim="#C8AAB4",
         cyan="#7FF0F0", pink="#FF8CBE", red="#E23A44", maroon="#781C2C", ok="#78E6A0", warn="#FFBE5A",
         ink="#0E080B", cream="#FFF6F0", lemon="#FFD84A")
# the name tag colour of each character's speech bubble
VOICE = {"lapa": C["pink"], "pixie": C["cyan"], "danyok": C["lemon"]}
LANG = "ru"
RU = True
LINUX = sys.platform.startswith("linux")


def T(ru, en):
    """Russian and English sit next to each other in the code; Polish and Spanish come from furros_dl_i18n."""
    if LANG == "ru":
        return ru
    if LANG == "en":
        return en
    return I18N.TR.get(en, (en, en))[0 if LANG == "pl" else 1]


def F(key, *args):
    return I18N.FMT[key][LANG].format(*args)


def pix(name):
    return QPixmap(str(ASSETS / name))


QSS = f"""
* {{ font-family: Nunito; color: {C['text']}; }}
QLabel#title {{ font-size: 36px; font-weight: 900; }}
QLabel#big {{ font-size: 50px; font-weight: 900; color: {C['cyan']}; }}
QLabel#dim {{ color: {C['dim']}; font-size: 14px; }}
QLabel#stage {{ font-size: 20px; font-weight: 800; }}
QLabel#chip {{ background: {C['maroon']}; border: 2px solid {C['ink']}; border-radius: 10px; padding: 2px 10px;
               font-size: 12px; font-weight: 900; }}
QWidget#card {{ background: {C['surface']}; border: 3px solid {C['ink']}; border-radius: 18px; }}
QPushButton {{ background: {C['surface2']}; border: 3px solid {C['ink']}; border-radius: 14px; padding: 9px 22px;
               font-size: 15px; font-weight: 800; }}
QPushButton:hover {{ background: #4A2E3C; }}
QPushButton:focus {{ border-color: {C['pink']}; }}
QPushButton:checked {{ background: {C['maroon']}; border-color: {C['pink']}; }}
QPushButton:disabled {{ color: #7A6068; }}
QPushButton#go {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {C['pink']}, stop:1 {C['cyan']});
                  color: {C['ink']}; font-size: 20px; font-weight: 900; padding: 13px 44px; border-radius: 20px; }}
QPushButton#go:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #FFA4CC, stop:1 #A4FFFF); }}
QPushButton#go:disabled {{ background: #3E5A5C; color: #1E2A2B; }}
QPushButton#skip {{ background: rgba(14,8,11,0.55); border: 2px solid {C['ink']}; font-size: 13px; padding: 6px 16px; }}
QLineEdit {{ background: {C['bg']}; border: 3px solid {C['ink']}; border-radius: 12px; padding: 8px 12px;
             font-size: 14px; }}
QLineEdit:focus {{ border-color: {C['pink']}; }}
QCheckBox {{ font-size: 14px; spacing: 10px; }}
QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 7px; border: 3px solid {C['ink']};
                        background: {C['surface2']}; }}
QCheckBox::indicator:checked {{ background: {C['cyan']}; }}
QCheckBox::indicator:disabled {{ border-color: #6E5560; }}
"""

TIPS = [
    ("В FurrOS 17 рабочих столов — от уютной KDE до плиточного Hyprland. Выберешь в установщике!",
     "FurrOS has 17 desktops — from cosy KDE to tiling Hyprland. You pick one in the installer!"),
    ("Школа Лапы научит основам Linux прямо после установки. Без скучных лекций, обещаю.",
     "Lapa's School teaches Linux basics right after install. No boring lectures, promise."),
    ("Снимки системы: если обновление что-то сломает, выбери снимок в меню загрузки — и всё как было.",
     "System snapshots: if an update breaks something, pick a snapshot in the boot menu — and it's all back."),
    ("Живые обои двигаются прямо на рабочем столе. Мои любимые — с Лапой.",
     "Live wallpapers move right on your desktop. My favourites are the Lapa ones."),
    ("FurrOS встаёт рядом с Windows: при включении выбираешь систему.",
     "FurrOS installs next to Windows: you choose the system when the computer starts."),
    ("Драйверы видеокарты ставятся сами, даже для старых NVIDIA GTX 10xx.",
     "Graphics drivers install themselves, even for older NVIDIA GTX 10xx cards."),
    ("Установщик говорит на 4 языках, а саму систему можно поставить на одном из 51 — с фонетическими раскладками.",
     "The installer speaks 4 languages, and the system itself comes in any of 51 — with phonetic layouts too."),
    ("Меню загрузки у FurrOS своё — FurrBoot: с мышкой, темами и снимками системы. И со мной!",
     "FurrOS has its own boot menu, FurrBoot: with a mouse, themes and system snapshots. And with me!"),
    ("Флешку удобно записать через Rufus (режим DD) или Ventoy.",
     "A handy way to write the stick: Rufus (DD mode) or Ventoy."),
    ("Если интернет оборвётся — ничего страшного, загрузка продолжится с того же места.",
     "If the internet drops — no worries, the download resumes from the same point."),
]


# ------------------------------------------------------------------ animated pieces

class Backdrop(QWidget):
    """Maroon stripes drifting slowly and paw prints floating up — the FurrOS look, alive."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.paw = pix("paw.png")
        self.t = 0.0
        self.parts = [self._particle(initial=True) for _ in range(26)]
        self.timer = QTimer(self, interval=33, timeout=self._tick)
        self.timer.start()

    def _particle(self, initial=False):
        w, h = max(self.width(), 960), max(self.height(), 640)
        return dict(x=random.uniform(0, w), y=random.uniform(0, h) if initial else h + 30, s=random.uniform(14, 34),
                    v=random.uniform(0.25, 0.9), r=random.uniform(0, 360), vr=random.uniform(-0.6, 0.6),
                    a=random.uniform(0.05, 0.16), heart=random.random() < 0.3)

    def _tick(self):
        self.t += 0.033
        for i, p in enumerate(self.parts):
            p["y"] -= p["v"]
            p["x"] += math.sin(self.t + i) * 0.25
            p["r"] += p["vr"]
            if p["y"] < -40:
                self.parts[i] = self._particle()
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#2B1620"))
        g.setColorAt(1, QColor(C["bg"]))
        p.fillRect(self.rect(), g)
        # diagonal stripes, drifting
        p.save()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(120, 28, 44, 34))
        off = (self.t * 12) % 120
        p.translate(-off, 0)
        p.shear(-0.6, 0)
        for x in range(-200, self.width() + 800, 120):
            p.drawRect(QRectF(x, 0, 52, self.height()))
        p.restore()
        for q in self.parts:
            p.save()
            p.setOpacity(q["a"])
            p.translate(q["x"], q["y"])
            p.rotate(q["r"])
            s = q["s"]
            if q["heart"]:
                path = QPainterPath()
                path.moveTo(0, s * 0.3)
                path.cubicTo(-s * 0.6, -s * 0.2, -s * 0.2, -s * 0.6, 0, -s * 0.2)
                path.cubicTo(s * 0.2, -s * 0.6, s * 0.6, -s * 0.2, 0, s * 0.3)
                p.fillPath(path, QColor(C["pink"]))
            else:
                p.drawPixmap(QRectF(-s / 2, -s / 2, s, s), self.paw, QRectF(self.paw.rect()))
            p.restore()


class Actor(QWidget):
    """A character: slides in with a bounce, breathes (idle bob), hops, shakes, swaps poses."""

    def __init__(self, image, height, parent=None, flip=False, head=0.5):
        super().__init__(parent)
        self.head_x = 1 - head if flip else head  # where the head is, as a share of the picture's width
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.h = height
        self.flip = flip
        self._bob = 0.0
        self._hop = 0.0
        self._shake = 0.0
        self.home = QPoint(0, 0)
        self.set_image(image)
        self.idle = QVariantAnimation(self, startValue=0.0, endValue=2 * math.pi, duration=2600, loopCount=-1)
        self.idle.valueChanged.connect(lambda v: self._set("_bob", math.sin(v) * 5))
        self.idle.start()

    def set_image(self, image):
        pm = pix(image) if isinstance(image, str) else image
        pm = pm.scaledToHeight(self.h, Qt.SmoothTransformation)
        if self.flip:
            pm = pm.transformed(QTransform().scale(-1, 1))
        self.pm = pm
        self.setFixedSize(pm.width(), pm.height() + 30)
        self.update()

    def _set(self, name, v):
        setattr(self, name, v)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        # soft shadow under the feet, smaller while in the air
        lift = self._hop + max(self._bob, 0)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        sw = self.width() * (0.55 - lift / 200)
        p.drawEllipse(QRectF((self.width() - sw) / 2, self.height() - 22, sw, 14))
        p.drawPixmap(int(self._shake), int(18 - self._hop - self._bob), self.pm)

    def hop(self, height=34, ms=420):
        a = QVariantAnimation(self, startValue=0.0, endValue=math.pi, duration=ms)
        a.valueChanged.connect(lambda v: self._set("_hop", math.sin(v) * height))
        a.start(QPropertyAnimation.DeleteWhenStopped)

    def shake(self):
        a = QVariantAnimation(self, startValue=0.0, endValue=6 * math.pi, duration=520)
        a.valueChanged.connect(lambda v: self._set("_shake", math.sin(v) * 9 * (1 - v / (6 * math.pi))))
        a.start(QPropertyAnimation.DeleteWhenStopped)

    def place(self, pos):
        self.home = QPoint(pos)
        self.move(pos)

    def head(self):
        """Top middle of the picture at its resting spot: where a speech bubble's tail points."""
        return QPoint(self.home.x() + int(self.width() * self.head_x), self.home.y() + 18)

    def slide_in(self, start, end, ms=700, delay=0):
        self.home = QPoint(end)
        self.move(start)
        self.show()
        a = QPropertyAnimation(self, b"pos", self, duration=ms, startValue=start, endValue=end,
                               easingCurve=QEasingCurve.OutBack)
        QTimer.singleShot(delay, lambda: a.start(QPropertyAnimation.DeleteWhenStopped))
        return a

    def slide_out(self, end, ms=450):
        a = QPropertyAnimation(self, b"pos", self, duration=ms, startValue=self.pos(), endValue=end,
                               easingCurve=QEasingCurve.InBack)
        a.finished.connect(self.hide)
        a.start(QPropertyAnimation.DeleteWhenStopped)


class Bubble(QWidget):
    """Speech bubble of the FurrOS look (cream box, ink outline, hard shadow, the speaker's name on a coloured tag).
    say(actor, ...) puts it right above that character, the tail pointing straight down at the head, so it's
    always clear who talks. The text types itself out."""

    TAIL, SHADOW, GAP = 22, 5, 4

    def __init__(self, parent=None, tail=None, width=380):
        super().__init__(parent)
        self.tail_x = width / 2
        self.setFixedWidth(width)
        self.lbl = QLabel(self)
        self.lbl.setWordWrap(True)
        self.lbl.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {C['bg']};")
        self.name = QLabel(self)
        self.color = C["pink"]
        self.full = ""
        self.typer = QTimer(self, interval=16, timeout=self._type)
        self.op = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.op)

    def say(self, actor, who, text, voice="lapa"):
        self.hide()
        self.color = VOICE.get(voice, C["pink"])
        self.name.setText(who.upper())
        self.name.setStyleSheet(f"font-size: 12px; font-weight: 900; color: {C['ink']}; background: {self.color};"
                                f"border: 2px solid {C['ink']}; border-radius: 9px; padding: 1px 10px;")
        self.name.adjustSize()
        self.full, self.n = text, 0
        self.lbl.setText("")
        self.lbl.setFixedWidth(self.width() - 52 - self.SHADOW)
        self.lbl.setText(text)
        self.lbl.adjustSize()
        h = self.lbl.height() + 58 + self.TAIL + self.SHADOW
        self.setFixedHeight(h)
        self.name.move(20, 0)
        self.lbl.move(24, 30)
        self.lbl.setText("")
        self.aim(actor)
        self.typer.start()
        fade = QPropertyAnimation(self.op, b"opacity", self, duration=250, startValue=0.0, endValue=1.0)
        fade.start(QPropertyAnimation.DeleteWhenStopped)
        self.show()

    def aim(self, actor):
        """Stand right above the actor: centred on it when there's room, the tail always on its head."""
        head = actor.head()
        pw = self.parentWidget().width()
        x = min(max(head.x() - self.width() // 2, 14), pw - self.width() - 14)
        self.tail_x = min(max(head.x() - x, 34), self.width() - 34 - self.SHADOW)
        self.move(x, head.y() - self.height() + self.GAP)
        self.update()

    def finish_typing(self):
        if self.typer.isActive():
            self.typer.stop()
            self.lbl.setText(self.full)
            return True
        return False

    def typing(self):
        return self.typer.isActive()

    def _type(self):
        self.n += 2
        self.lbl.setText(self.full[:self.n])
        if self.n >= len(self.full):
            self.typer.stop()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        sh, tl = self.SHADOW, self.TAIL
        r = QRectF(3, 11, self.width() - 6 - sh, self.height() - 14 - sh - tl)
        path = QPainterPath()
        path.addRoundedRect(r, 18, 18)
        tail = QPainterPath()
        x = self.tail_x
        tail.moveTo(x - 15, r.bottom() - 4)
        tail.lineTo(x, r.bottom() + tl)
        tail.lineTo(x + 15, r.bottom() - 4)
        tail.closeSubpath()
        path = path.united(tail)
        p.fillPath(path.translated(sh, sh), QColor(C["ink"]))       # the hard shadow of the FurrOS cards
        p.setPen(QPen(QColor(C["ink"]), 3))
        p.setBrush(QColor(C["cream"]))
        p.drawPath(path)
        p.setPen(Qt.NoPen)                                          # a strip of the speaker's colour on the left
        p.setBrush(QColor(self.color))
        p.drawRoundedRect(QRectF(r.left() + 6, r.top() + 22, 5, max(r.height() - 34, 8)), 2, 2)


class PawBar(QWidget):
    """Progress: a glowing pink-to-cyan track, paw prints stamped along the filled part, a paw that runs at the head.
    busy(): a shimmer for steps without a percentage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self.value = 0.0
        self.shown = 0.0
        self.t = 0.0
        self.busy_mode = False
        self.paw = pix("paw.png")
        QTimer(self, interval=16, timeout=self._tick).start()

    def set_value(self, v):
        self.value = max(0.0, min(1.0, v))
        self.busy_mode = False

    def busy(self):
        self.busy_mode = True

    def _tick(self):
        self.t += 0.016
        self.shown += (self.value - self.shown) * 0.12
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        track = QRectF(10, 22, self.width() - 20, 22)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawRoundedRect(track, 11, 11)
        if self.busy_mode:
            p.save()
            p.setClipRect(track)
            w = track.width() * 0.3
            x = track.left() + ((self.t * 0.6) % 1.3 - 0.3) * track.width()
            g = QLinearGradient(x, 0, x + w, 0)
            g.setColorAt(0, QColor(255, 140, 190, 0))
            g.setColorAt(0.5, QColor(C["cyan"]))
            g.setColorAt(1, QColor(127, 240, 240, 0))
            p.setBrush(g)
            p.drawRoundedRect(QRectF(x, track.top(), w, track.height()), 11, 11)
            p.restore()
            return
        fw = track.width() * self.shown
        if fw > 1:
            fill = QRectF(track.left(), track.top(), max(fw, 22), track.height())
            g = QLinearGradient(track.left(), 0, track.right(), 0)
            g.setColorAt(0, QColor(C["pink"]))
            g.setColorAt(1, QColor(C["cyan"]))
            p.setBrush(g)
            p.drawRoundedRect(fill, 11, 11)
            # moving shine
            p.save()
            p.setClipRect(fill)
            sx = fill.left() + (self.t * 160) % (fill.width() + 120) - 60
            sg = QLinearGradient(sx, 0, sx + 60, 0)
            sg.setColorAt(0, QColor(255, 255, 255, 0))
            sg.setColorAt(0.5, QColor(255, 255, 255, 110))
            sg.setColorAt(1, QColor(255, 255, 255, 0))
            p.setBrush(sg)
            p.drawRect(QRectF(sx, fill.top(), 60, fill.height()))
            p.restore()
            # paw prints stamped along the way
            p.setOpacity(0.55)
            step = 46
            for i, x in enumerate(range(int(track.left()) + 14, int(track.left() + fw) - 30, step)):
                y = track.top() + (3 if i % 2 else 9)
                p.drawPixmap(QRectF(x, y, 12, 12), self.paw, QRectF(self.paw.rect()))
            p.setOpacity(1.0)
        # the runner at the head of the bar
        hx = track.left() + fw
        hop = abs(math.sin(self.t * 9)) * 10 if 0 < self.value < 1 else 0
        p.drawPixmap(QRectF(hx - 18, track.top() - 22 - hop, 36, 36), self.paw, QRectF(self.paw.rect()))


class DiscMerge(QWidget):
    """The FurrOS disc, cut in half: the halves of one finished disc (logo in the middle) slide together while the
    parts are joined, sparks fly along the seam, and once whole the disc glows and a light sweeps over it."""

    R = 72

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 200)
        self.v = 0.0
        self.t = 0.0
        self.sparks = []
        self.disc = self._render()
        QTimer(self, interval=16, timeout=self._tick).start()

    def _render(self):
        r = self.R
        size = 2 * r + 4
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        c = QPointF(size / 2, size / 2)
        # the shiny data side: a rainbow sheen like a real disc, in FurrOS colours
        sheen = QConicalGradient(c, 35)
        for at, col in ((0.0, "#DDE6F0"), (0.12, C["cyan"]), (0.25, "#F4F7FB"), (0.38, C["pink"]),
                        (0.5, "#DDE6F0"), (0.62, C["cyan"]), (0.75, "#F4F7FB"), (0.88, C["pink"]), (1.0, "#DDE6F0")):
            sheen.setColorAt(at, QColor(col))
        p.setPen(QPen(QColor("#FFF6F8"), 2.5))
        p.setBrush(sheen)
        p.drawEllipse(c, r, r)
        # faint grooves
        p.setBrush(Qt.NoBrush)
        for k in range(6):
            p.setPen(QPen(QColor(255, 255, 255, 45), 1))
            p.drawEllipse(c, r * (0.55 + k * 0.07), r * (0.55 + k * 0.07))
        # the label with the paw logo
        p.setPen(QPen(QColor(C["pink"]), 3))
        p.setBrush(QColor(C["maroon"]))
        p.drawEllipse(c, r * 0.48, r * 0.48)
        paw = pix("paw.png")
        s = r * 0.62
        p.drawPixmap(QRectF(c.x() - s / 2, c.y() - s / 2 - 2, s, s), paw, QRectF(paw.rect()))
        p.end()
        return pm

    def set_value(self, v):
        if v > self.v and v < 1:
            for _ in range(3):
                self.sparks.append(dict(x=0.0, y=random.uniform(-self.R, self.R), vx=random.uniform(-2.5, 2.5),
                                        vy=random.uniform(-2, 2), life=1.0, c=random.choice([C["cyan"], C["pink"], "#FFFFFF"])))
        self.v = v

    def _tick(self):
        self.t += 0.016
        for s in self.sparks:
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["life"] -= 0.04
        self.sparks = [s for s in self.sparks if s["life"] > 0]
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        cx, cy = self.width() / 2, self.height() / 2
        d = self.disc
        half = d.width() / 2
        gap = (1 - min(self.v, 1)) * 58
        wob = math.sin(self.t * 5) * 2.5 * (1 - self.v)
        whole = self.v >= 0.999
        if whole:
            glow_a = 0.5 + 0.5 * math.sin(self.t * 5)
            for k in range(3):
                p.setPen(QPen(QColor(127, 240, 240, int(70 * glow_a / (k + 1))), 8 - k * 2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(cx, cy), self.R + 6 + k * 5, self.R + 6 + k * 5)
        # left half, right half — two halves of the very same disc
        p.drawPixmap(QRectF(cx - half - gap, cy - half + wob, half, d.height()), d, QRectF(0, 0, half, d.height()))
        p.drawPixmap(QRectF(cx + gap, cy - half - wob, half, d.height()), d, QRectF(half, 0, half, d.height()))
        if whole:
            # a light sweeping over the finished disc
            clip = QPainterPath()
            clip.addEllipse(QPointF(cx, cy), self.R, self.R)
            p.setClipPath(clip)
            sx = cx - self.R * 1.6 + ((self.t * 0.8) % 1.6) * self.R * 2
            g = QLinearGradient(sx - 30, cy - self.R, sx + 30, cy + self.R)
            g.setColorAt(0, QColor(255, 255, 255, 0))
            g.setColorAt(0.5, QColor(255, 255, 255, 140))
            g.setColorAt(1, QColor(255, 255, 255, 0))
            p.fillRect(QRectF(sx - 40, cy - self.R, 80, 2 * self.R), g)
            p.setClipping(False)
        for s in self.sparks:
            p.setOpacity(max(s["life"], 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(s["c"]))
            p.drawEllipse(QPointF(cx + s["x"], cy + s["y"]), 2.6, 2.6)
        p.setOpacity(1)


class Confetti(QWidget):
    """A burst of paws and hearts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.paw = pix("paw.png")
        self.items = []
        self.timer = QTimer(self, interval=16, timeout=self._tick)

    def burst(self, n=90):
        w = self.width()
        cols = [C["pink"], C["cyan"], C["red"], C["warn"], C["ok"], "#FFFFFF"]
        for _ in range(n):
            self.items.append(dict(x=w / 2 + random.uniform(-60, 60), y=self.height() * 0.45,
                                   vx=random.uniform(-9, 9), vy=random.uniform(-15, -5), r=random.uniform(0, 360),
                                   vr=random.uniform(-9, 9), s=random.uniform(10, 22), c=random.choice(cols),
                                   kind=random.choice(["paw", "heart", "dot", "dot"]), life=1.0))
        self.timer.start()

    def _tick(self):
        for it in self.items:
            it["x"] += it["vx"]
            it["y"] += it["vy"]
            it["vy"] += 0.35
            it["vx"] *= 0.99
            it["r"] += it["vr"]
            it["life"] -= 0.007
        self.items = [it for it in self.items if it["life"] > 0 and it["y"] < self.height() + 40]
        if not self.items:
            self.timer.stop()
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for it in self.items:
            p.save()
            p.setOpacity(max(it["life"], 0))
            p.translate(it["x"], it["y"])
            p.rotate(it["r"])
            s = it["s"]
            if it["kind"] == "paw":
                p.drawPixmap(QRectF(-s / 2, -s / 2, s, s), self.paw, QRectF(self.paw.rect()))
            elif it["kind"] == "heart":
                path = QPainterPath()
                path.moveTo(0, s * 0.3)
                path.cubicTo(-s * 0.6, -s * 0.2, -s * 0.2, -s * 0.6, 0, -s * 0.2)
                path.cubicTo(s * 0.2, -s * 0.6, s * 0.6, -s * 0.2, 0, s * 0.3)
                p.fillPath(path, QColor(it["c"]))
            else:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(it["c"]))
                p.drawRoundedRect(QRectF(-s / 2, -s / 4, s, s / 2), 3, 3)
            p.restore()


def glow(widget, color=C["pink"], pulse=True):
    eff = QGraphicsDropShadowEffect(widget, blurRadius=30, color=QColor(color), offset=QPointF(0, 0))
    widget.setGraphicsEffect(eff)
    if pulse:
        a = QVariantAnimation(widget, startValue=18.0, endValue=48.0, duration=1100, loopCount=-1,
                              easingCurve=QEasingCurve.InOutSine)
        a.valueChanged.connect(lambda v: eff.setBlurRadius(v))
        a.setKeyValueAt(0.5, 48.0)
        a.setEndValue(18.0)
        a.start()
        widget._glow_anim = a


def hard_shadow(widget, d=5):
    """The FurrOS card shadow: solid ink, no blur, down-right."""
    widget.setGraphicsEffect(QGraphicsDropShadowEffect(widget, blurRadius=0, color=QColor(C["ink"]),
                                                       offset=QPointF(d, d)))
    return widget


def label(text="", name=None, wrap=True):
    l = QLabel(text)
    if name:
        l.setObjectName(name)
    l.setWordWrap(wrap)
    return l


# ------------------------------------------------------------------ workers

class FindWorker(QThread):
    found = Signal(object)
    failed = Signal(str, str, bool)

    def __init__(self, repo, tag, token):
        super().__init__()
        self.args = (repo, tag, token)

    def run(self):
        try:
            self.found.emit(core.find_build(*self.args))
        except core.DLError as e:
            self.failed.emit(e.ru, e.en, e.need_token)


class JobWorker(QThread):
    progress = Signal(str, float, float, float)
    note = Signal(str, str)
    done = Signal(str)
    failed = Signal(str, str)

    def __init__(self, job_factory):
        super().__init__()
        self.factory = job_factory
        self.job = None

    def run(self):
        try:
            self.job = self.factory(lambda s, d, t, v: self.progress.emit(s, d, t, v), self.note.emit)
            self.done.emit(self.job.run())
        except core.DLError as e:
            self.failed.emit(e.ru, e.en)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"Неожиданная ошибка: {e!r}", f"Unexpected error: {e!r}")

    def stop(self):
        if self.job:
            self.job.stop()


class DemoBuild:
    title, tag, iso_name, size = "FurrOS 1.0", "demo", "FurrOS-1.0-x86_64.iso", 2718859264
    pieces = ["FurrOS-1.0-x86_64.iso.part1", "FurrOS-1.0-x86_64.iso.part2"]


class DemoJob:
    """The same stages as core.Job with made-up numbers: for screenshots and checking the animations."""

    def __init__(self, build, folder, progress, note):
        self.b, self.progress, self.note, self._stop = build, progress, note, False
        self.folder = folder

    def stop(self):
        self._stop = True

    def run(self):
        size = self.b.size
        for i in range(0, 101):
            if self._stop:
                raise core.DLError("Остановлено", "Stopped")
            self.progress("download", size * i / 100, size, 9.5e6)
            time.sleep(0.07)
        self.note("Склеиваю части в один ISO…", "Joining the parts into one ISO…")
        for i in range(0, 101, 2):
            self.progress("join", size * i / 100, size, 0)
            time.sleep(0.06)
        self.note("Проверяю готовый ISO…", "Checking the finished ISO…")
        for i in range(0, 101, 4):
            self.progress("check", size * i / 100, size, 0)
            time.sleep(0.05)
        return os.path.join(self.folder, self.b.iso_name)


# ------------------------------------------------------------------ pages

class Page(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win

    def enter(self):
        pass


class IntroPage(Page):
    """The opening scene: the three of them pop in one after another and introduce themselves."""

    BEATS = [
        ("lapa", "lapa-wave.png", "Лапа", "Lapa", "Привет! Я Лапа 🐾 Сейчас мы вместе скачаем FurrOS — это быстрее, чем кажется!",
         "Hi! I'm Lapa 🐾 We're going to download FurrOS together — it's quicker than it looks!"),
        ("pixie", None, "Велвет", "Velvet", "А я Велвет. Пока всё качается, буду рассказывать интересное. Ну, или просто посижу рядом.",
         "And I'm Velvet. While it downloads I'll tell you cool stuff. Or just hang out here."),
        ("danyok", None, "Данёк", "Danyok", "А я склею кусочки образа в один. С лимоном получается быстрее, проверено 🍋",
         "And I'll glue the image pieces into one. It's faster with a lemon, tested 🍋"),
        ("lapa", "lapa-heart.png", "Лапа", "Lapa", "Ну что, поехали? Жми, когда будешь готов!",
         "So, shall we? Click when you're ready!"),
    ]

    def __init__(self, win):
        super().__init__(win)
        self.lapa = Actor("lapa-wave.png", 330, self)
        self.pixie = Actor("pixie.png", 150, self, head=0.23)
        self.danyok = Actor("danyok.png", 250, self, flip=True, head=0.62)
        for a in (self.lapa, self.pixie, self.danyok):
            a.hide()
        self.bubble = Bubble(self, None, 400)
        self.bubble.hide()
        self.skip = QPushButton(T("Пропустить ›", "Skip ›"), self)
        self.skip.setObjectName("skip")
        self.skip.clicked.connect(self.finish)
        self.hint = label(T("нажми, чтобы продолжить", "click to continue"), "dim", wrap=False)
        self.hint.setParent(self)
        self.hint.setStyleSheet(f"color: {C['dim']}; font-size: 13px;")
        self.beat = -1
        self.pending = False
        self.last = 0.0
        # "click to continue" shows only when a click will really go on
        self.hint_timer = QTimer(self, interval=100, timeout=lambda: self.hint.setVisible(
            not self.pending and not self.bubble.typing()))
        self.hint_timer.start()

    def resizeEvent(self, _):
        self.skip.adjustSize()
        self.skip.move(self.width() - self.skip.width() - 24, 20)
        self.hint.adjustSize()
        self.hint.move((self.width() - self.hint.width()) // 2, self.height() - 34)

    def enter(self):
        self.beat = -1
        self.next()

    def mousePressEvent(self, _):
        self.next()

    def mouseDoubleClickEvent(self, _):
        pass  # Qt would deliver a fast double click as a second press: one click = one step

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.next()
        elif e.key() == Qt.Key_Escape:
            self.finish()

    def next(self):
        now = time.monotonic()
        if self.pending or now - self.last < 0.35:
            return
        self.last = now
        if self.bubble.typing():
            return
        self.beat += 1
        if self.beat >= len(self.BEATS):
            return self.finish()
        who, image, ru_name, en_name, ru, en = self.BEATS[self.beat]
        w, h = self.width(), self.height()
        actor = getattr(self, who)
        if who == "lapa":
            if image:
                actor.set_image(image)
            end = QPoint(70, h - actor.height() - 34)
            if actor.isHidden():
                actor.slide_in(QPoint(-actor.width(), end.y()), end)
            else:
                actor.place(end)  # a new pose can be taller: stand on the same floor
                actor.hop()
        elif who == "pixie":
            actor.slide_in(QPoint(w + 40, h - actor.height() - 34), QPoint(w - actor.width() - 50, h - actor.height() - 34))
        else:
            x = (70 + self.lapa.width() + w - self.pixie.width() - 50) // 2 - actor.width() // 2
            actor.slide_in(QPoint(x, h + 20), QPoint(x, h - actor.height() - 34))
        # hide the old line right away: otherwise it flashes at the old speaker before the new one starts typing
        self.bubble.hide()
        self.bubble.lbl.setText("")
        self.pending = True
        QTimer.singleShot(250, lambda: (self.bubble.say(actor, T(ru_name, en_name), T(ru, en), who),
                                        setattr(self, "pending", False)))

    def finish(self):
        for a in (self.lapa, self.pixie, self.danyok):
            a.hide()
        self.bubble.hide()
        self.win.show_page("setup")


class SetupPage(Page):
    def __init__(self, win):
        super().__init__(win)
        self.lapa = Actor("lapa-hoodie.png", 300, self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(56, 46, 56, 40)
        title = label("FurrOS 1.0", "title")
        outer.addWidget(title)
        outer.addWidget(label(T("Пушистый дистрибутив Linux на основе Arch", "A fluffy Arch-based Linux distro"), "dim"))
        outer.addSpacing(22)
        self.card = QWidget()
        self.card.setObjectName("card")
        self.card.setMaximumWidth(560)
        self.card.setAttribute(Qt.WA_StyledBackground)
        hard_shadow(self.card)
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(24, 20, 24, 22)
        cl.setSpacing(10)
        self.build = label(T("Ищу свежую сборку…", "Looking for the latest build…"), "stage")
        cl.addWidget(self.build)
        self.size = label("", "dim")
        cl.addWidget(self.size)
        cl.addSpacing(6)
        cl.addWidget(label(T("Куда сохранить ISO", "Where to save the ISO"), "dim"))
        row = QHBoxLayout()
        self.folder = QLineEdit(str(Path.home() / ("Downloads" if (Path.home() / "Downloads").exists() else "")))
        pick = QPushButton(T("Выбрать…", "Browse…"))
        pick.clicked.connect(self.choose)
        row.addWidget(self.folder, 1)
        row.addWidget(pick)
        cl.addLayout(row)
        self.usb = QCheckBox(T("Потом записать на USB-флешку", "Then write it to a USB stick"))
        self.usb.setEnabled(LINUX)
        cl.addWidget(self.usb)
        if not LINUX:
            cl.addWidget(label(T("На Windows флешку удобно записать через Rufus (режим DD) или Ventoy — подскажу в конце.",
                                 "On Windows write the stick with Rufus (DD mode) or Ventoy — I'll remind you at the end."), "dim"))
        outer.addWidget(self.card)
        outer.addSpacing(26)
        self.go = QPushButton(T("Скачать FurrOS", "Download FurrOS"))
        self.go.setObjectName("go")
        self.go.setEnabled(False)
        self.go.setCursor(Qt.PointingHandCursor)
        self.go.clicked.connect(self.start)
        glow(self.go)
        outer.addWidget(self.go, 0, Qt.AlignLeft)
        outer.addStretch()
        self.bubble = Bubble(self, None, 300)
        self.bubble.hide()

    def lapa_spot(self):
        return QPoint(self.width() - self.lapa.width() - 50, self.height() - self.lapa.height() - 24)

    def resizeEvent(self, _):
        self.lapa.place(self.lapa_spot())
        if self.bubble.isVisible():
            self.bubble.aim(self.lapa)

    def enter(self):
        end = self.lapa_spot()
        self.lapa.slide_in(QPoint(self.width() + 10, end.y()), end)
        if self.win.build is None:
            self.win.find_build()
        else:
            self.show_build(self.win.build)

    def show_build(self, b):
        self.build.setText(f"{b.title}")
        self.size.setText(F("size", core.human(b.size, RU), len(b.pieces)))
        self.go.setEnabled(True)
        QTimer.singleShot(500, lambda: self.bubble.say(self.lapa, T("Лапа", "Lapa"),
                                                       T("Сборка нашлась! Выбери папку и жми кнопку.",
                                                         "Found the build! Pick a folder and press the button.")))

    def choose(self):
        d = QFileDialog.getExistingDirectory(self, T("Папка для ISO", "Folder for the ISO"), self.folder.text())
        if d:
            self.folder.setText(d)

    def start(self):
        self.win.folder = self.folder.text().strip() or "."
        self.win.want_usb = self.usb.isChecked()
        self.win.start_job()


class DownloadPage(Page):
    def __init__(self, win):
        super().__init__(win)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(56, 44, 56, 30)
        self.stage = label("", "stage")
        outer.addWidget(self.stage)
        self.pct = label("0%", "big")
        outer.addWidget(self.pct)
        self.bar = PawBar()
        outer.addWidget(self.bar)
        row = QHBoxLayout()
        self.info = label("", "dim")
        row.addWidget(self.info, 1)
        self.stop = QPushButton(T("Пауза", "Pause"))
        self.stop.clicked.connect(self.win.stop_job)
        hard_shadow(self.stop, 4)
        row.addWidget(self.stop, 0, Qt.AlignTop)
        outer.addLayout(row)
        self.note = label("", "dim")
        self.note.setStyleSheet(f"color: {C['warn']}; font-size: 14px;")
        outer.addWidget(self.note)
        outer.addStretch()
        self.lapa = Actor("lapa-timer.png", 210, self)
        self.pixie = Actor("pixie.png", 120, self, head=0.23)
        self.danyok = Actor("danyok.png", 200, self, flip=True, head=0.62)
        self.danyok.hide()
        self.disc = DiscMerge(self)
        self.disc.hide()
        self.tip = Bubble(self, None, 380)
        self.tip.hide()
        self.tips = list(TIPS)
        random.shuffle(self.tips)
        self.tip_timer = QTimer(self, interval=10000, timeout=self.next_tip)
        self.mode = None
        self.speeds = []

    def spots(self):
        """The cast in one row on the floor: Velvet on the left, the disc, Danyok, Lapa on the right."""
        h, w = self.height(), self.width()
        return dict(pixie=QPoint(30, h - self.pixie.height() - 24),
                    disc=QPoint(int(w * 0.30), h - self.disc.height() - 60),
                    danyok=QPoint(int(w * 0.56), h - self.danyok.height() - 24),
                    lapa=QPoint(w - self.lapa.width() - 40, h - self.lapa.height() - 24))

    def resizeEvent(self, _):
        sp = self.spots()
        for name in ("pixie", "danyok", "lapa"):
            getattr(self, name).place(sp[name])
        self.disc.move(sp["disc"])
        if self.tip.isVisible():
            self.tip.aim(self.danyok if self.mode == "join" else self.pixie)

    def enter(self):
        self.mode = None
        self.bar.set_value(0)
        self.pct.setText("0%")
        self.note.setText("")
        self.info.setText(T("Подключаюсь…", "Connecting…"))
        self.stage.setText(T("Скачиваю FurrOS", "Downloading FurrOS"))
        self.lapa.set_image("lapa-timer.png")
        self.danyok.hide()
        self.disc.hide()
        sp = self.spots()
        self.pixie.slide_in(QPoint(-200, sp["pixie"].y()), sp["pixie"])
        QTimer.singleShot(1200, self.next_tip)
        self.tip_timer.start()
        self.stop.setEnabled(True)

    def next_tip(self):
        if self.mode in ("join", "check"):
            return
        ru, en = self.tips.pop(0)
        self.tips.append((ru, en))
        self.tip.say(self.pixie, T("Велвет", "Velvet"), T(ru, en), "pixie")
        self.pixie.hop(18)

    def on_progress(self, stage, done, total, speed):
        frac = done / total if total else 0
        if stage != self.mode:
            self.mode = stage
            self.set_mode(stage)
        if stage == "download":
            self.speeds = (self.speeds + [speed])[-25:] if speed else self.speeds
            avg = sum(self.speeds) / len(self.speeds) if self.speeds else 0
            left = (total - done) / avg if avg else 0
            eta = F("eta", int(left // 60), int(left % 60)) if avg else ""
            self.info.setText(f"{core.human(done, RU)} / {core.human(total, RU)}"
                              + (f" · {core.human(avg, RU)}/{F('sec')}" if avg else "") + eta)
        else:
            self.info.setText(f"{core.human(done, RU)} / {core.human(total, RU)}")
        self.bar.set_value(frac)
        self.pct.setText(f"{int(frac * 100)}%")
        if stage == "join":
            self.disc.set_value(frac)

    def set_mode(self, stage):
        if stage == "download":
            self.stage.setText(T("Скачиваю FurrOS", "Downloading FurrOS"))
            self.lapa.set_image("lapa-timer.png")
        elif stage == "join":
            self.stage.setText(T("Данёк склеивает части в один ISO", "Danyok is gluing the parts into one ISO"))
            self.lapa.set_image("lapa-heart.png")
            self.tip.hide()
            sp = self.spots()
            self.lapa.place(sp["lapa"])  # the new pose has another height: keep her on the floor
            self.disc.show()
            self.danyok.slide_in(QPoint(sp["danyok"].x(), self.height() + 10), sp["danyok"])
            QTimer.singleShot(500, lambda: self.tip.say(self.danyok, T("Данёк", "Danyok"),
                                                        T("Кусочек к кусочку… Лимон, не подведи! 🍋",
                                                          "Piece by piece… Lemon, don't let me down! 🍋"), "danyok"))
        elif stage == "check":
            self.stage.setText(T("Проверяю, что всё скачалось без ошибок", "Checking that everything arrived intact"))
            self.lapa.set_image("lapa-sip.png")
            self.lapa.place(self.spots()["lapa"])
            self.tip.hide()
            self.disc.set_value(1.0)
        elif stage == "write":
            self.stage.setText(T("Записываю на флешку — не вынимай её", "Writing to the stick — don't unplug it"))
            self.lapa.set_image("lapa-timer.png")
            self.lapa.place(self.spots()["lapa"])
        self.lapa.hop()

    def on_note(self, ru, en):
        text = T(ru, en)
        if en.startswith("Connection"):
            self.note.setText("⚠ " + text)
        else:
            self.note.setText("")

    def leave(self):
        self.tip_timer.stop()
        self.tip.hide()


class DonePage(Page):
    def __init__(self, win):
        super().__init__(win)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(56, 44, 56, 30)
        self.title = label(T("Готово! 🎉", "Done! 🎉"), "title")
        outer.addWidget(self.title, 0, Qt.AlignHCenter)
        self.path = label("", "dim")
        self.path.setAlignment(Qt.AlignHCenter)
        outer.addWidget(self.path)
        self.next_steps = label("", "dim")
        self.next_steps.setAlignment(Qt.AlignHCenter)
        outer.addWidget(self.next_steps)
        outer.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        self.open = QPushButton(T("Открыть папку", "Open folder"))
        self.open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.win.folder)))
        self.usb = QPushButton(T("Записать на флешку", "Write to a USB stick"))
        self.usb.setObjectName("go")
        self.usb.clicked.connect(lambda: self.win.show_page("usb"))
        self.usb.setVisible(LINUX)
        close = QPushButton(T("Закрыть", "Close"))
        close.clicked.connect(self.win.close)
        for b in (self.open, self.usb, close):
            row.addWidget(b)
        row.addStretch()
        outer.addLayout(row)
        self.actors = [Actor("lapa-wave.png", 250, self), Actor("pixie.png", 120, self, head=0.23), Actor("danyok.png", 210, self)]
        for a in self.actors:
            a.hide()
        self.confetti = Confetti(self)

    def resizeEvent(self, _):
        self.confetti.setGeometry(self.rect())

    def enter(self, written=False):
        self.path.setText(self.win.iso or "")
        if written:
            self.title.setText(T("Флешка готова! 🎉", "The stick is ready! 🎉"))
            self.next_steps.setText(T("Вставь её в компьютер и выбери в меню загрузки (F8 / F11 / F12 / Esc).",
                                      "Plug it in and pick it in the boot menu (F8 / F11 / F12 / Esc)."))
            self.usb.hide()
        else:
            self.next_steps.setText(T("Дальше: запиши ISO на флешку — здесь, через Rufus (режим DD) или Ventoy — и загрузись с неё.",
                                      "Next: write the ISO to a USB stick — here, with Rufus (DD mode) or Ventoy — and boot from it."))
        w, h = self.width(), self.height()
        xs = [w // 2 - 330, w // 2 + 170, w // 2 - 70]
        for i, a in enumerate(self.actors):
            a.slide_in(QPoint(xs[i], h + 10), QPoint(xs[i], h - a.height() - 90), delay=200 + i * 220)
            QTimer.singleShot(1300 + i * 260, a.hop)
            QTimer.singleShot(2600 + i * 260, a.hop)
        QTimer.singleShot(400, self.confetti.burst)
        QTimer.singleShot(1400, lambda: self.confetti.burst(60))


class UsbPage(Page):
    """Linux: pick the stick. Only USB disks are listed, and the person has to tick that the stick will be erased."""

    def __init__(self, win):
        super().__init__(win)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(56, 44, 56, 30)
        outer.addWidget(label(T("Запись на флешку", "Write to a USB stick"), "title"))
        outer.addWidget(label(T("Здесь только USB-диски — внутренние диски компьютера сюда не попадают.",
                                "Only USB disks are shown here — the computer's internal disks never are."), "dim"))
        outer.addSpacing(12)
        self.list = QVBoxLayout()
        outer.addLayout(self.list)
        self.buttons = []
        refresh = QPushButton(T("Обновить список", "Refresh"))
        refresh.clicked.connect(self.fill)
        outer.addWidget(refresh, 0, Qt.AlignLeft)
        outer.addSpacing(12)
        self.sure = QCheckBox(T("Я понимаю, что ВСЁ на выбранной флешке будет удалено",
                                "I understand that EVERYTHING on the chosen stick will be erased"))
        self.sure.toggled.connect(self.sync)
        outer.addWidget(self.sure)
        outer.addStretch()
        row = QHBoxLayout()
        back = QPushButton(T("Назад", "Back"))
        back.clicked.connect(lambda: self.win.show_page("done"))
        self.go = QPushButton(T("Записать", "Write"))
        self.go.setObjectName("go")
        self.go.clicked.connect(self.write)
        row.addWidget(back)
        row.addStretch()
        row.addWidget(self.go)
        outer.addLayout(row)
        self.lapa = Actor("lapa-grr.png", 200, self)
        self.chosen = None

    def resizeEvent(self, _):
        self.lapa.move(self.width() - self.lapa.width() - 50, 110)

    def enter(self):
        self.sure.setChecked(False)
        self.fill()
        self.lapa.shake()

    def fill(self):
        for b in self.buttons:
            b.deleteLater()
        self.buttons, self.chosen = [], None
        disks = core.usb_disks()
        if not disks:
            b = label(T("Флешка не найдена — вставь её и нажми «Обновить список».",
                        "No stick found — plug it in and press Refresh."), "dim")
            self.list.addWidget(b)
            self.buttons.append(b)
        for d in disks:
            b = QPushButton(f"{(d.get('model') or 'USB').strip()} — {core.human(int(d['size']), RU)}  ({d['path']})")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, d=d, b=b: self.pick(d, b))
            self.list.addWidget(b)
            self.buttons.append(b)
        self.sync()

    def pick(self, d, btn):
        for b in self.buttons:
            if isinstance(b, QPushButton):
                b.setChecked(b is btn)
        self.chosen = d
        self.sync()

    def sync(self):
        self.go.setEnabled(bool(self.chosen) and self.sure.isChecked())

    def write(self):
        self.win.start_write(self.chosen)


class ErrorPage(Page):
    def __init__(self, win):
        super().__init__(win)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(56, 60, 56, 30)
        outer.addWidget(label(T("Грр, что-то пошло не так", "Grr, something went wrong"), "title"))
        self.msg = label("", "stage")
        outer.addWidget(self.msg)
        outer.addWidget(label(T("Скачанное не пропадёт: при следующем запуске загрузка продолжится с того же места.",
                                "Nothing downloaded is lost: next time it resumes from the same point."), "dim"))
        # private test builds: GitHub only lets collaborators in with a personal token (classic, "repo" scope)
        self.token_box = QWidget(self)
        tb = QVBoxLayout(self.token_box)
        tb.setContentsMargins(0, 18, 0, 0)
        tb.addWidget(label(T("Закрытая сборка для тестеров: вставь свой токен GitHub. Создать его: github.com → "
                             "Settings → Developer settings → Personal access tokens → Tokens (classic) → "
                             "Generate new token, отметь «repo», срок — 7 дней. Токен не сохраняется.",
                             "Private test build: paste your GitHub token. To make one: github.com → Settings → "
                             "Developer settings → Personal access tokens → Tokens (classic) → Generate new token, "
                             "tick “repo”, expiry 7 days. The token is not saved."), "dim"))
        self.token = QLineEdit(self.token_box)
        self.token.setEchoMode(QLineEdit.Password)
        self.token.setPlaceholderText("ghp_…")
        self.token.setMaximumWidth(520)
        tb.addWidget(self.token)
        outer.addWidget(self.token_box)
        self.token_box.setVisible(False)
        outer.addStretch()
        row = QHBoxLayout()
        again = QPushButton(T("Попробовать снова", "Try again"))
        again.setObjectName("go")
        again.clicked.connect(self.retry)
        close = QPushButton(T("Закрыть", "Close"))
        close.clicked.connect(self.win.close)
        row.addWidget(again)
        row.addWidget(close)
        row.addStretch()
        outer.addLayout(row)
        self.lapa = Actor("lapa-grr.png", 280, self)

    def resizeEvent(self, _):
        self.lapa.move(self.width() - self.lapa.width() - 60, self.height() - self.lapa.height() - 20)

    def retry(self):
        if self.token_box.isVisible() and self.token.text().strip():
            self.win.token = self.token.text().strip()
            self.win.build = None
        self.win.show_page("setup")

    def enter(self, ru="", en="", need_token=False):
        self.msg.setText(T(ru, en))
        self.token_box.setVisible(need_token)
        QTimer.singleShot(300, self.lapa.shake)


class LangPage(Page):
    """First screen: Lapa waves, four big language buttons. The system language is highlighted."""

    def __init__(self, win):
        super().__init__(win)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(56, 70, 56, 40)
        t = label("🐾 FurrOS", "title")
        outer.addWidget(t)
        outer.addWidget(label(I18N.TITLE, "dim"))
        outer.addSpacing(30)
        for code, name in I18N.LANGS:
            b = QPushButton(name)
            b.setObjectName("go" if code == LANG else "")
            b.setMinimumWidth(320)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("font-size: 20px; padding: 12px 30px; text-align: left;")
            if code != LANG:
                hard_shadow(b, 4)
            b.clicked.connect(lambda _=False, c=code: self.win.choose_lang(c))
            outer.addWidget(b, 0, Qt.AlignLeft)
            if code == LANG:
                glow(b)
        outer.addStretch()
        self.lapa = Actor("lapa-wave.png", 360, self)

    def resizeEvent(self, _):
        self.lapa.move(self.width() - self.lapa.width() - 70, self.height() - self.lapa.height() - 20)

    def enter(self):
        self.lapa.slide_in(QPoint(self.width() + 20, self.height() - self.lapa.height() - 20),
                           QPoint(self.width() - self.lapa.width() - 70, self.height() - self.lapa.height() - 20))
        QTimer.singleShot(900, self.lapa.hop)


# ------------------------------------------------------------------ window

class Window(QWidget):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.token = os.environ.get("GITHUB_TOKEN")
        self.build = None
        self.folder = "."
        self.iso = None
        self.want_usb = False
        self.worker = None
        self.setWindowTitle("FurrOS Downloader")
        self.setWindowIcon(QIcon(str(ASSETS / "paw.png")))
        self.resize(1000, 660)
        self.setMinimumSize(900, 600)
        self.backdrop = Backdrop(self)
        self.stack = QStackedLayout()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        holder = QWidget(self)
        holder.setLayout(self.stack)
        root.addWidget(holder)
        self.pages = {"lang": LangPage(self)}
        self.stack.addWidget(self.pages["lang"])
        self.backdrop.lower()
        self.current = None
        if args.lang:
            QTimer.singleShot(150, lambda: self.choose_lang(args.lang))
        else:
            QTimer.singleShot(150, lambda: self.show_page("lang"))

    def choose_lang(self, code):
        global LANG, RU
        LANG, RU = code, code == "ru"
        for name, cls in (("intro", IntroPage), ("setup", SetupPage), ("download", DownloadPage), ("done", DonePage),
                          ("usb", UsbPage), ("error", ErrorPage)):
            if name in self.pages:
                self.stack.removeWidget(self.pages[name])
                self.pages[name].deleteLater()
            self.pages[name] = cls(self)
            self.stack.addWidget(self.pages[name])
        self.show_page("setup" if self.args.no_intro else "intro")

    def resizeEvent(self, _):
        self.backdrop.setGeometry(self.rect())

    def show_page(self, name, *a):
        page = self.pages[name]
        if self.current and hasattr(self.current, "leave"):
            self.current.leave()
        self.stack.setCurrentWidget(page)
        self.current = page
        eff = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(eff)
        fade = QPropertyAnimation(eff, b"opacity", page, duration=380, startValue=0.0, endValue=1.0)
        fade.finished.connect(lambda: page.setGraphicsEffect(None))
        fade.start(QPropertyAnimation.DeleteWhenStopped)
        page.setFocus()
        page.enter(*a)

    def find_build(self):
        if self.args.demo:
            QTimer.singleShot(900, lambda: self._found(DemoBuild()))
            return
        self._finder = FindWorker(self.args.repo, self.args.tag, self.token)
        self._finder.found.connect(self._found)
        self._finder.failed.connect(lambda ru, en, need: self.show_page("error", ru, en, need))
        self._finder.start()

    def _found(self, b):
        self.build = b
        if self.current is self.pages["setup"]:
            self.pages["setup"].show_build(b)

    def start_job(self):
        if self.args.demo:
            factory = lambda pr, nt: DemoJob(self.build, self.folder, pr, nt)  # noqa: E731
        else:
            factory = lambda pr, nt: core.Job(self.build, self.folder, pr, nt)  # noqa: E731
        self.show_page("download")
        self.worker = JobWorker(factory)
        page = self.pages["download"]
        self.worker.progress.connect(page.on_progress)
        self.worker.note.connect(page.on_note)
        self.worker.done.connect(self._job_done)
        self.worker.failed.connect(lambda ru, en: self.show_page("error", ru, en))
        self.worker.start()

    def stop_job(self):
        if self.worker:
            self.worker.stop()

    def _job_done(self, iso):
        self.iso = iso
        self.show_page("usb" if self.want_usb and LINUX else "done")

    def start_write(self, disk):
        iso = self.iso

        def factory(pr, nt):
            class W:
                def stop(self):
                    pass

                def run(self):
                    core.write_usb(iso, disk, pr, root_cmd=("pkexec",))
                    return iso
            return W()
        self.show_page("download")
        page = self.pages["download"]
        page.stage.setText(T("Записываю на флешку — не вынимай её", "Writing to the stick — don't unplug it"))
        page.stop.setEnabled(False)
        self.worker = JobWorker(factory)
        self.worker.progress.connect(page.on_progress)
        self.worker.done.connect(lambda _: self.show_page("done", True))
        self.worker.failed.connect(lambda ru, en: self.show_page("error", ru, en))
        self.worker.start()

    def closeEvent(self, e):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        e.accept()


def main():
    global LANG, RU
    ap = argparse.ArgumentParser()
    try:
        import furros_dl_build  # written by the testers' build script: REPO = "owner/name"
        default_repo = furros_dl_build.REPO
    except ImportError:
        default_repo = core.REPO
    ap.add_argument("--repo", default=default_repo)
    ap.add_argument("--tag")
    ap.add_argument("--demo", action="store_true", help="the whole show without downloading anything")
    ap.add_argument("--no-intro", action="store_true")
    ap.add_argument("--lang", choices=[c for c, _ in I18N.LANGS])
    args = ap.parse_args()
    app = QApplication(sys.argv)
    from PySide6.QtCore import QLocale
    LANG = QLocale.system().name()[:2] if QLocale.system().name()[:2] in dict(I18N.LANGS) else "en"
    RU = LANG == "ru"
    QFontDatabase.addApplicationFont(str(ASSETS / "Nunito.ttf"))
    app.setFont(QFont("Nunito", 11))
    app.setStyleSheet(QSS)
    w = Window(args)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
