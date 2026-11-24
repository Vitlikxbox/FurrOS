#!/usr/bin/env python3
"""«Обои FurrOS»: pick a wallpaper from previews and it's set on whatever desktop is running.
Pictures from /usr/share/backgrounds/furros, live (video) wallpapers from .../animated; applying is done by
furros-set-wallpaper (same per-desktop logic as the first login). Language: UI_LANG from /etc/furros/settings.conf.
   furros-wallpapers-app [--dry-run]   (--dry-run: show the window, don't change anything)"""
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QProcess, QSize, Qt, QTimer
from PySide6.QtGui import (QColor, QFont, QFontDatabase, QIcon, QImage, QImageReader, QPainter, QPainterPath, QPen,
                           QPixmap, QPolygonF)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget)

ROOT = Path(os.environ.get("FURROS_ROOT", "/"))
BG = ROOT / "usr/share/backgrounds/furros"
THUMBS = ROOT / "usr/share/furros/thumbs"
CURRENT = BG / "current.png"
DRY = "--dry-run" in sys.argv
VIDEO_DESKTOPS = ("kde", "plasma", "hyprland", "sway", "niri", "cosmic")
X11_VIDEO_DESKTOPS = ("i3", "bspwm", "awesome", "qtile")   # via xwinwrap + mpv
KDE_VIDEO_PLUGIN = ROOT / "usr/share/plasma/wallpapers/luisbocanegra.smart.video.wallpaper.reborn"

C = {"bg": "#1E1218", "card": "#2A1A22", "ink": "#0E080B", "text": "#FFECEC", "dim": "#C8AAB4",
     "cyan": "#7FF0F0", "pink": "#FF8CBE", "red": "#E23A44"}


def settings():
    out = {}
    for p in (Path("/etc/furros/settings.conf"),
              Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "furros/wallpaper.conf"):
        try:
            for line in p.read_text().splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    out[k.strip()] = shlex.split(v)[0] if v.strip() else ""
        except (OSError, ValueError):
            pass
    return out


SET = settings()
LANG = SET.get("UI_LANG") or os.environ.get("LANG", "en")[:2]
LANG = LANG if LANG in ("ru", "en", "pl", "es") else "en"

