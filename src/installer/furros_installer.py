#!/usr/bin/env python3
"""FurrOS graphical installer ("Лапа-установщик")."""
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QProcess, QPropertyAnimation, Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QPlainTextEdit, QProgressBar,
    QPushButton, QRadioButton, QScrollArea, QSizePolicy, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "drivers"))
import catalog  # noqa: E402
from i18n import STRINGS  # noqa: E402
from terms import TERMS  # noqa: E402
import furros_hw  # noqa: E402

LINUX = platform.system() == "Linux"
ROOT = Path(os.environ.get("FURROS_ROOT", "/" if LINUX else r"D:\FurrOS\profile\airootfs"))
SHARE = ROOT / "usr/share/furros"
DRY = not LINUX or "--dry-run" in sys.argv or os.environ.get("FURROS_DRY") == "1"
LANG = os.environ.get("FURROS_LANG", "ru")
VIRT = ""
if LINUX:
    try:
        VIRT = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True).stdout.strip()
        VIRT = "" if VIRT == "none" else VIRT
    except OSError:
        pass


def tr(s):
    """Translate a Russian source string into the current UI language."""
    if LANG == "ru" or not s:
        return s
    return STRINGS.get(s, {}).get(LANG, s)


LOG_PATH = Path("/tmp/furros-install.log") if LINUX else Path(tempfile.gettempdir()) / "furros-install.log"

C = dict(bg="#1E1218", surface="#2A1A22", surface2="#3A2430", ink="#0E080B", text="#FFECEC",
         dim="#C8AAB4", primary="#7FF0F0", accent="#FF8CBE", danger="#E23A44", maroon="#781C2C",
         ok="#78E6A0", warn="#FFBE5A")

