#!/usr/bin/env python3
"""«About FurrOS»: the system, the Pack (Стая — supporters on Boosty) and achievements.
furros-about [--tab system|pack|ach] [--screenshot out.png]

Names of the Pack come from /usr/share/furros-staya/names.txt (its own tiny package, so a new name reaches
everyone with furros-update without rebuilding the branding), one per line (lines starting with # are skipped):
only people who agreed to be listed."""
import os
import platform
import re
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QFontDatabase, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QStackedWidget, QVBoxLayout, QWidget)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import furros_achievements as ach  # noqa: E402
from furros_academy import SHARE, detect_desktop, ui_lang  # noqa: E402

STAYA = SHARE.parent / "furros-staya" / "names.txt"   # package furros-staya
LINKS = [("furros.xyz", "https://furros.xyz"), ("Discord", "https://discord.gg/ZA3GuBYKwG"),
         ("Telegram", "https://t.me/FurrOS_Linux"), ("Boosty", "https://boosty.to/furroslinux"),
         ("GitHub", "https://github.com/Vitlikxbox/FurrOS")]

T = {
    "ru": {"title": "О системе", "tabs": ("Система", "Стая", "Достижения"),
           "rows": ("Версия", "Ядро", "Рабочий стол", "Процессор", "Видеокарта", "Память", "Диск", "Загрузчик"),
           "free": "свободно {0} из {1}", "pack_head": "Стая FurrOS",
           "pack_text": "Эти люди поддерживают FurrOS на Boosty на уровне «Стая». Спасибо, что вы с нами! 🐺",
           "pack_empty": "Здесь появятся имена тех, кто поддержит FurrOS на уровне «Стая».",
           "pack_join": "Стать частью Стаи", "ach_head": "Достижения: {0} из {1}", "locked": "ещё не получено",
           "copy": "Скопировать", "copied": "Скопировано!", "close": "Закрыть"},
    "en": {"title": "About FurrOS", "tabs": ("System", "The Pack", "Achievements"),
           "rows": ("Version", "Kernel", "Desktop", "Processor", "Graphics", "Memory", "Disk", "Boot loader"),
           "free": "{0} free of {1}", "pack_head": "The FurrOS Pack",
           "pack_text": "These people support FurrOS on Boosty at the «Pack» level. Thank you for being with us! 🐺",
           "pack_empty": "Here will be the names of those who support FurrOS at the «Pack» level.",
           "pack_join": "Join the Pack", "ach_head": "Achievements: {0} of {1}", "locked": "not yet earned",
           "copy": "Copy", "copied": "Copied!", "close": "Close"},
    "pl": {"title": "O systemie", "tabs": ("System", "Stado", "Osiągnięcia"),
           "rows": ("Wersja", "Jądro", "Pulpit", "Procesor", "Grafika", "Pamięć", "Dysk", "Program rozruchowy"),
           "free": "wolne {0} z {1}", "pack_head": "Stado FurrOS",
           "pack_text": "Te osoby wspierają FurrOS na Boosty na poziomie «Stado». Dziękujemy, że jesteście z nami! 🐺",
           "pack_empty": "Tu pojawią się imiona osób, które wesprą FurrOS na poziomie «Stado».",
           "pack_join": "Dołącz do Stada", "ach_head": "Osiągnięcia: {0} z {1}", "locked": "jeszcze nie zdobyte",
           "copy": "Kopiuj", "copied": "Skopiowano!", "close": "Zamknij"},
    "es": {"title": "Acerca de FurrOS", "tabs": ("Sistema", "La Manada", "Logros"),
           "rows": ("Versión", "Kernel", "Escritorio", "Procesador", "Gráficos", "Memoria", "Disco", "Arranque"),
           "free": "{0} libres de {1}", "pack_head": "La Manada de FurrOS",
           "pack_text": "Estas personas apoyan FurrOS en Boosty con el nivel «Manada». ¡Gracias por estar con nosotros! 🐺",
           "pack_empty": "Aquí aparecerán los nombres de quienes apoyen FurrOS con el nivel «Manada».",
           "pack_join": "Únete a la Manada", "ach_head": "Logros: {0} de {1}", "locked": "aún no conseguido",
           "copy": "Copiar", "copied": "¡Copiado!", "close": "Cerrar"},
}