TXT = {
    "title": {"ru": "Обои FurrOS", "en": "FurrOS Wallpapers", "pl": "Tapety FurrOS", "es": "Fondos de FurrOS"},
    "sub": {"ru": "Нажми на картинку, и она сразу встанет на рабочий стол",
            "en": "Click a picture and it goes straight onto your desktop",
            "pl": "Kliknij obrazek, a od razu trafi na pulpit",
            "es": "Haz clic en una imagen y irá directa al escritorio"},
    "still": {"ru": "Картинки", "en": "Pictures", "pl": "Obrazki", "es": "Imágenes"},
    "count": {"ru": "{0} шт.", "en": "{0} pcs", "pl": "{0} szt.", "es": "{0} uds."},
    "live": {"ru": "Живые", "en": "Live", "pl": "Ruchome", "es": "Animados"},
    "own": {"ru": "Свои обои…", "en": "Your own…", "pl": "Własna…", "es": "Propio…"},
    "pick": {"ru": "Выбери картинку", "en": "Choose a picture", "pl": "Wybierz obrazek", "es": "Elige una imagen"},
    "busy": {"ru": "Ставлю обои…", "en": "Setting the wallpaper…", "pl": "Ustawiam tapetę…", "es": "Poniendo el fondo…"},
    "done": {"ru": "Готово 🐾", "en": "Done 🐾", "pl": "Gotowe 🐾", "es": "Listo 🐾"},
    "fail": {"ru": "Не получилось: {0}", "en": "Didn't work: {0}", "pl": "Nie udało się: {0}", "es": "No funcionó: {0}"},
    "now": {"ru": "сейчас", "en": "now", "pl": "teraz", "es": "ahora"},
    "flash": {"ru": "⚡ мерцает", "en": "⚡ flashing", "pl": "⚡ miga", "es": "⚡ parpadea"},
    "novideo": {"ru": "В этой оболочке видео не крутится: живые обои встанут картинкой. Двигаются они в KDE, COSMIC, Hyprland, Sway, Niri, i3, bspwm, Awesome и Qtile.",
                "en": "This desktop can't play video: live wallpapers become a still picture. They move in KDE, COSMIC, Hyprland, Sway, Niri, i3, bspwm, Awesome and Qtile.",
                "pl": "Ten pulpit nie odtwarza wideo: ruchome tapety będą obrazkiem. Ruszają się w KDE, COSMIC, Hyprland, Sway, Niri, i3, bspwm, Awesome i Qtile.",
                "es": "Este escritorio no reproduce vídeo: los fondos animados serán una imagen. Se mueven en KDE, COSMIC, Hyprland, Sway, Niri, i3, bspwm, Awesome y Qtile."},
    "boot": {"ru": "Меню загрузки", "en": "Boot menu", "pl": "Menu startowe", "es": "Menú de arranque"},
    "bootnote": {"ru": "Цвета меню FurrBoot, которое встречает при включении. В самом меню тему меняет клавиша T.",
                 "en": "Colours of the FurrBoot menu you see when the PC starts. In the menu itself, T changes the theme.",
                 "pl": "Kolory menu FurrBoot, które wita cię po włączeniu. W samym menu motyw zmienia klawisz T.",
                 "es": "Colores del menú FurrBoot que ves al encender. En el propio menú, la tecla T cambia el tema."},
    "bootdone": {"ru": "Тема меню загрузки: {0}. Увидишь при следующем включении 🐾",
                 "en": "Boot menu theme: {0}. You'll see it on the next start 🐾",
                 "pl": "Motyw menu startowego: {0}. Zobaczysz go przy następnym uruchomieniu 🐾",
                 "es": "Tema del menú de arranque: {0}. Lo verás en el próximo arranque 🐾"},
    "flashwarn": {"ru": "⚡ — в ролике есть быстрое мерцание. Не ставь такие, если от вспышек плохо.",
                  "en": "⚡ — the clip has fast flashing. Skip these if flashes make you unwell.",
                  "pl": "⚡ — w klipie są szybkie błyski. Pomiń je, jeśli błyski ci szkodzą.",
                  "es": "⚡ — el clip tiene destellos rápidos. Evítalos si los destellos te sientan mal."},
}


def tr(key, *a):
    s = TXT[key].get(LANG) or TXT[key]["en"]
    return s.format(*a) if a else s