QSS = f"""
* {{ font-family: Nunito; color: {C['text']}; }}
QMainWindow, #root {{ background: {C['bg']}; }}
#sidebar {{ background: {C['ink']}; border-right: 3px solid {C['maroon']}; }}
QLabel#h1 {{ font-size: 30px; font-weight: 900; }}
QLabel#h2 {{ font-size: 19px; font-weight: 800; }}
QLabel#sub {{ font-size: 15px; color: {C['dim']}; }}
QLabel#dim {{ color: {C['dim']}; font-size: 13px; }}
QLabel#err {{ color: {C['danger']}; font-size: 13px; font-weight: 700; }}
QLabel#chip {{ background: {C['maroon']}; border-radius: 9px; padding: 2px 10px; font-size: 12px; font-weight: 800; }}
QLabel#chipCyan {{ background: {C['primary']}; color: {C['ink']}; border-radius: 9px; padding: 2px 10px;
                  font-size: 12px; font-weight: 800; }}
QLabel#bubble {{ background: {C['surface']}; border: 3px solid {C['ink']}; border-radius: 16px;
                padding: 12px 16px; font-size: 14px; }}
QFrame#card {{ background: {C['surface']}; border: 3px solid {C['ink']}; border-radius: 16px; }}
QFrame#card:hover {{ background: {C['surface2']}; }}
QFrame#card[selected="true"] {{ border: 3px solid {C['accent']}; background: {C['surface2']}; }}
QFrame#danger {{ background: #3A1418; border: 3px solid {C['danger']}; border-radius: 16px; }}
QPushButton {{ background: {C['surface2']}; border: 3px solid {C['ink']}; border-radius: 14px;
              padding: 10px 22px; font-size: 15px; font-weight: 800; min-height: 24px; }}
QPushButton:hover {{ background: #4A2E3C; }}
QPushButton:focus {{ border: 3px solid {C['accent']}; }}
QPushButton:disabled {{ color: #7A6068; background: {C['surface']}; }}
QPushButton#primary {{ background: {C['primary']}; color: {C['ink']}; }}
QPushButton#primary:hover {{ background: #A8F7F7; }}
QPushButton#primary:disabled {{ background: #3E5A5C; color: #1E2A2B; }}
QPushButton#danger {{ background: {C['danger']}; color: white; }}
QPushButton#danger:disabled {{ background: #5A2A2E; color: #A08088; }}
QPushButton#link {{ background: transparent; border: none; color: {C['accent']}; padding: 2px 6px;
                   font-size: 13px; text-decoration: underline; min-height: 0; }}
QPushButton#step {{ background: transparent; border: none; border-radius: 10px; text-align: left;
                   padding: 8px 12px; font-size: 14px; font-weight: 700; color: {C['dim']}; }}
QPushButton#step[state="current"] {{ background: {C['maroon']}; color: white; }}
QPushButton#step[state="done"] {{ color: {C['primary']}; }}
QPushButton#step:disabled {{ color: #5E4650; }}
QLineEdit, QComboBox, QPlainTextEdit, QListWidget {{ background: {C['surface']}; border: 3px solid {C['ink']};
              border-radius: 12px; padding: 8px 12px; font-size: 15px; selection-background-color: {C['maroon']}; }}
QLineEdit:focus, QComboBox:focus, QListWidget:focus {{ border: 3px solid {C['accent']}; }}
QLineEdit[bad="true"] {{ border: 3px solid {C['danger']}; }}
QComboBox QAbstractItemView {{ background: {C['surface']}; border: 3px solid {C['ink']};
                              selection-background-color: {C['maroon']}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QListWidget::item {{ padding: 6px; border-radius: 8px; }}
QListWidget::item:selected {{ background: {C['maroon']}; }}
QPlainTextEdit {{ font-family: 'JetBrains Mono', Consolas, monospace; font-size: 12px; }}
QCheckBox, QRadioButton {{ font-size: 15px; spacing: 10px; padding: 4px; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 22px; height: 22px; border: 3px solid {C['ink']};
              background: {C['surface2']}; }}
QCheckBox::indicator {{ border-radius: 7px; }}
QRadioButton::indicator {{ border-radius: 14px; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{ background: {C['primary']}; }}
QCheckBox:focus, QRadioButton:focus {{ color: {C['accent']}; }}
QProgressBar {{ background: {C['surface']}; border: 3px solid {C['ink']}; border-radius: 14px; height: 30px;
               text-align: center; font-weight: 900; color: {C['text']}; }}
QProgressBar::chunk {{ border-radius: 10px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
               stop:0 {C['primary']}, stop:1 {C['accent']}); }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 12px; }}
QScrollBar::handle:vertical {{ background: {C['maroon']}; border-radius: 6px; min-height: 40px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""


# ------------------------------------------------------------------ helpers
def hard_shadow(w, dx=4, dy=4):
    e = QGraphicsDropShadowEffect(w)
    e.setBlurRadius(0)
    e.setOffset(dx, dy)
    e.setColor(QColor(C["ink"]))
    w.setGraphicsEffect(e)
    return w


def label(text, name=None, wrap=True):
    l = QLabel(text)
    if name:
        l.setObjectName(name)
    l.setWordWrap(wrap)
    l.setTextFormat(Qt.RichText)
    return l


def button(text, name=None, shadow=True):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    b.setCursor(Qt.PointingHandCursor)
    if shadow:
        hard_shadow(b)
    return b


def pix(path, w=None, h=None):
    p = QPixmap(str(path))
    if p.isNull():
        return p
    if w and h:
        return p.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if w:
        return p.scaledToWidth(w, Qt.SmoothTransformation)
    if h:
        return p.scaledToHeight(h, Qt.SmoothTransformation)
    return p


def lapa(mood, h=None, w=None):
    l = QLabel()
    l.setPixmap(pix(SHARE / "lapa" / f"lapa-{mood}-small.png", w=w, h=h))
    l.setAlignment(Qt.AlignCenter)
    return l


def human(nbytes):
    for unit in (tr("Б"), tr("КБ"), tr("МБ"), tr("ГБ"), tr("ТБ")):
        if nbytes < 1024 or unit == tr("ТБ"):
            return f"{nbytes:.0f} {unit}" if unit in (tr("Б"), tr("КБ")) else f"{nbytes:.1f} {unit}"
        nbytes /= 1024


def set_prop(w, name, value):
    w.setProperty(name, value)
    w.style().unpolish(w)
    w.style().polish(w)


class Card(QFrame):
    clicked = Signal()

    def __init__(self, shadow=True):
        super().__init__()
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        if shadow:
            hard_shadow(self)

    def setSelected(self, on):
        set_prop(self, "selected", "true" if on else "false")

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.clicked.emit()
        else:
            super().keyPressEvent(e)


TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
                    ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r",
                     "s", "t", "u", "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya"]))


def make_username(fullname):
    s = "".join(TRANSLIT.get(ch, ch) for ch in fullname.lower().split(" ")[0])
    s = re.sub(r"[^a-z0-9_-]", "", s)
    if s and not re.match(r"[a-z_]", s[0]):
        s = "u" + s
    return s[:32]


RESERVED = {"root", "bin", "daemon", "mail", "ftp", "http", "nobody", "dbus", "systemd-network", "sddm", "gdm",
            "polkitd", "git", "furry-live", "uucp", "avahi", "colord", "rtkit"}


def password_score(pw):
    if not pw:
        return 0, ""
    score = min(len(pw), 16) / 16 * 2
    score += sum(bool(re.search(r, pw)) for r in (r"[a-zа-я]", r"[A-ZА-Я]", r"\d", r"[^\w]"))
    score = round(min(score, 6) / 6 * 4)
    return score, [tr("Очень слабый"), tr("Слабый"), tr("Нормальный"), tr("Хороший"), tr("Отличный")][score]


# ------------------------------------------------------------------ system probing
def list_disks():
    if DRY:
        return [
            {"path": "/dev/sda", "size": 256 * 1024 ** 3, "model": "VBOX HARDDISK", "tran": "sata", "pttype": "gpt",
             "esp": "/dev/sda1", "windows": True, "free": 120 * 1024 ** 3, "parts": [
                {"name": "sda1", "path": "/dev/sda1", "size": 100 * 1024 ** 2, "fstype": "vfat", "label": "EFI", "parttype": ESP_GUID},
                {"name": "sda2", "path": "/dev/sda2", "size": 135 * 1024 ** 3, "fstype": "ntfs", "label": "Windows"}],
             "shrink": [{"path": "/dev/sda2", "label": "Windows", "size": 135 * 1024 ** 3, "min": 60 * 1024 ** 3,
                         "probe": 0}]},
            {"path": "/dev/nvme0n1", "size": 512 * 1024 ** 3, "model": "Samsung SSD 980", "tran": "nvme",
             "pttype": "", "esp": "", "windows": False, "free": 0, "parts": [], "shrink": []},
            # another Linux (Arch) with a partition left free for FurrOS: the "own partitions" mode
            {"path": "/dev/sdb", "size": 476 * 1024 ** 3, "model": "Crucial MX500", "tran": "sata", "pttype": "gpt",
             "esp": "/dev/sdb1", "windows": False, "free": 0, "shrink": [], "parts": [
                {"name": "sdb1", "path": "/dev/sdb1", "size": 512 * 1024 ** 2, "fstype": "vfat", "label": "",
                 "parttype": ESP_GUID},
                {"name": "sdb2", "path": "/dev/sdb2", "size": 300 * 1024 ** 3, "fstype": "ext4", "label": "arch",
                 "parttype": "0fc63daf-8483-4772-8e79-3d69d8477de4"},
                {"name": "sdb3", "path": "/dev/sdb3", "size": 175 * 1024 ** 3, "fstype": "", "label": "",
                 "parttype": "0fc63daf-8483-4772-8e79-3d69d8477de4"}]},
        ]
    live = subprocess.run(["findmnt", "-no", "SOURCE", "/run/archiso/bootmnt"], capture_output=True,
                          text=True).stdout.strip()
    data = json.loads(subprocess.run(
        ["lsblk", "-J", "-b", "-o", "NAME,PATH,SIZE,MODEL,TRAN,TYPE,RO,FSTYPE,LABEL,PKNAME,PTTYPE,PARTTYPE,MOUNTPOINT"],
        capture_output=True, text=True).stdout or '{"blockdevices": []}')
    disks = []
    for d in data["blockdevices"]:
        if d["type"] != "disk" or d.get("ro") or d["name"].startswith(("loop", "zram", "sr")):
            continue
        children = d.get("children") or []
        if is_live_medium(d, live):
            continue
        esp = next((c["path"] for c in children if (c.get("parttype") or "").lower() == ESP_GUID), "")
        disks.append({"path": d["path"], "size": int(d["size"]), "model": (d.get("model") or tr("Диск")).strip(),
                      "tran": d.get("tran") or "", "pttype": d.get("pttype") or "", "esp": esp,
                      # Windows: its reserved partition (GPT) or a BitLocker volume; a lone NTFS may be a data disk
                      "windows": any((c.get("parttype") or "").lower() == MSR_GUID or c.get("fstype") == "BitLocker"
                                     for c in children), "free": free_space(d["path"]),
                      "parts": [
                          {"name": c["name"], "path": c["path"], "size": int(c["size"]), "fstype": c.get("fstype") or "",
                           "label": c.get("label") or "", "parttype": (c.get("parttype") or "").lower()}
                          for c in children],
                      # NTFS partitions FurrOS could shrink to make room (only looked at on GPT disks with an ESP)
                      "shrink": [ntfs_shrink_info(c) for c in children if c.get("fstype") == "ntfs"]
                                if esp and d.get("pttype") == "gpt" else []})
    return disks


def _tree(node):
    yield node
    for c in node.get("children") or []:
        yield from _tree(c)


def is_live_medium(disk, live):
    """The stick FurrOS runs from. Written with dd it holds the ISO itself; with Ventoy the ISO is a file on an exFAT
    partition, mapped through device-mapper (/dev/mapper/ventoy) and the boot partition is labelled VTOYEFI."""
    for n in _tree(disk):
        if live and n.get("path") == live:
            return True
        if (n.get("mountpoint") or "").startswith("/run/archiso"):
            return True
        if n.get("fstype") == "iso9660" and (n.get("label") or "").upper().startswith("FURROS"):
            return True
        if n.get("label") == "VTOYEFI":
            return True
    return False


def as_root(cmd):
    return cmd if os.geteuid() == 0 else ["sudo", "-n"] + cmd


def ntfs_shrink_info(c):
    """How small this NTFS partition can get: ntfs-3g.probe (0 = clean, 14 = hibernated / Fast Startup) and
    ntfsresize --info-mb-only, the smallest size it supports (read-only, ~ the used space)."""
    info = {"path": c["path"], "label": c.get("label") or "", "size": int(c["size"]), "min": 0, "probe": -1}
    try:
        info["probe"] = subprocess.run(as_root(["ntfs-3g.probe", "--readwrite", c["path"]]), capture_output=True,
                                       timeout=20).returncode
        if info["probe"] == 0:
            text = subprocess.run(as_root(["ntfsresize", "--force", "--info-mb-only", c["path"]]), capture_output=True,
                                  text=True, timeout=120).stdout
            info["min"] = ntfs_min_bytes(text)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return info


def ntfs_min_bytes(text):
    """ntfsresize --info-mb-only prints "Minsize (in MB): 2105" (nothing when it can't shrink). Its MB are 10^6;
    counted here as MiB, which leaves Windows a little more room."""
    m = re.search(r"Minsize[^:]*:\s*(\d+)", text or "")
    return int(m.group(1)) * 1024 ** 2 if m else 0


FURROS_MIN = 20 * 1024 ** 3   # the smallest FurrOS partition
WIN_RESERVE = 10 * 1024 ** 3  # free space left inside Windows after shrinking: updates, the page file, restore points


def shrink_room(info):
    """Biggest size FurrOS may take from this NTFS partition (whole GiB), 0 if it can't be shrunk."""
    if info.get("probe") != 0 or not info.get("min"):
        return 0
    return max(0, (info["size"] - info["min"] - WIN_RESERVE) // 1024 ** 3 * 1024 ** 3)


def shrink_candidate(d):
    """The NTFS partition with the most room to give, if the disk has no free space of its own."""
    best = max(d.get("shrink") or [], key=shrink_room, default=None)
    return best if best and shrink_room(best) >= FURROS_MIN else None


ESP_GUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
MSR_GUID = "e3c9e316-0b5c-4db8-817d-f92df00215ae"


def free_space(disk):
    """Size in bytes of the biggest unpartitioned gap (where FurrOS goes when installing next to Windows)."""
    # the window runs as the live user, who can't open /dev/sdX: without root parted prints nothing and every disk
    # looked full ("less than 20 GB free"). The live user has passwordless sudo
    cmd = as_root(["parted", "-sm", disk, "unit", "B", "print", "free"])
    try:
        lines = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return 0
    rows = (line.rstrip(";").split(":") for line in lines)
    mib = 1024 ** 2
    # the backend puts partitions on 1 MiB boundaries: count only the aligned part of every gap
    return max((max(0, (int(f[2].rstrip("B")) + 1) // mib * mib - -(-int(f[1].rstrip("B")) // mib) * mib)
                for f in rows if len(f) >= 5 and f[4] == "free"), default=0)


def timezones():
    try:
        import zoneinfo
        zs = sorted(z for z in zoneinfo.available_timezones() if "/" in z and not z.startswith(("Etc/", "SystemV")))
        if zs:
            return zs
    except Exception:  # noqa: BLE001
        pass
    return ["Europe/Moscow", "Europe/Kaliningrad", "Europe/Samara", "Asia/Yekaterinburg", "Asia/Omsk",
            "Asia/Novosibirsk", "Asia/Krasnoyarsk", "Asia/Irkutsk", "Asia/Yakutsk", "Asia/Vladivostok",
            "Asia/Magadan", "Asia/Kamchatka", "Europe/Kyiv", "Europe/Minsk", "Asia/Almaty", "Europe/Berlin",
            "Europe/London", "America/New_York"]


class Async(QObject):
    done = Signal(str, object)

    def run(self, key, fn):
        def target():
            try:
                res = fn()
            except Exception as e:  # noqa: BLE001
                res = e
            try:
                self.done.emit(key, res)
            except RuntimeError:
                pass  # window closed before the check finished
        threading.Thread(target=target, daemon=True).start()


def check_internet():
    try:
        socket.create_connection(("archlinux.org", 443), timeout=5).close()
        return True
    except OSError:
        return False


def geo_timezone():
    with urllib.request.urlopen("https://ipapi.co/timezone", timeout=4) as r:
        return r.read().decode().strip()


# ------------------------------------------------------------------ pages
class Page(QWidget):
    title = ""
    subtitle = ""
    mood = "hoodie"
    tip = ""
    step_name = ""
    changed = Signal()

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.plan = win.plan
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        self.body = QVBoxLayout(inner)
        self.body.setContentsMargins(4, 4, 16, 16)
        self.body.setSpacing(14)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def valid(self):
        return True

    def enter(self):
        pass

    def leave(self):
        pass


class WelcomePage(Page):
    title = "Привет! Я Лапа 🐾"
    step_name = "Привет"
    mood = "wave"
    tip = "Я буду рядом всю установку и подскажу, если что-то непонятно. Наведи мышку на любой пункт, чтобы узнать больше!"

    def __init__(self, win):
        super().__init__(win)
        row = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(16)
        left.addWidget(label(tr("Добро пожаловать в <b style='color:#7FF0F0'>FurrOS</b>, пушистый дистрибутив "
                             "на основе Arch Linux. За пару минут мы вместе настроим систему под тебя: "
                             "выберем рабочий стол, программы, обои и создадим твой аккаунт."), "sub"))
        left.addWidget(label("Язык · Language · Język · Idioma", "h2"))
        langs = QHBoxLayout()
        langs.setSpacing(10)
        for code, (_loc, native, _kb, _tz) in catalog.LANGUAGES.items():
            b = button(native, "primary" if code == LANG else None)
            b.setAccessibleName(native)
            b.clicked.connect(lambda _=False, c=code: self.win.switch_lang(c))
            langs.addWidget(b)
        langs.addStretch()
        left.addLayout(langs)
        left.addWidget(label(tr("Язык системы"), "h2"))
        self.locale = QComboBox()
        for code, name in catalog.LOCALES:
            self.locale.addItem(name, code)
        self.locale.setCurrentIndex(max(0, self.locale.findData(catalog.LANGUAGES[LANG][0])))
        self.locale.setToolTip(tr("На этом языке будут меню, программы и сообщения системы"))
        self.locale.currentIndexChanged.connect(self.sync)
        left.addWidget(self.locale)

        info = QFrame()
        info.setObjectName("card")
        hard_shadow(info)
        il = QVBoxLayout(info)
        il.addWidget(label(tr("<b>Что понадобится</b>"), "h2"))
        for t in (tr("Интернет: пакеты скачиваются свежими"), tr("От 20 ГБ на диске, лучше 40 ГБ и больше"),
                  tr("Около 10–30 минут, смотря какая скорость интернета"),
                  tr("Важные файлы с выбранного диска лучше сохранить заранее")):
            il.addWidget(label(f"<span style='color:#FF8CBE'>●</span>&nbsp; {t}"))
        left.addWidget(info)

        btns = QHBoxLayout()
        academy = button(tr("Сначала пройти обучение"))
        academy.setToolTip(tr("Откроет «Школу Лапы»: уроки о том, как пользоваться FurrOS"))
        academy.clicked.connect(lambda: subprocess.Popen(["furros-academy"]) if shutil.which("furros-academy") else None)
        btns.addWidget(academy)
        btns.addStretch()
        left.addLayout(btns)
        left.addStretch()
        row.addLayout(left, 3)
        row.addWidget(lapa("wave", h=430), 2)
        self.body.addLayout(row)
        self.sync()

    def sync(self):
        self.plan["locale"] = self.locale.currentData()


class TermsPage(Page):
    title = "Условия использования"
    subtitle = "Прочитай, пожалуйста. Тут коротко и по делу"
    step_name = "Условия"
    mood = "hoodie"
    tip = "Главное: FurrOS бесплатная, без гарантий, слежки нет, а арт принадлежит его авторам и только для личного использования."

    def __init__(self, win):
        super().__init__(win)
        card = QFrame()
        card.setObjectName("card")
        hard_shadow(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 14, 22, 18)
        text = label(TERMS.get(LANG, TERMS["en"]))
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cl.addWidget(text)
        self.body.addWidget(card)
        self.accept = QCheckBox(tr("Я прочитал(а) и принимаю условия использования"))
        self.accept.toggled.connect(self.sync)
        self.body.addWidget(self.accept)
        self.body.addStretch()

    def sync(self, on):
        self.plan["terms_accepted"] = bool(on)
        self.changed.emit()

    def valid(self):
        return self.accept.isChecked()


class ChecksPage(Page):
    title = "Проверка готовности"
    subtitle = "Смотрю, подходит ли компьютер для FurrOS"
    step_name = "Проверка"
    mood = "timer"
    tip = "Красный пункт останавливает установку, жёлтый просто предупреждает. Если нет интернета, подключись через значок сети в углу экрана."

    def __init__(self, win):
        super().__init__(win)
        self.rows = {}
        self.state = {}
        for key, title in [("net", tr("Интернет")), ("boot", tr("Режим загрузки")), ("ram", tr("Оперативная память")),
                           ("disk", tr("Подходящий диск")), ("gpu", tr("Видеокарта")), ("power", tr("Питание"))]:
            card = QFrame()
            card.setObjectName("card")
            hard_shadow(card)
            h = QHBoxLayout(card)
            icon = QLabel("…")
            icon.setFixedWidth(40)
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("font-size: 24px; font-weight: 900;")
            text = QVBoxLayout()
            text.addWidget(label(f"<b>{title}</b>"))
            det = label(tr("Проверяю…"), "dim")
            text.addWidget(det)
            h.addWidget(icon)
            h.addLayout(text, 1)
            self.rows[key] = (icon, det)
            self.body.addWidget(card)
        again = button(tr("Проверить снова"))
        again.clicked.connect(self.enter)
        self.body.addWidget(again, 0, Qt.AlignLeft)
        self.body.addStretch()
        self.async_ = Async()
        self.async_.done.connect(self.on_async)

    def set(self, key, level, text):
        icon, det = self.rows[key]
        sym, col = {"ok": ("✓", C["ok"]), "warn": ("!", C["warn"]), "bad": ("✕", C["danger"]),
                    "wait": ("…", C["dim"])}[level]
        icon.setText(sym)
        icon.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {col};")
        det.setText(text)
        self.state[key] = level
        self.changed.emit()

    def enter(self):
        self.set("net", "wait", tr("Стучусь на archlinux.org…"))
        self.async_.run("net", lambda: True if DRY else check_internet())
        uefi = Path("/sys/firmware/efi").exists() or (DRY and os.environ.get("FURROS_DRY_BIOS") != "1")
        self.plan["_uefi"] = uefi
        self.set("boot", "ok", tr("UEFI: современный режим, всё отлично") if uefi
                 else tr("Legacy BIOS: тоже подойдёт, поставлю загрузчик Limine"))
        ram = 8 * 1024 ** 3
        if LINUX:
            try:
                kb = int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1))
                ram = kb * 1024
            except Exception:  # noqa: BLE001
                pass
        if ram < 1.5 * 1024 ** 3:
            self.set("ram", "bad", tr('{0}: слишком мало, нужно хотя бы 2 ГБ').format(human(ram)))
        elif ram < 4 * 1024 ** 3:
            self.set("ram", "warn", tr('{0}: хватит, но лучше выбрать лёгкую оболочку (Xfce, LXQt)').format(human(ram)))
        else:
            self.set("ram", "ok", tr('{0}: с запасом').format(human(ram)))
        self.plan["_ram"] = ram
        # in the background: measuring how far a big Windows partition can shrink takes a while
        self.set("disk", "wait", tr("Смотрю диски…"))
        self.async_.run("disk", list_disks)
        on_battery = False
        if LINUX:
            for ps in Path("/sys/class/power_supply").glob("*"):
                try:
                    if (ps / "type").read_text().strip() == "Mains" and (ps / "online").read_text().strip() == "0":
                        on_battery = True
                except OSError:
                    pass
        self.check_gpu()
        self.set("power", "warn" if on_battery else "ok",
                 tr("Ноутбук работает от батареи. Лучше подключить зарядку") if on_battery else tr("Всё в порядке"))

    def check_gpu(self):
        """Which graphics drivers will be installed (same logic as the backend and furros-drivers)."""
        if DRY or not LINUX:
            cards = furros_hw.gpus("01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA106 "
                                   "[GeForce RTX 3060] [10de:2504] (rev a1)")
            hw = furros_hw.plan(cards, laptop=False, vm="")
        else:
            hw = furros_hw.plan()
        lines = [tr(text).format(*args) for _, text, args in hw["notes"]]
        warn = any(level == "warn" for level, _, _ in hw["notes"])
        self.set("gpu", "warn" if warn else "ok", "<br>".join(lines) or tr("Всё в порядке"))

    def on_async(self, key, res):
        if key == "disk":
            disks = res if isinstance(res, list) else []
            self.win.disks = disks
            big = [d for d in disks if d["size"] >= 20 * 1024 ** 3]
            if big:
                self.set("disk", "ok", tr('Нашла {0} шт.: ').format(len(big)) + ", ".join(f"{d['model']} ({human(d['size'])})" for d in big))
            else:
                self.set("disk", "bad", tr("Нет диска на 20 ГБ и больше"))
        if key == "net":
            self.set("net", "ok" if res is True else "bad",
                     tr("Есть соединение") if res is True else tr("Нет интернета. Подключись к сети и нажми «Проверить снова»"))

    def valid(self):
        return all(self.state.get(k) in ("ok", "warn") for k in ("net", "ram", "disk"))


class RegionPage(Page):
    title = "Где ты живёшь?"
    subtitle = "Часовой пояс и раскладки клавиатуры"
    step_name = "Регион"
    mood = "hoodie"
    tip = "Часовой пояс я попробовала угадать по интернету. Раскладки переключаются выбранным сочетанием клавиш, а первая в списке будет основной."

    def __init__(self, win):
        super().__init__(win)
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.addWidget(label(tr("Часовой пояс"), "h2"), 0, 0)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("Поиск: Moscow, Novosibirsk, Kyiv…"))
        self.search.setAccessibleName(tr("Поиск часового пояса"))
        self.search.textChanged.connect(self.filter)
        grid.addWidget(self.search, 1, 0)
        self.tz = QListWidget()
        self.tz.setMinimumHeight(300)
        self.all_tz = timezones()
        for z in self.all_tz:
            self.tz.addItem(z)
        self.tz.currentTextChanged.connect(self.sync)
        grid.addWidget(self.tz, 2, 0, 3, 1)
        self.tz_hint = label("", "dim")
        grid.addWidget(self.tz_hint, 5, 0)

        grid.addWidget(label(tr("Раскладки"), "h2"), 0, 1)
        self.kb_search = QLineEdit()
        self.kb_search.setPlaceholderText(tr("Поиск: Русский, фонетическая, de…"))
        self.kb_search.setAccessibleName(tr("Поиск раскладки"))
        self.kb_search.textChanged.connect(self.kb_filter)
        grid.addWidget(self.kb_search, 1, 1)
        self.kb = QListWidget()
        for code, name, variant in catalog.KEYBOARDS:
            text = f"{name} — {tr(variant)}" if variant else name
            it = QListWidgetItem(f"{text}  ({code})")
            it.setData(Qt.UserRole, code)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked)
            self.kb.addItem(it)
        self.kb_defaults = []
        self.kb_touched = False   # once the user ticks something, a new system language no longer resets the list
        self.set_kb_defaults(catalog.system_language(catalog.LANGUAGES[LANG][0])[2])
        self.kb.itemChanged.connect(self.kb_changed)
        self.kb.setMinimumHeight(240)
        grid.addWidget(self.kb, 2, 1)
        grid.addWidget(label(tr("Переключение раскладки")), 3, 1)
        self.toggle = QComboBox()
        for code, name in catalog.LAYOUT_TOGGLES:
            self.toggle.addItem(tr(name), code)
        self.toggle.currentIndexChanged.connect(self.sync)
        grid.addWidget(self.toggle, 4, 1)
        self.test = QLineEdit()
        self.test.setPlaceholderText(tr("Попробуй напечатать что-нибудь тут"))
        grid.addWidget(self.test, 5, 1)
        self.kb_err = label("", "err")
        grid.addWidget(self.kb_err, 6, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.body.addLayout(grid)
        self.body.addStretch()
        self.select_tz(catalog.LANGUAGES[LANG][3])
        self.async_ = Async()
        self.async_.done.connect(self.on_geo)
        self.async_.run("geo", geo_timezone)

    def select_tz(self, z):
        items = self.tz.findItems(z, Qt.MatchExactly)
        if items:
            self.tz.setCurrentItem(items[0])
            self.tz.scrollToItem(items[0])

    def on_geo(self, _key, res):
        if isinstance(res, str) and res in self.all_tz:
            self.select_tz(res)
            self.tz_hint.setText(tr('Определила автоматически: <b>{0}</b>').format(res))

    def filter(self, text):
        t = text.lower().replace(" ", "_")
        for i in range(self.tz.count()):
            it = self.tz.item(i)
            it.setHidden(t not in it.text().lower())

    def set_kb_defaults(self, codes):
        """Tick the layouts of the chosen system language (the first one becomes the main layout)."""
        self.kb_defaults = list(codes)
        self.kb.blockSignals(True)
        for i in range(self.kb.count()):
            it = self.kb.item(i)
            it.setCheckState(Qt.Checked if it.data(Qt.UserRole) in self.kb_defaults else Qt.Unchecked)
        self.kb.blockSignals(False)

    def kb_changed(self, *_):
        self.kb_touched = True
        self.sync()

    def kb_filter(self, text):
        t = text.strip().lower()
        for i in range(self.kb.count()):
            it = self.kb.item(i)
            # ticked layouts always stay visible, so a search never hides what is already chosen
            it.setHidden(bool(t) and t not in it.text().lower() and it.checkState() != Qt.Checked)

    def enter(self):
        # the system language was picked on the first page: its layouts, unless the user already chose some here
        if not self.kb_touched:
            self.set_kb_defaults(catalog.system_language(self.plan.get("locale", ""))[2])
            self.sync()

    def sync(self, *_):
        if self.tz.currentItem():
            self.plan["timezone"] = self.tz.currentItem().text()
        ticked = [self.kb.item(i).data(Qt.UserRole) for i in range(self.kb.count())
                  if self.kb.item(i).checkState() == Qt.Checked]
        # the language's own layouts first, in their order (the first one is the main layout), then the rest
        layouts = [c for c in self.kb_defaults if c in ticked] + [c for c in ticked if c not in self.kb_defaults]
        self.plan["layouts"] = layouts
        self.plan["layout_toggle"] = self.toggle.currentData()
        self.kb_err.setText("" if layouts else tr("Выбери хотя бы одну раскладку"))
        self.changed.emit()

    def valid(self):
        return bool(self.plan.get("layouts")) and bool(self.plan.get("timezone"))


class DiskPage(Page):
    title = "Куда ставим?"
    subtitle = "Выбери, как ставить FurrOS, и диск"
    step_name = "Диск"
    mood = "grr"
    tip = "Грр! В режиме «Весь диск» всё, что на нём есть, исчезнет. Чтобы оставить Windows, выбери «Рядом с Windows»."

    def __init__(self, win):
        super().__init__(win)
        modes = QHBoxLayout()
        modes.setSpacing(24)
        self.mode_group = QButtonGroup(self)
        for code, name, desc in [
                ("whole", tr("Весь диск"), tr("FurrOS займёт выбранный диск целиком. Всё, что на нём было, удалится")),
                ("alongside", tr("Рядом с Windows"),
                 tr("FurrOS встанет в свободное место, Windows останется. При включении выбираешь систему")),
                ("manual", tr("Свои разделы"),
                 tr("Разметь диск сам и выбери, куда ставить. Подходит, если рядом уже стоит другой Linux"))]:
            box = QVBoxLayout()
            r = QRadioButton(name)
            r.setProperty("code", code)
            r.setChecked(code == "whole")
            self.mode_group.addButton(r)
            box.addWidget(r)
            box.addWidget(label(desc, "dim"))
            modes.addLayout(box, 1)
        self.mode_group.buttonToggled.connect(self.mode_changed)
        self.body.addLayout(modes)
        self.alongside_help = label(tr(
            "<b>Сначала в Windows:</b><br>"
            "1. Место: если диск C: не зашифрован BitLocker, FurrOS сама возьмёт у Windows сколько скажешь. "
            "С BitLocker освободи место заранее: «Управление дисками» (Win+X) → правой кнопкой по диску C: → «Сжать том», "
            "хотя бы 20 ГБ (лучше 50 и больше). В обоих случаях сначала сделай копию важных файлов.<br>"
            "2. Выключи гибернацию и «Быстрый запуск»: командная строка от администратора → <b>powercfg /h off</b>, "
            "затем «Завершение работы» (не перезагрузка). Крупные обновления Windows могут включить его снова.<br>"
            "3. <b>BitLocker</b> (часто включён на ноутбуках с Windows 11): сохрани ключ восстановления "
            "(aka.ms/myrecoverykey) и приостанови защиту BitLocker прямо перед отключением Secure Boot. "
            "Если Windows попросит ключ, когда ты выбираешь её в меню FurrOS, запускай её через загрузочное "
            "меню компьютера (F8, F11 или F12).<br>Нужен режим загрузки UEFI."), "dim")
        self.alongside_help.setVisible(False)
        self.body.addWidget(self.alongside_help)
        self.mode_note = label("", "err")
        self.mode_note.setVisible(False)
        self.body.addWidget(self.mode_note)
        self.cards_box = QVBoxLayout()
        self.cards_box.setSpacing(12)
        self.body.addLayout(self.cards_box)
        self.cards = []

        # "own partitions": the person partitions (KDE Partition Manager is on the live medium), then picks a
        # partition for FurrOS (formatted) and an existing EFI partition (only added to)
        self.manual_box = QFrame()
        self.manual_box.setObjectName("card")
        mb = QGridLayout(self.manual_box)
        mb.setContentsMargins(16, 12, 16, 12)
        mb.setVerticalSpacing(8)
        mb.addWidget(label(tr("Сначала создай раздел для FurrOS (от 20 ГБ) в менеджере разделов, потом выбери его здесь. "
                              "Раздел EFI нужен уже существующий: загрузчик FurrOS ляжет рядом с загрузчиком другой "
                              "системы, ничего не удаляя. Нужен режим загрузки UEFI."), "dim"), 0, 0, 1, 3)
        mb.addWidget(label(tr("Раздел для FurrOS"), wrap=False), 1, 0)
        self.root_combo = QComboBox()
        mb.addWidget(self.root_combo, 1, 1, 1, 2)
        mb.addWidget(label(tr("Раздел EFI"), wrap=False), 2, 0)
        self.esp_combo = QComboBox()
        mb.addWidget(self.esp_combo, 2, 1, 1, 2)
        pm = button(tr("Открыть менеджер разделов"), "link", shadow=False)
        pm.clicked.connect(self.open_partition_manager)
        mb.addWidget(pm, 3, 1)
        rf = button(tr("Обновить список"), "link", shadow=False)
        rf.clicked.connect(self.refresh_parts)
        mb.addWidget(rf, 3, 2)
        mb.setColumnStretch(1, 1)
        self.root_combo.currentIndexChanged.connect(self.root_changed)
        self.esp_combo.currentIndexChanged.connect(self.sync)
        self.manual_box.setVisible(False)
        self.body.addWidget(self.manual_box)

        # no free space next to Windows: FurrOS takes it from the Windows partition (ntfsresize)
        self.shrink_box = QFrame()
        self.shrink_box.setObjectName("card")
        sb = QVBoxLayout(self.shrink_box)
        sb.setContentsMargins(16, 12, 16, 12)
        self.shrink_text = label("", "dim")
        sb.addWidget(self.shrink_text)
        row = QHBoxLayout()
        row.addWidget(label(tr("Отдать FurrOS:"), wrap=False))
        self.shrink_gb = QSpinBox()
        self.shrink_gb.setSuffix(" " + tr("ГБ"))
        self.shrink_gb.setMinimumWidth(130)
        self.shrink_gb.valueChanged.connect(self.sync)
        row.addWidget(self.shrink_gb)
        self.shrink_left = label("", "dim")
        row.addWidget(self.shrink_left, 1)
        sb.addLayout(row)
        sb.addWidget(label(tr("Раздел Windows станет меньше, файлы на нём останутся. При первом запуске Windows "
                              "проверит диск (синий экран с процентами) — так и должно быть, не выключай компьютер."),
                           "dim"))
        self.shrink_box.setVisible(False)
        self.shrink_for = None
        self.body.addWidget(self.shrink_box)

        opts = QGridLayout()
        opts.setHorizontalSpacing(24)
        opts.setVerticalSpacing(2)
        opts.addWidget(label(tr("Файловая система"), "h2"), 0, 0)
        self.fs_group = QButtonGroup(self)
        for i, (code, name, desc) in enumerate([
            ("btrfs", tr("Btrfs (рекомендуем)"), tr("Сжатие и снимки системы: можно откатиться, если обновление что-то сломает")),
            ("ext4", "ext4", tr("Классика: просто и надёжно, но без снимков для отката"))]):
            r = QRadioButton(name)
            r.setProperty("code", code)
            r.setChecked(code == "btrfs")
            self.fs_group.addButton(r)
            opts.addWidget(r, 1 + i * 2, 0)
            opts.addWidget(label(desc, "dim"), 2 + i * 2, 0)
        opts.addWidget(label(tr("Подкачка (swap)"), "h2"), 0, 1)
        self.swap_group = QButtonGroup(self)
        for i, (code, name, desc) in enumerate([
            ("zram", tr("zram (рекомендуем)"), tr("Сжатая подкачка в памяти: быстро и не тратит диск")),
            ("file", tr("Файл подкачки 4 ГБ"), tr("Нужен, если хочешь спящий режим или у тебя мало памяти")),
            ("none", tr("Без подкачки"), tr("Если памяти очень много"))]):
            r = QRadioButton(name)
            r.setProperty("code", code)
            r.setChecked(code == "zram")
            self.swap_group.addButton(r)
            opts.addWidget(r, 1 + i * 2, 1)
            opts.addWidget(label(desc, "dim"), 2 + i * 2, 1)
        self.fs_group.buttonToggled.connect(self.sync)
        self.swap_group.buttonToggled.connect(self.sync)
        self.body.addLayout(opts)

        self.body.addWidget(label(tr("Шифрование"), "h2"))
        self.enc = QCheckBox(tr("Зашифровать диск (LUKS2): без пароля никто не прочитает твои файлы"))
        self.enc.toggled.connect(self.sync)
        self.body.addWidget(self.enc)
        self.enc_box = QWidget()
        eb = QGridLayout(self.enc_box)
        eb.setContentsMargins(34, 0, 0, 0)
        self.enc_pw = QLineEdit()
        self.enc_pw.setEchoMode(QLineEdit.Password)
        self.enc_pw.setPlaceholderText(tr("Пароль шифрования"))
        self.enc_pw2 = QLineEdit()
        self.enc_pw2.setEchoMode(QLineEdit.Password)
        self.enc_pw2.setPlaceholderText(tr("Ещё раз"))
        for w in (self.enc_pw, self.enc_pw2):
            w.textChanged.connect(self.sync)
        eb.addWidget(self.enc_pw, 0, 0)
        eb.addWidget(self.enc_pw2, 0, 1)
        self.enc_err = label("", "err")
        eb.addWidget(self.enc_err, 1, 0, 1, 2)
        eb.addWidget(label(tr("Этот пароль придётся вводить при каждом включении. Если забудешь, данные не восстановить."),
                           "dim"), 2, 0, 1, 2)
        self.enc_box.setVisible(False)
        self.body.addWidget(self.enc_box)

        self.layout_preview = label("", "dim")
        self.body.addWidget(self.layout_preview)
        self.body.addStretch()

    def enter(self):
        bios = not self.plan.get("_uefi", True)
        self.enc.setEnabled(not bios and self.mode() != "manual")
        if bios:
            self.enc.setChecked(False)
            self.enc.setToolTip(tr("Шифрование доступно только при загрузке в режиме UEFI"))
        if self.cards:
            return
        for d in self.win.disks:
            card = Card()
            h = QHBoxLayout(card)
            h.setContentsMargins(16, 12, 16, 12)
            kind = {"nvme": "NVMe SSD", "sata": "SATA", "usb": tr("USB-диск"), "mmc": tr("Карта памяти")}.get(d["tran"],
                                                                                                    d["tran"].upper())
            v = QVBoxLayout()
            v.addWidget(label(f"<b style='font-size:17px'>{d['model']}</b>&nbsp;&nbsp;"
                              f"<span style='color:#C8AAB4'>{d['path']} · {kind}</span>"))
            parts = ", ".join(f"{p['label'] or p['name']} ({p['fstype'] or '?'}, {human(p['size'])})"
                              for p in d["parts"]) or tr("пустой диск")
            v.addWidget(label(tr('Сейчас на нём: {0}').format(parts), "dim"))
            free = label(tr('Свободно (не размечено): {0}').format(human(d.get("free", 0))), "dim")
            free.setVisible(False)
            v.addWidget(free)
            h.addLayout(v, 1)
            size = label(f"<b style='font-size:20px; color:#7FF0F0'>{human(d['size'])}</b>", wrap=False)
            h.addWidget(size)
            card.clicked.connect(lambda d=d: self.pick(d))
            self.cards.append((card, d, free))
            self.cards_box.addWidget(card)
        self.fill_parts()
        self.mode_changed()

    def fill_parts(self):
        """Partitions for "own partitions": any partition of 20 GB+ that isn't an EFI or Windows' reserved one,
        and the existing EFI partitions, with file system and label so the right one is easy to spot."""
        keep_root, keep_esp = self.root_combo.currentData(), self.esp_combo.currentData()
        for c in (self.root_combo, self.esp_combo):
            c.blockSignals(True)
            c.clear()
        for d in self.win.disks:
            for p in d["parts"]:
                text = f"{p['path']} · {human(p['size'])} · {p['fstype'] or '?'}" + (f" · {p['label']}" if p['label'] else "")
                if p.get("parttype") == ESP_GUID:
                    self.esp_combo.addItem(f"{text} · {d['model']}", (p["path"], d["path"]))
                elif p.get("parttype") != MSR_GUID and p["size"] >= FURROS_MIN:
                    self.root_combo.addItem(f"{text} · {d['model']}", (p["path"], d["path"]))
        for c, keep in ((self.root_combo, keep_root), (self.esp_combo, keep_esp)):
            i = c.findData(keep) if keep else -1
            c.setCurrentIndex(i if i >= 0 else (0 if c.count() else -1))
            c.blockSignals(False)
        if not keep_esp:
            self.root_changed()

    def root_changed(self, *_):
        """The EFI partition of the same disk is the natural pick (another Linux there boots from it)."""
        r = self.root_combo.currentData()
        if r:
            for i in range(self.esp_combo.count()):
                if self.esp_combo.itemData(i)[1] == r[1]:
                    self.esp_combo.setCurrentIndex(i)
                    break
        self.sync()

    def refresh_parts(self):
        self.win.disks = list_disks()
        self.fill_parts()
        self.sync()

    def open_partition_manager(self):
        subprocess.Popen(["partitionmanager"], start_new_session=True)

    def why_not(self, d):
        """Why this disk can't be used in the current mode ("" = it can)."""
        if self.mode() == "whole":
            return tr("Слишком маленький: нужно хотя бы 20 ГБ") if d["size"] < 20 * 1024 ** 3 else ""
        if not self.plan.get("_uefi", True):
            return tr("Установка рядом с Windows работает только в режиме UEFI")
        if not d.get("parts"):
            # Windows on one disk, FurrOS on another, empty one: that's "whole disk", not "next to Windows"
            return tr("Этот диск пустой: выбери «Весь диск». Windows на другом диске останется, её можно будет выбрать при включении")
        if d.get("pttype") != "gpt" or not d.get("esp"):
            return tr("На этом диске нет раздела EFI (диск не GPT): поставь FurrOS на весь диск или на другой")
        if d.get("free", 0) >= FURROS_MIN or shrink_candidate(d):
            return ""
        shrink = d.get("shrink") or []
        if any(i.get("probe") in (14, 15) for i in shrink):
            return tr("Windows не выключена до конца (включён «Быстрый запуск» или гибернация): выполни в Windows "
                      "powercfg /h off и выключи компьютер через «Завершение работы»")
        if any(p.get("fstype") == "BitLocker" for p in d.get("parts", [])):
            return tr("Раздел Windows зашифрован BitLocker, FurrOS не может его сжать: освободи место в Windows "
                      "(«Управление дисками» → «Сжать том», хотя бы 30 ГБ)")
        return tr("На диске меньше 20 ГБ свободного места: освободи место в Windows («Сжать том»)")

    def shrink_plan(self, d):
        """The partition to shrink when this disk has no free space of its own, else None."""
        if not d or self.mode() != "alongside" or d.get("free", 0) >= FURROS_MIN:
            return None
        return shrink_candidate(d)

    def mode(self):
        b = self.mode_group.checkedButton()
        return b.property("code") if b else "whole"

    def mode_changed(self, *_):
        alongside = self.mode() == "alongside"
        manual = self.mode() == "manual"
        self.plan["mode"] = self.mode()
        self.alongside_help.setVisible(alongside)
        self.manual_box.setVisible(manual)
        if manual:
            self.enc.setChecked(False)
        self.enc.setEnabled(self.plan.get("_uefi", True) and not manual)
        for card, _d, _f in self.cards:
            card.setVisible(not manual)
        if manual:
            self.sync()
            return
        for card, d, free in self.cards:
            why = self.why_not(d)
            card.setEnabled(not why)
            card.setToolTip(why)
            # greyed text, not an opacity effect: the card already carries its drop shadow effect
            card.setStyleSheet("QLabel { color: #6E5560; }" if why else "")
            free.setVisible(alongside)
        cur = self.plan.get("_disk_info")
        if cur is None or self.why_not(cur):
            first = next((d for c, d, _f in self.cards if c.isEnabled()), None)
            if first:
                self.pick(first)
                return
            self.plan["disk"] = ""
            self.plan["_disk_info"] = None
            for c, _d, _f in self.cards:
                c.setSelected(False)
        self.sync()

    def pick(self, disk):
        self.plan["disk"] = disk["path"]
        self.plan["_disk_info"] = disk
        self.plan["esp"] = disk.get("esp", "")
        for c, d, _f in self.cards:
            c.setSelected(d is disk)
        self.sync()

    def sync(self, *_):
        b = self.fs_group.checkedButton()
        self.plan["filesystem"] = b.property("code") if b else "btrfs"
        b = self.swap_group.checkedButton()
        self.plan["swap"] = b.property("code") if b else "zram"
        enc = self.enc.isChecked()
        self.enc_box.setVisible(enc)
        self.plan["encrypt"] = enc
        self.plan["encrypt_password"] = self.enc_pw.text() if enc else ""
        err = ""
        if enc:
            if len(self.enc_pw.text()) < 6:
                err = tr("Пароль шифрования: минимум 6 символов")
            elif not all(" " <= ch <= "~" for ch in self.enc_pw.text()):
                # typed before the system is up (initramfs): only the US layout is guaranteed to work there
                err = tr("Пароль шифрования: только латинские буквы, цифры и знаки — при включении компьютера русская раскладка недоступна")
            elif self.enc_pw.text() != self.enc_pw2.text():
                err = tr("Пароли не совпадают")
        self.enc_err.setText(err)
        set_prop(self.enc_pw2, "bad", "true" if err == tr("Пароли не совпадают") else "false")
        if self.mode() == "manual":
            self.shrink_box.setVisible(False)
            self.plan.pop("shrink", None)
            r, e = self.root_combo.currentData(), self.esp_combo.currentData()
            self.plan["root_part"] = r[0] if r else ""
            self.plan["esp"] = e[0] if e else ""
            self.plan["disk"] = r[1] if r else ""
            self.plan["_disk_info"] = next((x for x in self.win.disks if r and x["path"] == r[1]), None)
            why = self.manual_why_not()
            if r and e and not why:
                self.layout_preview.setText(tr("<b>Будет отформатирован:</b> &nbsp;{0} ({1}). Остальные разделы не "
                                               "трогаются, загрузчик FurrOS ляжет в раздел EFI {2}").format(
                    r[0], self.plan["filesystem"], e[0]))
            else:
                self.layout_preview.setText("")
            self.mode_note.setText(why)
            self.mode_note.setVisible(bool(why))
            self.changed.emit()
            return
        d = self.plan.get("_disk_info")
        sh = self.shrink_plan(d)
        self.shrink_box.setVisible(bool(sh))
        free = d.get("free", 0) if d else 0
        if sh:
            room = shrink_room(sh) // 1024 ** 3
            if self.shrink_for != sh["path"]:
                # new partition: set the range once, start at 40 GB (or all there is)
                self.shrink_for = sh["path"]
                self.shrink_gb.blockSignals(True)
                self.shrink_gb.setRange(FURROS_MIN // 1024 ** 3, room)
                self.shrink_gb.setValue(min(40, room))
                self.shrink_gb.blockSignals(False)
            give = self.shrink_gb.value() * 1024 ** 3
            name = f"{sh['label'] or tr('Windows')} ({sh['path']}, {human(sh['size'])})"
            self.shrink_text.setText(tr("<b>На диске нет свободного места, но его можно взять у Windows.</b> "
                                        "FurrOS уменьшит раздел {0}: занято примерно {1}, можно отдать до {2} ГБ.")
                                     .format(name, human(sh["min"]), room))
            self.shrink_left.setText(tr("у Windows останется {0}").format(human(sh["size"] - give)))
            self.plan["shrink"] = {"part": sh["path"], "bytes": give}
            free = give
        else:
            self.shrink_for = None
            self.plan.pop("shrink", None)
        fs_note = f"{self.plan['filesystem']}{tr(', шифрование') if enc else ''}"
        if d and self.mode() == "alongside" and self.plan["filesystem"] == "btrfs" and not enc:
            # /boot lives inside the Btrfs root (snapshots carry their kernel): one partition only
            root = f"FurrOS {human(free)} ({fs_note})"
            self.layout_preview.setText(tr(
                "<b>Будет создано в свободном месте {0}:</b> &nbsp;{1}. "
                "Windows останется как есть, загрузчик FurrOS ляжет рядом с ней в раздел EFI").format(d['path'], root))
        elif d and self.mode() == "alongside":
            root = f"FurrOS {human(free - 1024 ** 3)} ({fs_note})"
            self.layout_preview.setText(tr(
                "<b>Будет создано в свободном месте {0}:</b> &nbsp;/boot 1 ГБ &nbsp;+&nbsp; {1}. "
                "Windows останется как есть, загрузчик FurrOS ляжет рядом с ней в раздел EFI").format(d['path'], root))
        elif d:
            boot = tr("EFI 1 ГБ (FAT32)") if self.plan.get("_uefi", True) else tr("BIOS boot 1 МБ")
            root = f"FurrOS {human(d['size'] - 1024 ** 3)} ({fs_note})"
            self.layout_preview.setText(tr('<b>Будет создано на {0}:</b> &nbsp;{1} &nbsp;+&nbsp; {2}').format(d['path'], boot, root))
        else:
            self.layout_preview.setText("")
        reasons = []
        if not d:
            for _c, disk, _f in self.cards:
                why = self.why_not(disk)
                if why and why not in reasons:
                    reasons.append(why)
        self.mode_note.setText("<b>" + tr("Нет подходящего диска для этого режима") + "</b><br>" + "<br>".join(reasons)
                               if reasons else "")
        self.mode_note.setVisible(bool(reasons))
        self.changed.emit()

    def manual_why_not(self):
        if not self.plan.get("_uefi", True):
            return tr("Установка на свои разделы работает только в режиме UEFI")
        if not self.root_combo.count():
            return tr("Нет раздела от 20 ГБ: создай его в менеджере разделов и нажми «Обновить список»")
        if not self.esp_combo.count():
            return tr("Нет раздела EFI: создай раздел FAT32 с типом «EFI System» (от 300 МБ) или выбери другой режим")
        return ""

    def valid(self):
        if self.mode() == "manual":
            return bool(self.plan.get("root_part") and self.plan.get("esp")) and not self.manual_why_not()
        d = self.plan.get("_disk_info")
        return bool(self.plan.get("disk")) and d is not None and not self.why_not(d) and not self.enc_err.text()


class DesktopPage(Page):
    title = "Выбери рабочий стол"
    subtitle = "Это то, как будет выглядеть и ощущаться система. Все варианты оформлены в стиле FurrOS"
    step_name = "Оболочка"
    mood = "wave"
    tip = "Если сомневаешься, бери KDE Plasma: она самая дружелюбная. Хочешь что-то экзотическое? Hyprland с анимациями просто огонь 🔥"

    def __init__(self, win):
        super().__init__(win)
        self.cards = []
        groups = [
            (tr("Рабочие столы"), tr("Привычная работа мышкой: панели, меню, значки"),
             [d for d in catalog.DESKTOPS if d["id"] not in catalog.TILING and d["dm"]]),
            (tr("Плиточные менеджеры окон"), tr("Окна сами раскладываются по экрану, управление в основном с клавиатуры. FurrOS ставит готовые конфиги с панелью и подсказкой по клавишам"),
             [d for d in catalog.DESKTOPS if d["id"] in catalog.TILING]),
            (tr("Без графики"), "", [d for d in catalog.DESKTOPS if not d["dm"]]),
        ]
        for gtitle, gsub, items in groups:
            self.body.addWidget(label(gtitle, "h2"))
            if gsub:
                self.body.addWidget(label(gsub, "dim"))
            grid = QGridLayout()
            grid.setSpacing(18)
            self.body.addLayout(grid)
            for i, de in enumerate(items):
                self._card(grid, i, de)
        self.warn = label("", "err")
        self.body.insertWidget(0, self.warn)
        self.pick("kde")

    def _card(self, grid, i, de):
        if True:
            card = Card()
            v = QVBoxLayout(card)
            v.setContentsMargins(12, 12, 12, 12)
            img = QLabel()
            img.setPixmap(pix(SHARE / "previews" / f"{de['id']}.png", w=226))
            img.setAlignment(Qt.AlignCenter)
            v.addWidget(img)
            top = QHBoxLayout()
            top.addWidget(label(f"<b style='font-size:17px'>{tr(de['name'])}</b>", wrap=False))
            top.addStretch()
            chip = label(tr(de["tag"]), "chipCyan" if de["id"] == "kde" else "chip", wrap=False)
            top.addWidget(chip)
            v.addLayout(top)
            v.addWidget(label(tr(de["blurb"]), "dim"))
            v.addStretch()
            v.addWidget(label(tr("<span style='color:#FF8CBE'>●</span> {0} &nbsp;&nbsp; <span style='color:#7FF0F0'>●</span> ~{1} МБ памяти").format(tr(de['level']), de['ram'])))
            card.setAccessibleName(de["name"])
            card.setToolTip(tr(de["blurb"]))
            card.clicked.connect(lambda de=de: self.pick(de["id"]))
            self.cards.append((card, de))
            grid.addWidget(card, i // 3, i % 3)

    def pick(self, did):
        self.plan["desktop"] = did
        for c, de in self.cards:
            c.setSelected(de["id"] == did)
        de = catalog.desktop(did)
        ram = self.plan.get("_ram", 8 * 1024 ** 3)
        msgs = []
        if de["ram"] * 1024 ** 2 * 3 > ram:
            msgs.append(tr('У тебя {0} памяти. {1} может подтормаживать. Попробуй Xfce или LXQt').format(human(ram), de['name']))
        if VIRT and did in ("hyprland", "niri", "sway", "cosmic"):
            msgs.append(tr("Похоже, это виртуальная машина. {0} нужна 3D-графика: включи 3D-ускорение в настройках VM "
                           "(VirtualBox: Дисплей → Включить 3D-ускорение), иначе вход в систему не сработает.").format(de['name']))
        self.warn.setText("<br>".join(msgs))
        self.changed.emit()


class AppsPage(Page):
    title = "Какие программы поставить?"
    subtitle = "Отметь всё, что пригодится. Потом можно доставить что угодно через терминал или магазин"
    step_name = "Программы"
    mood = "hoodie"
    tip = "Всё это можно поставить и потом командой sudo pacman -S. В «Школе Лапы» есть целый урок про это!"

    def __init__(self, win):
        super().__init__(win)
        self.body.addWidget(label(tr("Браузер"), "h2"))
        brow = QHBoxLayout()
        self.browser = QButtonGroup(self)
        for b in [b for b in catalog.APP_BUNDLES if b.get("group") == "browser"]:
            r = QRadioButton(tr(b["name"]))
            r.setToolTip(tr(b["blurb"]))
            r.setProperty("bid", b["id"])
            r.setChecked(b["default"])
            self.browser.addButton(r)
            brow.addWidget(r)
        brow.addStretch()
        self.browser.buttonToggled.connect(self.sync)
        self.body.addLayout(brow)

        self.body.addWidget(label(tr("Наборы"), "h2"))
        grid = QGridLayout()
        grid.setSpacing(14)
        self.checks = []
        for i, b in enumerate([b for b in catalog.APP_BUNDLES if not b.get("group")]):
            card = Card()
            v = QVBoxLayout(card)
            v.setContentsMargins(14, 10, 14, 12)
            cb = QCheckBox(tr(b["name"]))
            cb.setStyleSheet("font-weight: 800;")
            cb.setChecked(b["default"])
            cb.toggled.connect(self.sync)
            v.addWidget(cb)
            v.addWidget(label(tr(b["blurb"]), "dim"))
            card.clicked.connect(cb.toggle)
            card.setFocusPolicy(Qt.NoFocus)
            self.checks.append((cb, b, card))
            grid.addWidget(card, i // 3, i % 3)
        self.body.addLayout(grid)

        self.body.addWidget(label(tr("Ядро"), "h2"))
        krow = QHBoxLayout()
        self.kernel = QButtonGroup(self)
        for k in catalog.KERNELS:
            r = QRadioButton(tr(k["name"]))
            r.setToolTip(tr(k["blurb"]))
            r.setProperty("kid", k["id"])
            r.setChecked(k["default"])
            self.kernel.addButton(r)
            krow.addWidget(r)
        krow.addStretch()
        self.kernel.buttonToggled.connect(self.sync)
        self.body.addLayout(krow)
        self.kernel_note = label("", "dim")
        self.body.addWidget(self.kernel_note)

        self.note = label("", "dim")
        self.body.addWidget(self.note)
        self.body.addStretch()
        self.sync()

    def enter(self):
        btrfs = self.plan.get("filesystem") == "btrfs"
        for cb, b, card in self.checks:
            if b.get("needs_btrfs"):
                cb.setEnabled(btrfs)
                if not btrfs:
                    cb.setChecked(False)
                card.setToolTip("" if btrfs else tr("Доступно только с файловой системой Btrfs (шаг «Диск»)"))
        self.sync()

    def sync(self, *_):
        apps = [cb_b["id"] for cb_b in [b for cb, b, _ in self.checks if cb.isChecked()]]
        r = self.browser.checkedButton()
        if r:
            apps.append(r.property("bid"))
        self.plan["apps"] = apps
        k = self.kernel.checkedButton() if hasattr(self, "kernel") else None
        self.plan["kernel"] = k.property("kid") if k else "linux"
        if hasattr(self, "kernel_note"):
            kk = next(x for x in catalog.KERNELS if x["id"] == self.plan["kernel"])
            self.kernel_note.setText(tr(kk["blurb"]))
        for cb, b, card in self.checks:
            card.setSelected(cb.isChecked())
        plan = dict(self.plan)
        n = len(set(catalog.BASE_PACKAGES + catalog.desktop(plan.get("desktop", "kde"))["packages"] +
                    [p for b in catalog.APP_BUNDLES if b["id"] in apps for p in b["packages"]]))
        self.note.setText(tr('Будет установлено примерно {0} пакетов (и их зависимости)').format(n))
        self.changed.emit()


class LookPage(Page):
    title = "Обои и мелочи"
    subtitle = "Выбери обои. Их можно поменять в любой момент"
    step_name = "Оформление"
    mood = "wave"
    tip = "Обои с моими портретами самые лучшие, я проверяла 😌 А анимированные двигаются прямо на рабочем столе!"

    def __init__(self, win):
        super().__init__(win)
        self.cards = []
        self.body.addWidget(label(tr("Обои FurrOS"), "h2"))
        self.body.addLayout(self._grid([(f, n, None, False) for f, n in catalog.WALLPAPERS]))
        self.body.addWidget(label(tr("Анимированные обои") + " ▶", "h2"))
        self.anim_note = label("", "dim")
        self.body.addWidget(self.anim_note)
        self.body.addLayout(self._grid([(f"{stem}.png", n, f"{stem}.mp4", flash)
                                        for stem, n, flash in catalog.ANIMATED]))
        self.body.addWidget(label(tr("Дополнительно"), "h2"))
        self.academy = QCheckBox(tr("Открыть «Школу Лапы» при первом входе"))
        self.academy.setChecked(True)
        self.fetch = QCheckBox(tr("Показывать логотип и сведения о системе (fastfetch) в терминале"))
        self.fetch.setChecked(True)
        for w in (self.academy, self.fetch):
            w.toggled.connect(self.sync)
            self.body.addWidget(w)
        self.body.addStretch()
        self.pick("furros-lapa-wave.png", None)

    def _grid(self, items):
        grid = QGridLayout()
        grid.setSpacing(14)
        for i, (fname, name, video, flash) in enumerate(items):
            card = Card()
            v = QVBoxLayout(card)
            v.setContentsMargins(8, 8, 8, 8)
            img = QLabel()
            img.setPixmap(pix(SHARE / "thumbs" / fname, w=170))
            img.setAlignment(Qt.AlignCenter)
            v.addWidget(img)
            title = f"<b>{tr(name)}</b>"
            if video:
                title = "<span style='color:#7FF0F0'>▶</span> " + title
            v.addWidget(label(title))
            if flash:
                v.addWidget(label("⚡ " + tr("Есть мигающие цвета"), "err"))
            card.setAccessibleName(tr(name))
            card.clicked.connect(lambda f=fname, vid=video: self.pick(f, vid))
            self.cards.append((card, fname))
            grid.addWidget(card, i // 4, i % 4)
        return grid

    def enter(self):
        de = catalog.desktop(self.plan.get("desktop", "kde"))
        if de["id"] in catalog.VIDEO_DESKTOPS:
            note = tr("В {0} они будут двигаться прямо на рабочем столе. Звука нет.").format(de["name"])
            if VIRT:
                note += " " + tr("В виртуальной машине без 3D-ускорения видео рисует процессор: если всё тормозит, "
                                 "выбери обычные обои (их можно сменить потом в приложении «Обои FurrOS»).")
            self.anim_note.setText(note)
        else:
            self.anim_note.setText(tr("В {0} видео-обои не поддерживаются, поэтому будет красивый кадр из ролика. "
                                      "Двигаться они умеют в KDE Plasma, Hyprland, Sway, Niri, i3, bspwm, Awesome и Qtile.").format(tr(de["name"])))

    def pick(self, fname, video):
        self.plan["wallpaper"] = fname
        self.plan["wallpaper_video"] = video
        for c, f in self.cards:
            c.setSelected(f == fname)
        self.sync()

    def sync(self, *_):
        self.plan["academy"] = self.academy.isChecked()
        self.plan["fastfetch"] = self.fetch.isChecked()
        self.changed.emit()


class UserPage(Page):
    title = "Кто ты?"
    subtitle = "Создадим твой аккаунт"
    step_name = "Аккаунт"
    mood = "hoodie"
    tip = "Пароль понадобится для входа и для команд с sudo. Придумай такой, который не забудешь, но который не угадает соседский кот."

    def __init__(self, win):
        super().__init__(win)
        self._auto_user = True
        self._errs = {"init": 1}
        g = QGridLayout()
        g.setHorizontalSpacing(24)
        g.setVerticalSpacing(6)
        self.fields = {}

        def field(row, col, key, title, placeholder, echo=False, helptext=""):
            g.addWidget(label(f"<b>{title}</b>"), row, col)
            e = QLineEdit()
            e.setPlaceholderText(placeholder)
            e.setAccessibleName(title)
            if echo:
                e.setEchoMode(QLineEdit.Password)
            e.textChanged.connect(self.sync)
            g.addWidget(e, row + 1, col)
            err = label(helptext, "dim")
            g.addWidget(err, row + 2, col)
            self.fields[key] = (e, err, helptext)
            return e

        field(0, 0, "fullname", tr("Как тебя зовут?"), tr("Например: Виталик"))
        field(0, 1, "username", tr("Имя пользователя"), tr("латиницей, например vitalik"),
              helptext=tr("Маленькие латинские буквы, цифры, - и _"))
        field(3, 0, "password", tr("Пароль"), tr("Придумай пароль"), echo=True)
        field(3, 1, "password2", tr("Пароль ещё раз"), tr("Повтори пароль"), echo=True)
        self.meter = QProgressBar()
        self.meter.setRange(0, 4)
        self.meter.setTextVisible(False)
        self.meter.setFixedHeight(14)
        g.addWidget(self.meter, 6, 0)
        field(7, 0, "hostname", tr("Имя компьютера"), "furros", helptext=tr("Так компьютер будет виден в сети"))
        self.fields["hostname"][0].setText("furros")
        self.body.addLayout(g)
        self.show_pw = QCheckBox(tr("Показать пароли"))
        self.show_pw.toggled.connect(lambda on: [self.fields[k][0].setEchoMode(
            QLineEdit.Normal if on else QLineEdit.Password) for k in ("password", "password2")])
        self.body.addWidget(self.show_pw)
        self.autologin = QCheckBox(tr("Входить автоматически, без пароля на экране входа"))
        self.autologin.toggled.connect(self.sync)
        self.body.addWidget(self.autologin)
        self.same_root = QCheckBox(tr("Дать администратору (root) тот же пароль. Если выключить, root будет заблокирован, а всё делается через sudo"))
        self.same_root.setChecked(True)
        self.same_root.toggled.connect(self.sync)
        self.body.addWidget(self.same_root)
        self.body.addStretch()
        self._auto_user = True
        self.fields["username"][0].textEdited.connect(lambda _: setattr(self, "_auto_user", False))
        self.sync()

    def enter(self):
        # COSMIC has its own login screen (cosmic-greeter) and the installer can't set up autologin there:
        # don't offer a checkbox that would silently do nothing
        cosmic = self.plan.get("desktop") == "cosmic"
        if cosmic:
            self.autologin.setChecked(False)
        self.autologin.setEnabled(not cosmic)
        self.autologin.setToolTip(tr("В COSMIC автоматический вход пока не поддерживается") if cosmic else "")

    def sync(self, *_):
        if not hasattr(self, "autologin"):
            return
        f = {k: v[0].text() for k, v in self.fields.items()}
        if self._auto_user and self.sender() is self.fields["fullname"][0]:
            self.fields["username"][0].setText(make_username(f["fullname"]))
            f["username"] = self.fields["username"][0].text()
        errs = {}
        if f["username"] and (not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", f["username"]) or f["username"] in RESERVED):
            errs["username"] = tr("Так нельзя: только a-z, 0-9, - и _, начинаться с буквы, не системное имя")
        if f["password"] and len(f["password"]) < 4:
            errs["password"] = tr("Слишком короткий: минимум 4 символа")
        if f["password2"] and f["password"] != f["password2"]:
            errs["password2"] = tr("Пароли не совпадают")
        if f["hostname"] and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,62}", f["hostname"]):
            errs["hostname"] = tr("Только латиница, цифры и дефис")
        score, word = password_score(f["password"])
        self.meter.setValue(score)
        col = [C["danger"], C["danger"], C["warn"], C["ok"], C["primary"]][score]
        self.meter.setStyleSheet(f"QProgressBar::chunk {{ background: {col}; border-radius: 4px; }}"
                                 f"QProgressBar {{ border-radius: 7px; border: 2px solid {C['ink']}; }}")
        if f["password"] and "password" not in errs:
            errs.setdefault("password_ok", word)
        for k, (e, err, helptext) in self.fields.items():
            if k in errs:
                err.setObjectName("err")
                err.setText("⚠ " + errs[k])
                set_prop(e, "bad", "true")
            else:
                err.setObjectName("dim")
                err.setText(tr('Надёжность: {0}').format(errs['password_ok']) if k == "password" and "password_ok" in errs else helptext)
                set_prop(e, "bad", "false")
            err.style().unpolish(err)
            err.style().polish(err)
        self._errs = {k: v for k, v in errs.items() if k != "password_ok"}
        self.plan.update(fullname=f["fullname"] or f["username"], username=f["username"], password=f["password"],
                         hostname=f["hostname"] or "furros", autologin=self.autologin.isChecked(),
                         lock_root=not self.same_root.isChecked())
        self.changed.emit()

    def valid(self):
        f = {k: v[0].text() for k, v in self.fields.items()}
        return (not getattr(self, "_errs", {"x": 1}) and f["username"] and f["password"]
                and f["password"] == f["password2"])


def boot_menu_text(p):
    """Which boot menu this install gets (backend.bootloader / backend.furrboot decide the same way)."""
    if LINUX and not Path("/sys/firmware/efi").exists():
        return tr("Limine с темой FurrOS (компьютер без UEFI)")
    if p.get("mode") == "alongside" and not (p.get("filesystem") == "btrfs" and not p.get("encrypt")):
        return tr("GRUB с темой FurrOS, в нём есть Windows")
    if p.get("mode") == "manual" and p.get("filesystem") != "btrfs":
        return tr("GRUB с темой FurrOS, в нём есть другие системы")
    return tr("FurrBoot — меню FurrOS с мышью и снимками системы (запасной: GRUB)")


class SummaryPage(Page):
    title = "Всё проверим?"
    subtitle = "Последний шанс что-то поменять"
    step_name = "Итог"
    mood = "grr"
    tip = "Посмотри внимательно, особенно на диск. После нажатия «Установить» назад дороги нет!"

    def __init__(self, win):
        super().__init__(win)
        self.box = QVBoxLayout()
        self.box.setSpacing(10)
        self.body.addLayout(self.box)
        self.danger = QFrame()
        self.danger.setObjectName("danger")
        dl = QVBoxLayout(self.danger)
        self.danger_text = label("")
        dl.addWidget(self.danger_text)
        self.confirm = QCheckBox(tr("Я понимаю, что все данные на этом диске будут удалены"))
        self.confirm.toggled.connect(lambda _=None: self.changed.emit())
        dl.addWidget(self.confirm)
        self.body.addWidget(self.danger)
        self.body.addStretch()

    def enter(self):
        while self.box.count():
            it = self.box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        p = self.plan
        de = catalog.desktop(p["desktop"])
        loc = dict(catalog.LOCALES).get(p["locale"], p["locale"])
        apps = [tr(b["name"]) for b in catalog.APP_BUNDLES if b["id"] in p.get("apps", [])]
        anim = {f"{st}.png": n for st, n, _ in catalog.ANIMATED}
        wp = tr(dict(catalog.WALLPAPERS).get(p.get("wallpaper")) or anim.get(p.get("wallpaper"), p.get("wallpaper")))
        if p.get("wallpaper_video"):
            wp = "▶ " + wp + " (" + tr("анимированные") + ")"
        swap = {"zram": "zram", "file": tr("файл 4 ГБ"), "none": tr("нет")}[p["swap"]]
        rows = [
            (tr("Язык и регион"), tr('{0}, {1}, раскладки: {2}').format(loc, p['timezone'], ', '.join(p['layouts'])), 3),
            (tr("Диск"), (tr('<b>Рядом с Windows</b>, в свободных {0} · ').format(human(p['_disk_info'].get('free', 0)))
                         if p.get('mode') == 'alongside' else
                         tr('<b>Свои разделы</b>: FurrOS на {0}, EFI {1} · ').format(p.get('root_part', ''), p.get('esp', ''))
                         if p.get('mode') == 'manual' else '') +
             tr('{0} ({1}), {2}, подкачка: {3}{4}').format(p['disk'], human(p['_disk_info']['size']), p['filesystem'], swap, tr(', <b>шифрование</b>') if p.get('encrypt') else ''), 4),
            (tr("Рабочий стол"), tr(de["name"]), 5),
            (tr("Программы"), (", ".join(apps) or tr("ничего лишнего")) + " · " + tr("Ядро: {0}").format(
                tr(next((k["name"] for k in catalog.KERNELS if k["id"] == p.get("kernel", "linux")), "Обычное"))), 6),
            (tr("Загрузчик"), boot_menu_text(p), 4),
            (tr("Обои"), wp, 7),
            (tr("Аккаунт"), tr('{0} ({1}) на компьютере «{2}»{3}').format(p['fullname'], p['username'], p['hostname'], tr(', автовход') if p.get('autologin') else ''), 8),
        ]
        for title, value, page in rows:
            card = QFrame()
            card.setObjectName("card")
            h = QHBoxLayout(card)
            h.setContentsMargins(16, 10, 10, 10)
            t = label(f"<b>{title}</b>", wrap=False)
            t.setFixedWidth(150)
            h.addWidget(t)
            h.addWidget(label(value), 1)
            edit = button(tr("Изменить"), "link", shadow=False)
            edit.clicked.connect(lambda _=False, i=page: self.win.go(i))
            h.addWidget(edit)
            self.box.addWidget(card)
        d = p["_disk_info"]
        if p.get("mode") == "alongside" and p.get("shrink"):
            self.danger_text.setText(tr(
                "<b style='font-size:17px; color:#FF8C94'>⚠ FurrOS уменьшит раздел Windows {0} на {1} и займёт это место.</b><br>"
                "Файлы Windows останутся, но изменение разделов — это всегда риск: <b>сначала сделай копию важных файлов</b>. "
                "Ноутбук поставь на зарядку: если выключить компьютер, пока раздел сжимается, данные можно потерять. "
                "При первом запуске Windows проверит диск — дождись конца.").format(p["shrink"]["part"], human(p["shrink"]["bytes"])))
            self.confirm.setText(tr("Я сделал(а) копию важных файлов и готов(а) ставить рядом с Windows"))
        elif p.get("mode") == "manual":
            self.danger_text.setText(tr(
                "<b style='font-size:17px; color:#FF8C94'>⚠ Раздел {0} будет отформатирован, всё на нём исчезнет.</b><br>"
                "Другие разделы не трогаются, в раздел EFI {1} только добавится загрузчик FurrOS. Проверь, что выбран "
                "нужный раздел, и сделай копию важных файлов.").format(p.get("root_part", ""), p.get("esp", "")))
            self.confirm.setText(tr("Я проверил(а) раздел и готов(а) его отформатировать"))
        elif p.get("mode") == "alongside":
            self.danger_text.setText(tr(
                "<b style='font-size:17px; color:#FF8C94'>⚠ FurrOS займёт свободное место на {0} ({1}, {2}).</b><br>"
                "Разделы Windows и твои файлы не трогаются, но перед установкой рядом с другой системой "
                "всегда стоит сделать копию важных файлов и сохранить ключ восстановления BitLocker, если он есть.").format(d['model'], d['path'], human(d.get('free', 0))))
            self.confirm.setText(tr("Я сделал(а) копию важных файлов и готов(а) ставить рядом с Windows"))
        else:
            text = tr("<b style='font-size:17px; color:#FF8C94'>⚠ Диск {0} ({1}, {2}) будет полностью стёрт.</b><br>Все разделы и файлы на нём исчезнут, включая другие системы.").format(d['model'], d['path'], human(d['size']))
            if d.get("windows"):
                # "Whole disk" is the default mode: someone who wanted dual boot may simply have missed the switch
                text += tr("<br><b style='color:#FF8C94'>На этом диске установлена Windows — она тоже будет удалена.</b> "
                           "Если хочешь оставить Windows, вернись к выбору диска и выбери «Рядом с Windows».")
            self.danger_text.setText(text)
            self.confirm.setText(tr("Я понимаю, что все данные на этом диске будут удалены"))
        self.confirm.setChecked(False)

    def valid(self):
        return self.confirm.isChecked()


TIPS = [
    ("wave", "Пока я ставлю систему, загляни в «Школу Лапы»: там уроки про всё, от файлов до терминала."),
    ("hoodie", "Команда <b>treat</b> в терминале обновит всю систему. Пёсики любят вкусняшки!"),
    ("timer", "Arch Linux обновляется каждый день. Ставь обновления раз в неделю, и всё будет свежим."),
    ("hoodie", "AUR: это тысячи программ от сообщества. С yay ставятся так: <b>yay -S имя</b>"),
    ("wave", "Напиши <b>bark</b> в терминале. Просто попробуй 🐶"),
    ("grr", "Никогда не запускай в терминале команды из интернета, если не понимаешь, что они делают. Грр!"),
    ("timer", "Почти готово… Пакеты скачиваются прямо с зеркал Arch Linux, поэтому всё самое свежее."),
    ("hoodie", "Super (кнопка Windows) открывает меню приложений почти во всех оболочках FurrOS."),
]

# (picture in usr/share/furros/slides, title, text): the slideshow shown while FurrOS installs
SLIDES = [
    ("furrboot", "Твоё меню загрузки: FurrBoot",
     "При включении тебя встретит Данёк. Стрелки или мышь выбирают, Enter запускает, T меняет тему."),
    ("snapshots", "Машина времени",
     "На Btrfs перед каждым обновлением FurrOS делает снимок системы. Что-то сломалось? Выбери снимок прямо в меню загрузки."),
    ("academy", "Школа Лапы",
     "После первого входа откроется Школа Лапы: 14 глав, тесты и терминал-песочница, где ничего не сломаешь."),
    ("wallpapers", "Обои на любой вкус",
     "Статичные и живые обои с Лапой, Велвет, Мими и Даньком меняются в приложении «Обои FurrOS»."),
    ("update", "Обновления одной командой",
     "<b>furros-update</b> обновит систему, AUR и Flatpak разом, а FurrOS сама напомнит, когда пора."),
    ("keys", "Забыл клавиши?",
     "Шпаргалка по клавишам твоего рабочего стола есть в Школе Лапы, а в плиточных оболочках открывается по Super+F1."),
    ("desktops", "Захочешь другой рабочий стол?",
     "Ещё одну оболочку можно поставить потом и выбирать её на экране входа."),
    ("community", "Мы рядом",
     "Вопросы и идеи пиши в наш Discord и Telegram: ссылки на них есть в Школе Лапы."),
]


class InstallPage(Page):
    title = "Устанавливаю FurrOS"
    subtitle = "Можно расслабиться: я всё сделаю сама"
    step_name = "Установка"
    mood = "timer"
    tip = ""
    finished = Signal(bool, str)

    STEPS = [("prepare", "Подготовка и зеркала"), ("disk", "Разметка диска"), ("packages", "Установка пакетов"),
             ("branding", "Оформление FurrOS"), ("system", "Язык, время, загрузка"), ("user", "Аккаунт"),
             ("desktop", "Рабочий стол"), ("extras", "Дополнения"), ("boot", "Загрузчик"), ("finish", "Завершение")]

    def __init__(self, win):
        super().__init__(win)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setFormat("%p%")
        self.bar.setMinimumHeight(36)
        hard_shadow(self.bar)
        self.body.addWidget(self.bar)
        self.now = label(tr("Готовлюсь…"), "sub")
        self.body.addWidget(self.now)
        row = QHBoxLayout()
        steps = QFrame()
        steps.setObjectName("card")
        sl = QVBoxLayout(steps)
        self.step_labels = {}
        for sid, name in self.STEPS:
            name = tr(name)
            l = label(f"<span style='color:#5E4650'>○</span>&nbsp; {name}")
            self.step_labels[sid] = (l, name)
            sl.addWidget(l)
        row.addWidget(steps, 3)
        # the slideshow card: a screenshot, a title, two lines and dots; it fades from one slide to the next
        self.slide = QFrame()
        self.slide.setObjectName("card")
        hard_shadow(self.slide)
        outer = QVBoxLayout(self.slide)
        outer.setContentsMargins(16, 16, 16, 12)
        inner = QWidget()
        sv = QVBoxLayout(inner)
        sv.setContentsMargins(0, 0, 0, 0)
        sv.setSpacing(8)
        self.slide_img = QLabel()
        self.slide_img.setFixedSize(480, 270)
        self.slide_img.setAlignment(Qt.AlignCenter)
        self.slide_title = label("", wrap=True)
        self.slide_title.setStyleSheet(f"font-size: 19px; font-weight: 900; color: {C['text']};")
        self.slide_text = label("", "sub")
        self.slide_text.setMinimumHeight(48)
        sv.addWidget(self.slide_img, 0, Qt.AlignHCenter)
        sv.addWidget(self.slide_title)
        sv.addWidget(self.slide_text)
        outer.addWidget(inner)
        self.slide_dots = label("", wrap=False)
        self.slide_dots.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.slide_dots)
        self.fade = QGraphicsOpacityEffect(inner)
        inner.setGraphicsEffect(self.fade)
        self.fade_anim = QPropertyAnimation(self.fade, b"opacity", self)
        self.fade_anim.setDuration(450)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        row.addWidget(self.slide, 5)
        self.body.addLayout(row)
        self.log_btn = button(tr("Показать журнал"), shadow=False)
        self.log_btn.clicked.connect(self.toggle_log)
        self.body.addWidget(self.log_btn, 0, Qt.AlignLeft)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(5000)
        self.log.setMinimumHeight(220)
        self.log.setVisible(False)
        self.body.addWidget(self.log)
        self.body.addStretch()
        self.tip_i = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_tip)
        self.proc = None
        self.current = None
        self.error = ""

    def toggle_log(self):
        self.log.setVisible(not self.log.isVisible())
        self.log_btn.setText(tr("Скрыть журнал") if self.log.isVisible() else tr("Показать журнал"))

    def next_tip(self):
        i = self.tip_i % len(SLIDES)
        name, title, text = SLIDES[i]
        img = pix(SHARE / "slides" / f"{name}.png", w=480, h=270)
        if img.isNull():  # an ISO without the pictures: Lapa with a tip, like before
            mood, tip = TIPS[self.tip_i % len(TIPS)]
            img, title, text = pix(SHARE / "lapa" / f"lapa-{mood}-small.png", w=160, h=200), "", tip
        self.slide_img.setPixmap(img)
        self.slide_title.setText(tr(title))
        self.slide_text.setText(tr(text))
        self.slide_dots.setText(" ".join(
            f"<span style='color:{C['primary'] if k == i else '#5E4650'}; font-size:14px'>●</span>" for k in range(len(SLIDES))))
        self.fade_anim.stop()
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        self.tip_i += 1

    def start(self):
        self.next_tip()
        self.timer.start(9000)
        plan = {k: v for k, v in self.plan.items() if not k.startswith("_")}
        if self.plan.get("encrypt"):
            plan["_root_part"] = None
        fd, path = tempfile.mkstemp(prefix="furros-plan-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, ensure_ascii=False)
        os.chmod(path, 0o600)
        self.logf = open(LOG_PATH, "w", encoding="utf-8")
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.read)
        self.proc.finished.connect(self.done)
        backend = str(HERE / "backend.py")
        if DRY:
            self.proc.start(sys.executable, ["-u", backend, "--dry-run", path])
        else:
            self.proc.start("sudo", ["-n", "python3", "-u", backend, path])
        self._buf = ""

    def read(self):
        self._buf += bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        *lines, self._buf = self._buf.split("\n")
        for line in lines:
            self.logf.write(line + "\n")
            if line.startswith("@@P "):
                _, pct, text = line.split(" ", 2)
                self.bar.setValue(int(float(pct) * 10))
                self.now.setText(text)
            elif line.startswith("@@S "):
                self.mark(line[4:].strip())
            elif line.startswith("@@E "):
                self.error = line[4:]
                self.log.appendPlainText(tr("ОШИБКА: ") + self.error)
            else:
                self.log.appendPlainText(line)
        self.logf.flush()

    def mark(self, sid):
        if self.current:
            l, name = self.step_labels[self.current]
            l.setText(f"<span style='color:{C['ok']}'>✓</span>&nbsp; {name}")
        self.current = sid
        if sid in self.step_labels:
            l, name = self.step_labels[sid]
            l.setText(f"<span style='color:{C['primary']}'>●</span>&nbsp; <b>{name}</b>")

    def done(self, code, _status):
        self.read()
        self.timer.stop()
        self.logf.close()
        ok = code == 0 and not self.error
        if ok and self.current:
            self.mark("__end__")
        self.finished.emit(ok, self.error or tr('Процесс завершился с кодом {0}').format(code))


class FinishPage(Page):
    title = "Готово!"
    step_name = "Готово"
    mood = "wave"

    def __init__(self, win):
        super().__init__(win)
        row = QHBoxLayout()
        left = QVBoxLayout()
        self.msg = label("", "sub")
        left.addWidget(self.msg)
        self.buttons = QHBoxLayout()
        left.addLayout(self.buttons)
        left.addStretch()
        row.addLayout(left, 3)
        self.img = QLabel()
        self.img.setAlignment(Qt.AlignCenter)
        row.addWidget(self.img, 2)
        self.body.addLayout(row)

    def show_result(self, ok, err):
        while self.buttons.count():
            w = self.buttons.takeAt(0).widget()
            if w:
                w.deleteLater()
        if ok:
            self.win.header_title.setText(tr("FurrOS установлена! 🎉"))
            self.msg.setText(tr("Ура! Система готова. Вытащи установочную флешку (или диск из виртуальной машины) "
                             "и перезагрузись.<br><br>После входа тебя встретит Данёк, а потом я покажу, "
                             "где тут что, в «Школе Лапы». <b>Гав!</b>"))
            mascot = SHARE / "mascot" / "mascot-small.png"
            self.img.setPixmap(pix(mascot if mascot.exists() else SHARE / "lapa" / "lapa-wave-small.png", h=420))
            b = button(tr("Перезагрузить сейчас"), "primary")
            b.clicked.connect(lambda: subprocess.Popen(["systemctl", "reboot"]) if LINUX else QApplication.quit())
            self.buttons.addWidget(b)
            s = button(tr("Остаться в live-режиме"))
            s.clicked.connect(QApplication.quit)
            self.buttons.addWidget(s)
        else:
            self.win.header_title.setText(tr("Ой… что-то пошло не так"))
            self.msg.setText(tr("Грр. Установка остановилась с ошибкой:<br><br><b style='color:#FF8C94'>{0}</b><br><br>Полный журнал сохранён в <b>{1}</b>. Чаще всего помогает проверить интернет и попробовать снова.").format(err, LOG_PATH))
            self.img.setPixmap(pix(SHARE / "lapa" / "lapa-grr-small.png", h=420))
            b = button(tr("Попробовать снова"), "primary")
            b.clicked.connect(lambda: self.win.go(self.win.pages.index(self.win.summary)))
            self.buttons.addWidget(b)
            # one file with the log, the disks and the graphics card, saved to a USB stick or shared as a link
            r = button(tr("Отчёт об ошибке"))
            r.clicked.connect(lambda: subprocess.Popen(["furros-report-gui"], start_new_session=True) if LINUX else None)
            self.buttons.addWidget(r)
            s = button(tr("Закрыть"))
            s.clicked.connect(QApplication.quit)
            self.buttons.addWidget(s)
        self.buttons.addStretch()


# ------------------------------------------------------------------ window
class Installer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("Установка FurrOS"))
        self.setWindowIcon(QIcon(str(SHARE / "furros-logo.png")))
        self.resize(1180, 780)
        self.plan = {"locale": catalog.LANGUAGES[LANG][0], "ui_lang": LANG}
        self.disks = []

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(250)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(16, 20, 16, 16)
        logo = QLabel()
        logo.setPixmap(pix(SHARE / "furros-lockup.png", w=200))
        sv.addWidget(logo)
        sv.addSpacing(18)

        self.pages = [WelcomePage(self), TermsPage(self), ChecksPage(self), RegionPage(self), DiskPage(self),
                      DesktopPage(self), AppsPage(self), LookPage(self), UserPage(self), SummaryPage(self),
                      InstallPage(self), FinishPage(self)]
        self.summary = self.pages[9]
        self.install = self.pages[10]
        self.finish = self.pages[11]
        self.install.finished.connect(self.on_finished)

        self.step_btns = []
        for i, p in enumerate(self.pages[:-2]):
            b = QPushButton(f"{i + 1:>2}.  {tr(p.step_name)}")
            b.setObjectName("step")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, i=i: self.go(i))
            sv.addWidget(b)
            self.step_btns.append(b)
        sv.addStretch()
        sv.addWidget(label(tr("FurrOS 1.0<br>на основе Arch Linux"), "dim"))
        h.addWidget(side)

        main = QVBoxLayout()
        main.setContentsMargins(36, 26, 30, 20)
        main.setSpacing(10)
        self.header_title = label("", "h1")
        self.header_sub = label("", "sub")
        main.addWidget(self.header_title)
        main.addWidget(self.header_sub)
        self.stack = QStackedWidget()
        for p in self.pages:
            self.stack.addWidget(p)
            p.changed.connect(self.refresh_nav)
        main.addWidget(self.stack, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(14)
        self.tip_img = QLabel()
        self.tip_img.setFixedSize(84, 84)
        self.tip_img.setAlignment(Qt.AlignCenter)
        self.tip = label("", "bubble")
        self.tip.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bottom.addWidget(self.tip_img)
        bottom.addWidget(self.tip, 1)
        self.back = button(tr("Назад"))
        self.back.clicked.connect(lambda: self.go(self.index - 1))
        self.next = button(tr("Далее"), "primary")
        self.next.clicked.connect(self.forward)
        bottom.addWidget(self.back)
        bottom.addWidget(self.next)
        main.addLayout(bottom)
        h.addLayout(main, 1)

        QShortcut(QKeySequence("Alt+Right"), self, self.forward)
        QShortcut(QKeySequence("Alt+Left"), self, lambda: self.back.isEnabled() and self.go(self.index - 1))
        self.index = 0
        self.max_seen = 0
        self.go(0)

    def switch_lang(self, code):
        global LANG
        if code == LANG:
            return
        LANG = code
        new = Installer()
        new.setGeometry(self.geometry())
        new.show()
        QApplication.instance().main_window = new
        self.close()

    def go(self, i):
        if not 0 <= i < len(self.pages):
            return
        if i > self.max_seen + 0 and i > self.index + 1:
            return
        cur = self.stack.currentWidget()
        if isinstance(cur, Page):
            cur.leave()
        self.index = i
        self.max_seen = max(self.max_seen, i)
        p = self.pages[i]
        p.enter()
        self.stack.setCurrentWidget(p)
        self.header_title.setText(tr(p.title))
        self.header_sub.setText(tr(p.subtitle))
        self.header_sub.setVisible(bool(p.subtitle))
        self.tip.setText(tr(p.tip))
        self.tip.setVisible(bool(p.tip))
        self.tip_img.setVisible(bool(p.tip))
        self.tip_img.setPixmap(pix(SHARE / "lapa" / f"lapa-{p.mood}-small.png", w=84, h=84))
        self.refresh_nav()

    def refresh_nav(self):
        i = self.index
        p = self.pages[i]
        installing = p is self.install or p is self.finish
        self.back.setVisible(not installing)
        self.next.setVisible(not installing)
        self.back.setEnabled(i > 0)
        self.next.setEnabled(bool(p.valid()))
        if p is self.summary:
            self.next.setText(tr("Установить FurrOS"))
            self.next.setObjectName("danger")
        else:
            self.next.setText(tr("Поехали!") if i == 0 else tr("Далее"))
            self.next.setObjectName("primary")
        self.next.style().unpolish(self.next)
        self.next.style().polish(self.next)
        for j, b in enumerate(self.step_btns):
            set_prop(b, "state", "current" if j == i else ("done" if j < i or j <= self.max_seen else "todo"))
            b.setEnabled(not installing and j <= self.max_seen)

    def forward(self):
        p = self.pages[self.index]
        if not self.next.isVisible() or not p.valid():
            return
        if p is self.summary:
            self.go(self.index + 1)
            self.install.start()
            return
        self.go(self.index + 1)

    def on_finished(self, ok, err):
        self.go(len(self.pages) - 1)
        self.finish.show_result(ok, err)

    def closeEvent(self, e):
        if self.install.proc and self.install.proc.state() != QProcess.NotRunning:
            e.ignore()
            self.tip.setText(tr("Грр! Нельзя закрывать во время установки, иначе система не загрузится."))
            return
        super().closeEvent(e)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("furros-installer")
    app.setDesktopFileName("furros-installer")
    fonts = ROOT / "usr/share/fonts/furros"
    for f in fonts.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(f))
    app.setFont(QFont("Nunito", 11))
    app.setStyleSheet(QSS)
    global LANG
    if "--lang" in sys.argv:
        LANG = sys.argv[sys.argv.index("--lang") + 1]
    w = Installer()
    app.main_window = w
    if "--screenshot" in sys.argv:
        # dev helper: --screenshot <page> <out.png>
        i = sys.argv.index("--screenshot")
        page, outp = int(sys.argv[i + 1]), sys.argv[i + 2]
        w.disks = list_disks()  # the checks page scans in the background: the disk page must not start empty
        w.plan.setdefault("timezone", "Europe/Moscow")  # the region page fills these from a network lookup, too slow here
        w.plan.setdefault("layouts", ["us"])
        w.show()
        for k in range(page + 1):
            w.go(k)
            if k == 6 and "--check" in sys.argv:  # dev helper: tick app bundles, e.g. --check gaming
                want = sys.argv[sys.argv.index("--check") + 1].split(",")
                for cb, b, _ in w.pages[6].checks:
                    if b["id"] in want:
                        cb.setChecked(True)
            if k == 10:  # dev helper: the install page's slideshow, --slide N picks the slide
                for _ in range(int(sys.argv[sys.argv.index("--slide") + 1]) + 1 if "--slide" in sys.argv else 1):
                    w.pages[10].next_tip()
            if k == 4 and "--manual" in sys.argv:  # dev helper: show the "own partitions" mode
                disk_page = w.pages[4]
                next(b for b in disk_page.mode_group.buttons() if b.property("code") == "manual").setChecked(True)
                i = disk_page.root_combo.findText("/dev/sdb3", Qt.MatchStartsWith)
                if i >= 0:
                    disk_page.root_combo.setCurrentIndex(i)
            if k == 4 and "--alongside" in sys.argv:  # dev helper: show the dual boot variant
                disk_page = w.pages[4]
                next(b for b in disk_page.mode_group.buttons() if b.property("code") == "alongside").setChecked(True)
        QTimer.singleShot(1500, lambda: (w.grab().save(outp), app.quit()))
    else:
        avail = app.primaryScreen().availableGeometry()
        if avail.width() < w.width() + 40 or avail.height() < w.height() + 40:
            w.showMaximized()
        else:
            w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