CSS = """
QWidget#root { background: #1E1218; }
QLabel { color: #FFECEC; font-size: 14px; }
QLabel#head { font-size: 22px; font-weight: 900; }
QLabel#key { color: #C8AAB4; font-weight: 700; }
QLabel#dim { color: #C8AAB4; }
QLabel#name { font-size: 16px; font-weight: 800; background: #2A1A22; border: 3px solid #0E080B;
  border-radius: 12px; padding: 8px 14px; }
QFrame#card { background: #2A1A22; border: 3px solid #0E080B; border-radius: 14px; }
QFrame#card[on="false"] { background: #22161C; }
QPushButton { font-size: 14px; font-weight: 800; border: 3px solid #0E080B; border-radius: 12px; padding: 7px 16px;
  background: #3A2430; color: #FFECEC; }
QPushButton:hover { background: #4A2E3C; }
QPushButton#tab[on="true"], QPushButton#primary { background: #7FF0F0; color: #0E080B; }
QPushButton#link { background: transparent; border: 0; color: #FF8CBE; padding: 2px 6px; text-decoration: underline; }
QScrollArea { border: 0; background: transparent; }
"""


UNITS = ("Б", "КБ", "МБ", "ГБ", "ТБ") if ui_lang() == "ru" else ("B", "KB", "MB", "GB", "TB")


def human(n):
    for i, unit in enumerate(UNITS):
        if n < 1024 or i == len(UNITS) - 1:
            return f"{n:.0f} {unit}" if i < 2 else f"{n:.1f} {unit}"
        n /= 1024


def os_release():
    d = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                d[k] = v.strip().strip('"')
    except OSError:
        pass
    return d


def cpu():
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return re.sub(r"\s+", " ", line.split(":", 1)[1]).strip()
    except OSError:
        pass
    return platform.processor() or "—"


def gpu():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "drivers"))
        from furros_hw import gpus
        names = [g["name"] for g in gpus()]
        return "\n".join(names) if names else "—"
    except Exception:
        return "—"


def memory():
    try:
        kb = int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1))
        return human(kb * 1024)
    except (OSError, AttributeError):
        return "—"


def bootloader():
    if Path("/sys/firmware/efi").is_dir() and shutil.which("furrboot-theme"):
        return "FurrBoot"
    if shutil.which("limine"):   # BIOS PCs (the config sits on the root-only boot partition, so ask the package)
        return "Limine"
    return "GRUB" if Path("/boot/grub/grub.cfg").exists() else "—"