# picture names (file -> ru, en); anything not listed shows its file name
NAMES = {
    "furros-default.png": ("FurrOS", "FurrOS"), "furros-mascot.png": ("Пикси", "Pixie"),
    "furros-mascot-stripes.png": ("Пикси: полоски", "Pixie: stripes"), "furros-pixie-lying.png": ("Пикси: лежит", "Pixie: lying down"),
    "furros-lapa-wave.png": ("Лапа: привет", "Lapa: hi"), "furros-lapa-timer.png": ("Лапа: таймер", "Lapa: timer"),
    "furros-lapa-grr.png": ("Лапа: грр", "Lapa: grr"), "furros-lapa-hoodie.png": ("Лапа: худи", "Lapa: hoodie"),
    "furros-lapa-sip.png": ("Лапа: прочитано", "Lapa: seen"), "furros-lapa-heart.png": ("Лапа: ♥", "Lapa: ♥"),
    "furros-taroyadda-pointing.png": ("Тарояда: эй, ты!", "Taroyadda: hey, you!"),
    "furros-taroyadda-cozy.png": ("Тарояда: уютно", "Taroyadda: cozy"),
    "furros-taroyadda-standing.png": ("Тарояда: хмм", "Taroyadda: hmm"),
    "furros-taroyadda-sassy.png": ("Тарояда: дерзко", "Taroyadda: sassy"),
    "furros-bubblegum.png": ("Bubblegum", "Bubblegum"), "furros-danyok.png": ("Данёк", "Danyok"),
    "furros-danyok-lemon.png": ("Данёк: лимон", "Danyok: lemon"),
}
# packs of still pictures: (id, title, who/what, accent, cover avatar, file-name keys)
PACKS = [
    ("pixie", {"ru": "Обои с Пикси", "en": "Pixie pack", "pl": "Tapety z Pixie", "es": "Fondos con Pixie"},
     {"ru": "талисман FurrOS", "en": "the FurrOS mascot", "pl": "maskotka FurrOS", "es": "la mascota de FurrOS"},
     "#FF8CBE", "furros-mascot.png", ("mascot", "pixie")),
    ("taroyadda", {"ru": "Обои с Тароядой", "en": "Taroyadda pack", "pl": "Tapety z Taroyaddą", "es": "Fondos con Taroyadda"},
     {"ru": "арт taroyadda", "en": "art by taroyadda", "pl": "rysunki taroyadda", "es": "arte de taroyadda"},
     "#B69CFF", "furros-taroyadda.png", ("taroyadda",)),
    ("lapa", {"ru": "Обои с Лапой", "en": "Lapa pack", "pl": "Tapety z Łapą", "es": "Fondos con Lapa"},
     {"ru": "учительница из Школы Лапы", "en": "the teacher of Lapa's School", "pl": "nauczycielka ze Szkoły Łapy",
      "es": "la profe de la Escuela de Lapa"}, "#7FF0F0", "furros-lapa.png", ("lapa",)),
    ("danyok", {"ru": "Обои с Даньком", "en": "Danyok pack", "pl": "Tapety z Danyokiem", "es": "Fondos con Danyok"},
     {"ru": "FurrOS × Chromeble2S", "en": "FurrOS × Chromeble2S", "pl": "FurrOS × Chromeble2S", "es": "FurrOS × Chromeble2S"},
     "#FFD36B", "furros-danyok.png", ("danyok",)),
    ("furros", {"ru": "FurrOS", "en": "FurrOS", "pl": "FurrOS", "es": "FurrOS"},
     {"ru": "фирменные", "en": "the classics", "pl": "klasyka", "es": "los clásicos"}, "#E23A44", "", ()),
]
AVATARS = ROOT / "usr/share/furros/avatars"


def pack_of(path):
    for pid, *_rest, keys in PACKS:
        if any(k in path.stem for k in keys):
            return pid
    return "furros"


FLASHING = {"anim-bothered", "anim-two", "anim-pretty-cvnt", "anim-paper-planes", "anim-p3t", "anim-ch4insaww"}


def name_of(path):
    n = NAMES.get(path.name)
    if n:
        return n[0] if LANG == "ru" else n[1]
    return path.stem.replace("anim-", "").replace("furros-", "").replace("-", " ").title()


def current_desktop():
    """XDG_CURRENT_DESKTOP is unset in some sessions (Qtile, i3, Awesome: no DesktopNames= in their session files,
    tester report 20.11): furros-desktop also checks the session name and the running window manager."""
    try:
        r = subprocess.run(["furros-desktop"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().lower()
    except (OSError, subprocess.SubprocessError):
        pass
    return os.environ.get("XDG_CURRENT_DESKTOP", "").lower()


def can_play_video():
    desk = current_desktop()
    # a missing player (the KDE plugin, mpvpaper, xwinwrap) is installed by furros-set-wallpaper when a live
    # wallpaper is picked, so only the desktop decides (tester report 22.11: KDE without the plugin)
    return any(k in desk for k in VIDEO_DESKTOPS + X11_VIDEO_DESKTOPS)


def thumb(path, size=QSize(320, 180), radius=12):
    """A cover-cropped preview, decoded at reduced size (the pictures are full HD)."""
    r = QImageReader(str(path))
    src = r.size()
    if src.isValid():
        k = max(size.width() / src.width(), size.height() / src.height())
        r.setScaledSize(QSize(max(1, int(src.width() * k)), max(1, int(src.height() * k))))
    img = r.read()
    if img.isNull():
        img = QImage(size, QImage.Format_ARGB32)
        img.fill(Qt.black)
    x = max(0, (img.width() - size.width()) // 2)
    y = max(0, (img.height() - size.height()) // 2)
    return rounded(QPixmap.fromImage(img.copy(x, y, size.width(), size.height())), radius)


def rounded(pm, r):
    out = QPixmap(pm.size())
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, pm.width(), pm.height(), r, r)
    p.setClipPath(path)
    p.drawPixmap(0, 0, pm)
    p.end()
    return out


def avatar(file, accent, d=58):
    """A round pack cover with a coloured ring (the FurrOS logo when there is no avatar)."""
    src = QPixmap(str(AVATARS / file)) if file else QPixmap()
    if src.isNull():
        src = QPixmap(str(ROOT / "usr/share/furros/furros-logo.png"))
    out = QPixmap(d, d)
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(accent))
    p.drawEllipse(0, 0, d, d)
    p.setBrush(QColor(C["card"]))
    p.drawEllipse(3, 3, d - 6, d - 6)
    if not src.isNull():
        path = QPainterPath()
        path.addEllipse(5, 5, d - 10, d - 10)
        p.setClipPath(path)
        sc = src.scaled(d - 10, d - 10, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        p.drawPixmap(5 + (d - 10 - sc.width()) // 2, 5 + (d - 10 - sc.height()) // 2, sc)
    p.end()
    return out


class Card(QFrame):
    def __init__(self, win, picture, video, title, badge=""):
        super().__init__()
        self.win, self.picture, self.video = win, picture, video
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 10)
        v.setSpacing(6)
        self.bare = not title and not badge
        if self.bare:
            # the picture fills the card right up to its 3 px outline (Qt already insets the layout by the QSS border)
            v.setContentsMargins(0, 0, 0, 0)
            self.setFixedSize(320 + 6, 180 + 6)
        else:
            self.setFixedWidth(320 + 16 + 6)
        self.img = QLabel()
        self.img.setFixedSize(320, 180)
        v.addWidget(self.img)
        # «now» is a sticker on the picture itself, so cards without a title still show it
        self.now = QLabel("✓ " + tr("now"), self.img)
        self.now.setObjectName("now")
        self.now.adjustSize()
        self.now.move(320 - self.now.width() - 12, 12)
        self.now.hide()
        if title or badge:
            row = QHBoxLayout()
            self.name = QLabel(title)
            self.name.setObjectName("name")
            row.addWidget(self.name, 1)
            if badge:
                b = QLabel(badge)
                b.setObjectName("badge")
                row.addWidget(b)
            v.addLayout(row)
        self.thumb_src = THUMBS / f"{Path(video).stem}.png" if video and (THUMBS / f"{Path(video).stem}.png").exists() else picture

    def load(self):
        self.img.setPixmap(thumb(self.thumb_src, radius=13 if self.bare else 10))

    def set_current(self, on):
        self.setProperty("current", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.now.setVisible(on)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.win.apply(self.picture, self.video)


# FurrBoot's colour themes (bootloader/furrboot/src/theme.rs): night, page, wine page, selection, edge, paper
BOOT_THEMES = [
    ("comic", {"ru": "Комикс", "en": "Comic", "pl": "Komiks", "es": "Cómic"}, ("#150B11", "#1E1218", "#781C2C", "#7FF0F0", "#FF8CBE", "#FFECEC")),
    ("neon", {"ru": "Неон", "en": "Neon", "pl": "Neon", "es": "Neón"}, ("#07040D", "#140C22", "#5A0FC8", "#3DF5FF", "#FF3DCB", "#F2EBFF")),
    ("pastel", {"ru": "Пастель", "en": "Pastel", "pl": "Pastel", "es": "Pastel"}, ("#1C1418", "#271C21", "#8E3B4C", "#A8E6E2", "#F7B8D2", "#FFECEC")),
    ("night", {"ru": "Ночь", "en": "Night", "pl": "Noc", "es": "Noche"}, ("#0A0F1F", "#141B33", "#1E3A8A", "#7FD0FF", "#B69CFF", "#E9F0FF")),
    ("forest", {"ru": "Лес", "en": "Forest", "pl": "Las", "es": "Bosque"}, ("#0C130E", "#17221A", "#2F5D3A", "#9BE39B", "#F4B860", "#F1F5E8")),
    ("mono", {"ru": "Монохром", "en": "Mono", "pl": "Mono", "es": "Mono"}, ("#0B0B0B", "#181818", "#3A3A3A", "#FFFFFF", "#D9D9D9", "#F2F2F2")),
]
EFIVAR = Path("/sys/firmware/efi/efivars/FurrBootTheme-9868b1f9-c27c-4bbd-926e-76ef5b5ada1a")


def boot_menu_here():
    """FurrBoot only runs on UEFI PCs, and the theme is set with furrboot-theme (package furrboot)."""
    return DRY or (Path("/sys/firmware/efi/efivars").is_dir() and shutil.which("furrboot-theme") is not None)


def boot_theme_now():
    try:
        return EFIVAR.read_bytes()[4:].rstrip(b"\0").decode() or "comic"
    except OSError:
        return "comic"


BOOT_SHOTS = ROOT / "usr/share/furros/boot-themes"   # real screenshots of FurrBoot in each theme (640x400)


def boot_shot(name):
    """The real screenshot of the menu in this theme, rounded; None if it isn't installed."""
    pm = QPixmap(str(BOOT_SHOTS / f"{name}.jpg"))
    if pm.isNull():
        return None
    return rounded(pm.scaled(320, 200, Qt.IgnoreAspectRatio, Qt.SmoothTransformation), 10)


def boot_preview(cols):
    """A small drawing of the FurrBoot menu in these colours (fallback when there is no screenshot)."""
    night, page, wine, sel, edge, paper = (QColor(c) for c in cols)
    pm = QPixmap(320, 180)
    pm.fill(night)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(wine)
    p.drawPolygon(QPolygonF([QPointF(200, 0), QPointF(320, 0), QPointF(320, 180), QPointF(160, 180)]))
    p.setPen(QPen(edge, 3))
    p.drawLine(QPointF(203, 0), QPointF(163, 180))
    p.setPen(QPen(QColor("#0E080B"), 3))
    p.setBrush(page)
    p.drawPolygon(QPolygonF([QPointF(18, 52), QPointF(178, 52), QPointF(170, 150), QPointF(12, 150)]))
    p.setPen(Qt.NoPen)
    p.setBrush(paper)
    p.drawRoundedRect(28, 70, 70, 14, 4, 4)            # the big title
    p.drawRoundedRect(28, 118, 90, 18, 8, 8)           # the speech bubble
    p.drawEllipse(QPointF(140, 100), 22, 26)           # the character
    for i in range(4):                                 # menu rows, the first one selected
        y = 52 + i * 26
        p.setPen(QPen(QColor("#0E080B"), 2))
        p.setBrush(sel if i == 0 else page)
        p.drawPolygon(QPolygonF([QPointF(196, y), QPointF(306, y), QPointF(302, y + 20), QPointF(192, y + 20)]))
    p.setPen(Qt.NoPen)
    p.setBrush(paper)
    p.drawEllipse(QPointF(26, 20), 7, 7)               # the logo paw
    p.drawRoundedRect(38, 14, 44, 12, 3, 3)
    p.end()
    return pm


class BootCard(QFrame):
    def __init__(self, win, name, title, cols):
        super().__init__()
        self.win, self.theme, self.title = win, name, title
        self.setObjectName("card")
        self.setFixedWidth(320 + 16 + 6)
        self.setCursor(Qt.PointingHandCursor)
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 10)
        v.setSpacing(6)
        img = QLabel()
        shot = boot_shot(name)
        img.setFixedSize(320, 200 if shot else 180)
        img.setPixmap(shot or boot_preview(cols))
        v.addWidget(img)
        row = QHBoxLayout()
        n = QLabel(title)
        n.setObjectName("name")
        row.addWidget(n, 1)
        self.now = QLabel("✓ " + tr("now"))
        self.now.setObjectName("now")
        self.now.hide()
        row.addWidget(self.now)
        v.addLayout(row)

    def set_current(self, on):
        self.setProperty("current", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.now.setVisible(on)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.win.set_boot_theme(self.theme, self.title)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("title"))
        self.setWindowIcon(QIcon.fromTheme("preferences-desktop-wallpaper", QIcon.fromTheme("furros")))
        self.resize(1140, 780)
        self.cards = []
        self.proc = None
        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(28, 22, 28, 18)
        lay.setSpacing(12)
        head = QHBoxLayout()
        head.setSpacing(16)
        logo = QLabel()
        lp = QPixmap(str(ROOT / "usr/share/furros/furros-logo.png"))
        if not lp.isNull():
            logo.setPixmap(lp.scaledToHeight(64, Qt.SmoothTransformation))
            head.addWidget(logo, 0, Qt.AlignVCenter)
        t = QVBoxLayout()
        t.setSpacing(2)
        title = QLabel(tr("title"))
        title.setObjectName("title")
        t.addWidget(title)
        sub = QLabel(tr("sub"))
        sub.setObjectName("dim")
        t.addWidget(sub)
        head.addLayout(t, 1)
        own = QPushButton(tr("own"))
        own.setObjectName("own")
        own.clicked.connect(self.own)
        head.addWidget(own, 0, Qt.AlignVCenter)
        lay.addLayout(head)

        tabs = QHBoxLayout()
        self.group = QButtonGroup(self)
        self.stack = QStackedWidget()
        for i, key in enumerate(("still", "live") + (("boot",) if boot_menu_here() else ())):
            b = QPushButton(tr(key))
            b.setObjectName("tab")
            b.setCheckable(True)
            b.setChecked(i == 0)
            self.group.addButton(b, i)
            tabs.addWidget(b)
        tabs.addStretch()
        self.group.idClicked.connect(self.stack.setCurrentIndex)
        self.group.idClicked.connect(lambda i: own.setVisible(i != 2))  # «your own picture» means nothing for the boot menu
        lay.addLayout(tabs)

        stills = sorted(p for p in BG.glob("*.png") if p.name != "current.png" and not p.is_symlink())
        order = list(NAMES)
        stills.sort(key=lambda p: order.index(p.name) if p.name in order else len(order))
        self.stack.addWidget(self.packs(stills))
        videos = sorted((BG / "animated").glob("*.mp4"))
        live = []
        for v in videos:
            still = v.with_suffix(".png")
            live.append((still if still.exists() else CURRENT, str(v), name_of(v), tr("flash") if v.stem in FLASHING else ""))
        notes = [tr("flashwarn")] + ([] if can_play_video() else [tr("novideo")])
        self.stack.addWidget(self.grid(live, notes))
        self.boot_cards = []
        if boot_menu_here():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            inner = QWidget()
            bv = QVBoxLayout(inner)
            bv.setContentsMargins(0, 0, 0, 0)
            note = QLabel(tr("bootnote"))
            note.setObjectName("note")
            note.setWordWrap(True)
            bv.addWidget(note)
            g = QGridLayout()
            g.setSpacing(16)
            g.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            for i, (name, titles, cols) in enumerate(BOOT_THEMES):
                c = BootCard(self, name, titles.get(LANG, titles["en"]), cols)
                self.boot_cards.append(c)
                g.addWidget(c, i // 3, i % 3)
            bv.addLayout(g)
            bv.addStretch()
            scroll.setWidget(inner)
            self.stack.addWidget(scroll)
            self.mark_boot_theme()
        lay.addWidget(self.stack, 1)

        self.status = QLabel("")
        self.status.setObjectName("status")
        lay.addWidget(self.status)
        self.mark_current()
        # previews load after the window is up, a few per tick, so it opens at once
        self._todo = list(self.cards)
        self._timer = QTimer(self, interval=0)
        self._timer.timeout.connect(self._load_some)
        self._timer.start()

    def packs(self, stills):
        """The «Pictures» tab: a section per pack (Pixie, Taroyadda, Lapa…), pictures without names."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(0, 0, 8, 0)
        v.setSpacing(10)
        for pid, titles, subs, accent, cover, _keys in PACKS:
            pics = [p for p in stills if pack_of(p) == pid]
            if not pics:
                continue
            head = QFrame()
            head.setObjectName("packhead")
            head.setFixedWidth(3 * (320 + 6) + 2 * 16)  # as wide as a row of three pictures
            head.setStyleSheet(f"QFrame#packhead {{ border-left: 6px solid {accent}; }}")
            h = QHBoxLayout(head)
            h.setContentsMargins(14, 10, 14, 10)
            h.setSpacing(14)
            av = QLabel()
            av.setPixmap(avatar(cover, accent))
            h.addWidget(av)
            tv = QVBoxLayout()
            tv.setSpacing(0)
            name = QLabel(titles.get(LANG, titles["en"]))
            name.setObjectName("packname")
            tv.addWidget(name)
            sub = QLabel(subs.get(LANG, subs["en"]))
            sub.setObjectName("dim")
            tv.addWidget(sub)
            h.addLayout(tv, 1)
            cnt = QLabel(tr("count", len(pics)))
            cnt.setObjectName("count")
            cnt.setStyleSheet(f"background: {accent};")
            h.addWidget(cnt, 0, Qt.AlignVCenter)
            v.addSpacing(6)
            v.addWidget(head)
            g = QGridLayout()
            g.setSpacing(16)
            g.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            for i, p in enumerate(pics):
                c = Card(self, p, "", "", "")
                self.cards.append(c)
                g.addWidget(c, i // 3, i % 3)
            v.addLayout(g)
        v.addStretch()
        scroll.setWidget(inner)
        return scroll

    def grid(self, items, notes=()):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(0, 0, 0, 0)
        for n in notes:
            l = QLabel(n)
            l.setObjectName("note")
            l.setWordWrap(True)
            v.addWidget(l)
        g = QGridLayout()
        g.setSpacing(16)
        g.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        for i, (pic, video, title, badge) in enumerate(items):
            c = Card(self, pic, video, title, badge)
            self.cards.append(c)
            g.addWidget(c, i // 3, i % 3)
        v.addLayout(g)
        v.addStretch()
        scroll.setWidget(inner)
        return scroll

    def _load_some(self):
        for _ in range(3):
            if not self._todo:
                self._timer.stop()
                return
            self._todo.pop(0).load()

    def mark_current(self):
        s = settings()
        cur_pic = str(CURRENT.resolve()) if CURRENT.exists() else ""
        cur_vid = s.get("WALLPAPER_VIDEO", "")
        for c in self.cards:
            if cur_vid:
                on = bool(c.video) and os.path.realpath(c.video) == os.path.realpath(cur_vid)
            else:
                on = not c.video and str(c.picture.resolve()) == cur_pic
            c.set_current(on)

    def mark_boot_theme(self, name=None):
        name = name or boot_theme_now()
        for c in self.boot_cards:
            c.set_current(c.theme == name)

    def set_boot_theme(self, name, title):
        """The theme lives in an EFI variable: writing it needs root (pkexec asks for the password)."""
        if self.proc and self.proc.state() != QProcess.NotRunning:
            return
        if DRY:
            self.mark_boot_theme(name)
            self.status.setText(tr("bootdone", title))
            return
        self.proc = QProcess(self)
        self.proc.finished.connect(lambda code, _s: (self.mark_boot_theme(name if code == 0 else None),
                                                      self.status.setText(tr("bootdone", title) if code == 0 else tr(
                                                          "fail", bytes(self.proc.readAllStandardError()).decode(errors="replace").strip() or f"code {code}"))))
        self.proc.start("pkexec", ["furrboot-theme", name])

    def own(self):
        f, _ = QFileDialog.getOpenFileName(self, tr("pick"), str(Path.home()),
                                           "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if f:
            self.apply(Path(f), "")

    def apply(self, picture, video):
        if self.proc and self.proc.state() != QProcess.NotRunning:
            return
        self.status.setText(tr("busy"))
        if DRY:
            QTimer.singleShot(400, lambda: self.status.setText(tr("done") + f"  (dry run: {picture.name})"))
            return
        self.proc = QProcess(self)
        self.proc.finished.connect(self.finished)
        self.proc.start("furros-set-wallpaper", [str(picture)] + ([video] if video else []))

    def finished(self, code, _status):
        if code == 0:
            self.status.setText(tr("done"))
            self.mark_current()
        else:
            err = bytes(self.proc.readAllStandardError()).decode(errors="replace").strip() or f"code {code}"
            self.status.setText(tr("fail", err))


QSS = f"""
QWidget {{ background: {C['bg']}; color: {C['text']}; font-family: Nunito; font-size: 15px; }}
QLabel#title {{ font-family: "Dela Gothic One"; font-size: 30px; color: {C['text']}; }}
QFrame#packhead {{ background: {C['card']}; border-radius: 14px; }}
QFrame#packhead QLabel {{ background: transparent; }}
QLabel#packname {{ font-size: 20px; font-weight: 900; }}
QLabel#count {{ color: {C['ink']}; border-radius: 10px; padding: 3px 12px; font-weight: 900; font-size: 13px; }}
QLabel#dim, QLabel#note {{ color: {C['dim']}; }}
QLabel#note {{ background: {C['card']}; border-radius: 12px; padding: 10px 14px; }}
QLabel#status {{ color: {C['cyan']}; font-weight: 700; }}
QFrame#card {{ background: {C['card']}; border: 3px solid {C['ink']}; border-radius: 16px; }}
QFrame#card:hover {{ border-color: {C['cyan']}; background: #34202B; }}
QFrame#card[current="true"] {{ border-color: {C['pink']}; }}
QFrame#card QLabel {{ background: transparent; }}
QLabel#name {{ font-weight: 700; }}
QLabel#badge {{ color: #FFD36B; font-size: 13px; }}
QFrame#card QLabel#now, QLabel#now {{ color: {C['ink']}; background: {C['pink']}; border: 2px solid {C['ink']}; border-radius: 9px; padding: 2px 9px; font-size: 13px; font-weight: 900; }}
QPushButton {{ background: {C['card']}; border: 3px solid {C['ink']}; border-radius: 14px; padding: 8px 18px; font-weight: 800; }}
QPushButton:hover {{ border-color: {C['cyan']}; }}
QPushButton#tab:checked {{ background: {C['cyan']}; color: {C['ink']}; }}
QPushButton#own {{ background: {C['pink']}; color: {C['ink']}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: #4A2E3C; border-radius: 5px; min-height: 40px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("furros-wallpapers")
    app.setDesktopFileName("furros-wallpapers")
    for f in (ROOT / "usr/share/fonts/furros").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(f))
    app.setFont(QFont("Nunito", 11))
    app.setStyleSheet(QSS)
    w = Window()
    w.show()
    if "--screenshot" in sys.argv:  # dev helper: --screenshot OUT.png [--live]
        out = sys.argv[sys.argv.index("--screenshot") + 1]
        if "--live" in sys.argv:
            w.group.button(1).click()
        if "--boot" in sys.argv:  # the boot menu tab
            w.group.button(2).click()
        QTimer.singleShot(2500, lambda: (w.grab().save(out), app.quit()))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