def staya():
    try:
        return [x.strip() for x in STAYA.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
    except OSError:
        return []


def system_rows(t):
    r = os_release()
    du = shutil.disk_usage("/")
    de = os.environ.get("XDG_CURRENT_DESKTOP") or detect_desktop()
    session = os.environ.get("XDG_SESSION_TYPE", "")
    return list(zip(t["rows"], [
        r.get("PRETTY_NAME", "FurrOS") + (f" ({r['BUILD_ID']})" if r.get("BUILD_ID") else ""),
        platform.release(),
        de + (f" · {session}" if session else ""),
        cpu(), gpu(), memory(), t["free"].format(human(du.free), human(du.total)), bootloader()]))


class About(QWidget):
    def __init__(self, lang, tab="system"):
        super().__init__()
        self.t = t = T.get(lang, T["en"])
        self.lang = lang
        self.setObjectName("root")
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(CSS)
        self.setWindowTitle(t["title"])
        self.setWindowIcon(QIcon(str(SHARE / "furros-logo.png")))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 18)
        lay.setSpacing(14)

        top = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap(str(SHARE / "furros-lockup.png")).scaledToHeight(40, Qt.SmoothTransformation))
        top.addWidget(logo)
        top.addStretch()
        self.tabs = []
        for i, name in enumerate(t["tabs"]):
            b = QPushButton(name, objectName="tab", cursor=Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, i=i: self.show_tab(i))
            self.tabs.append(b)
            top.addWidget(b)
        lay.addLayout(top)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.system_page())
        self.stack.addWidget(self.pack_page())
        self.stack.addWidget(self.ach_page())
        lay.addWidget(self.stack, 1)

        links = QHBoxLayout()
        for name, url in LINKS:
            b = QPushButton(name, objectName="link", cursor=Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            links.addWidget(b)
        links.addStretch()
        close = QPushButton(t["close"], cursor=Qt.PointingHandCursor)
        close.clicked.connect(self.close)
        links.addWidget(close)
        lay.addLayout(links)

        self.resize(820, 600)
        self.show_tab({"pack": 1, "ach": 2}.get(tab, 0))
        ach.unlock("about")

    def show_tab(self, i):
        self.stack.setCurrentIndex(i)
        for k, b in enumerate(self.tabs):
            b.setProperty("on", "true" if k == i else "false")
            b.style().unpolish(b)
            b.style().polish(b)

    def system_page(self):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setSpacing(24)
        pic = QLabel(alignment=Qt.AlignBottom | Qt.AlignHCenter)
        pic.setPixmap(QPixmap(str(SHARE / "lapa" / "lapa-sip-small.png")).scaled(230, 330, Qt.KeepAspectRatio,
                                                                                  Qt.SmoothTransformation))
        h.addWidget(pic)
        card = QFrame(objectName="card")
        g = QGridLayout(card)
        g.setContentsMargins(20, 16, 20, 16)
        g.setHorizontalSpacing(18)
        g.setVerticalSpacing(10)
        self.rows = system_rows(self.t)
        for i, (k, v) in enumerate(self.rows):
            g.addWidget(QLabel(k, objectName="key"), i, 0, Qt.AlignTop)
            val = QLabel(v)
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            g.addWidget(val, i, 1)
        copy = QPushButton(self.t["copy"], cursor=Qt.PointingHandCursor)

        def do_copy():
            QApplication.clipboard().setText("\n".join(f"{k}: {v}" for k, v in self.rows))
            copy.setText(self.t["copied"])
            QTimer.singleShot(1500, lambda: copy.setText(self.t["copy"]))
        copy.clicked.connect(do_copy)
        g.addWidget(copy, len(self.rows), 1, Qt.AlignRight)
        h.addWidget(card, 1)
        return w

    def pack_page(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel(self.t["pack_head"], objectName="head"))
        names = staya()
        intro = QLabel(self.t["pack_text"] if names else self.t["pack_empty"], objectName="dim")
        intro.setWordWrap(True)
        v.addWidget(intro)
        box = QWidget()
        g = QGridLayout(box)
        g.setSpacing(10)
        g.setAlignment(Qt.AlignTop)
        for i, n in enumerate(names):
            g.addWidget(QLabel("🐺 " + n, objectName="name"), i // 3, i % 3)
        area = QScrollArea(widgetResizable=True)
        area.setWidget(box)
        box.setStyleSheet("background: transparent;")
        v.addWidget(area, 1)
        row = QHBoxLayout()
        pic = QLabel()
        pic.setPixmap(QPixmap(str(SHARE / "lapa" / "lapa-heart-small.png")).scaledToHeight(120, Qt.SmoothTransformation))
        row.addWidget(pic)
        row.addStretch()
        join = QPushButton(self.t["pack_join"], objectName="primary", cursor=Qt.PointingHandCursor)
        join.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://boosty.to/furroslinux")))
        row.addWidget(join, 0, Qt.AlignBottom)
        v.addLayout(row)
        return w

    def ach_page(self):
        w = QWidget()
        v = QVBoxLayout(w)
        try:
            ach.check()
        except OSError:
            pass
        got = ach.load()
        n = sum(1 for a, _, _ in ach.ACH if a in got)
        v.addWidget(QLabel(self.t["ach_head"].format(n, len(ach.ACH)), objectName="head"))
        box = QWidget()
        box.setStyleSheet("background: transparent;")
        g = QGridLayout(box)
        g.setSpacing(10)
        for i, (aid, _, _) in enumerate(ach.ACH):
            emoji, title, how = ach.text(aid, self.lang)
            on = aid in got
            card = QFrame(objectName="card")
            card.setProperty("on", "true" if on else "false")
            h = QHBoxLayout(card)
            h.setContentsMargins(12, 8, 12, 8)
            e = QLabel(emoji if on else "🔒")
            e.setStyleSheet("font-size: 26px;")
            h.addWidget(e)
            tx = QLabel(f"<b>{title}</b><br><span style='color:#C8AAB4'>{how if on else how + ' · ' + self.t['locked']}"
                        "</span>")
            tx.setWordWrap(True)
            if not on:
                tx.setStyleSheet("color: #8E7A84;")
            h.addWidget(tx, 1)
            g.addWidget(card, i // 2, i % 2)
        area = QScrollArea(widgetResizable=True)
        area.setWidget(box)
        v.addWidget(area, 1)
        return w


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("furros-about")
    app.setDesktopFileName("furros-about")
    if "Nunito" in QFontDatabase.families():
        app.setFont(QFont("Nunito", 11))
    tab = sys.argv[sys.argv.index("--tab") + 1] if "--tab" in sys.argv[:-1] else "system"
    w = About(ui_lang(), tab)
    w.show()
    if "--screenshot" in sys.argv:
        out = sys.argv[sys.argv.index("--screenshot") + 1]
        QTimer.singleShot(600, lambda: (w.grab().save(out), app.quit()))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
