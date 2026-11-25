#!/usr/bin/env python3
"""FurrOS welcome popup: a small tour with Danyok on the first login after installation (like GNOME Tour).
When it closes, Lapa's School opens.   furros-welcome [--no-school] [--screenshot out.png [page]]"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                               QPushButton, QStackedWidget, QVBoxLayout, QWidget)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from furros_academy import SHARE, ui_lang  # noqa: E402

DISCORD, TELEGRAM = "https://discord.gg/ZA3GuBYKwG", "https://t.me/FurrOS_Linux"

# (image, title, text) per page; the last page also gets the Discord / Telegram links
T = {
    "ru": {"pages": [
        ("mascot/mascot-small.png", "Добро пожаловать в FurrOS!",
         "Привет, я <b>Данёк</b>! 🐾 Система установлена и готова к работе. Давай я быстро покажу, что тут есть."),
        (None, "Всё уже настроено",
         "⟳ &nbsp;<b>Обновления</b> одной командой <code>furros-update</code>, перед ними делается снимок системы<br>"
         "⏪ &nbsp;<b>Снимки системы</b>: если что-то сломалось, откатись прямо из меню загрузки<br>"
         "🎮 &nbsp;<b>Драйверы</b> видеокарты подскажет <code>furros-drivers</code><br>"
         "🛡 &nbsp;<b>Фаервол</b> уже включён"),
        ("slides/furrboot.png", "Твоё меню загрузки: FurrBoot",
         "При включении встречает FurrBoot. Клавиша <b>T</b> меняет тему (или «Обои FurrOS» → «Меню загрузки»), а «Снимки системы» и «Другое ядро» выручат, если что-то пошло не так."),
        ("lapa/lapa-wave-small.png", "Знакомься, это Лапа",
         "Лапа научит тебя Linux: 14 глав, тесты и песочница, где ничего не сломаешь. "
         "Её школа откроется сразу после этого окна."),
    ], "back": "Назад", "next": "Далее", "done": "Открыть Школу Лапы", "skip": "Пропустить",
        "help": "Вопросы? Мы в <a style='color:#FF8CBE' href='{d}'>Discord</a> и <a style='color:#FF8CBE' href='{t}'>Telegram</a>"},
    "en": {"pages": [
        ("mascot/mascot-small.png", "Welcome to FurrOS!",
         "Hi, I'm <b>Danyok</b>! 🐾 The system is installed and ready. Let me quickly show you around."),
        (None, "Everything is already set up",
         "⟳ &nbsp;<b>Updates</b> with one command, <code>furros-update</code>, with a system snapshot first<br>"
         "⏪ &nbsp;<b>System snapshots</b>: if something breaks, roll back right from the boot menu<br>"
         "🎮 &nbsp;<b>Graphics drivers</b>: <code>furros-drivers</code> tells you what you need<br>"
         "🛡 &nbsp;<b>Firewall</b> is already on"),
        ("slides/furrboot.png", "Your boot menu: FurrBoot",
         "FurrBoot greets you when the PC starts. <b>T</b> changes its theme (or «FurrOS Wallpapers» → «Boot menu»), and «System snapshots» and «Other kernel» save the day if something goes wrong."),
        ("lapa/lapa-wave-small.png", "Meet Lapa",
         "Lapa will teach you Linux: 14 chapters, quizzes and a sandbox where you can't break anything. "
         "Her school opens right after this window."),
    ], "back": "Back", "next": "Next", "done": "Open Lapa's School", "skip": "Skip",
        "help": "Questions? We're on <a style='color:#FF8CBE' href='{d}'>Discord</a> and <a style='color:#FF8CBE' href='{t}'>Telegram</a>"},
    "pl": {"pages": [
        ("mascot/mascot-small.png", "Witaj w FurrOS!",
         "Cześć, jestem <b>Danyok</b>! 🐾 System jest zainstalowany i gotowy. Pokażę ci szybko, co tu jest."),
        (None, "Wszystko jest już ustawione",
         "⟳ &nbsp;<b>Aktualizacje</b> jednym poleceniem <code>furros-update</code>, najpierw migawka systemu<br>"
         "⏪ &nbsp;<b>Migawki systemu</b>: jeśli coś się zepsuje, wróć prosto z menu startowego<br>"
         "🎮 &nbsp;<b>Sterowniki grafiki</b> podpowie <code>furros-drivers</code><br>"
         "🛡 &nbsp;<b>Zapora</b> jest już włączona"),
        ("slides/furrboot.png", "Twoje menu startowe: FurrBoot",
         "Po włączeniu wita cię FurrBoot. Klawisz <b>T</b> zmienia motyw (albo «Tapety FurrOS» → «Menu startowe»), a «Migawki systemu» i «Inne jądro» pomogą, gdy coś pójdzie nie tak."),
        ("lapa/lapa-wave-small.png", "Poznaj Łapę",
         "Łapa nauczy cię Linuksa: 14 rozdziałów, testy i piaskownica, w której nic nie zepsujesz. "
         "Jej szkoła otworzy się zaraz po tym oknie."),
    ], "back": "Wstecz", "next": "Dalej", "done": "Otwórz Szkołę Łapy", "skip": "Pomiń",
        "help": "Pytania? Jesteśmy na <a style='color:#FF8CBE' href='{d}'>Discordzie</a> i <a style='color:#FF8CBE' href='{t}'>Telegramie</a>"},
    "es": {"pages": [
        ("mascot/mascot-small.png", "¡Bienvenido a FurrOS!",
         "¡Hola, soy <b>Danyok</b>! 🐾 El sistema está instalado y listo. Te enseño rápido lo que hay."),
        (None, "Todo está ya configurado",
         "⟳ &nbsp;<b>Actualizaciones</b> con un solo comando, <code>furros-update</code>, con una instantánea antes<br>"
         "⏪ &nbsp;<b>Instantáneas</b>: si algo se rompe, vuelve atrás desde el menú de arranque<br>"
         "🎮 &nbsp;<b>Drivers gráficos</b>: <code>furros-drivers</code> te dice cuál necesitas<br>"
         "🛡 &nbsp;El <b>cortafuegos</b> ya está activado"),
        ("slides/furrboot.png", "Tu menú de arranque: FurrBoot",
         "Al encender te recibe FurrBoot. La tecla <b>T</b> cambia el tema (o «Fondos de FurrOS» → «Menú de arranque»), y «Instantáneas» y «Otro kernel» te salvan si algo sale mal."),
        ("lapa/lapa-wave-small.png", "Conoce a Lapa",
         "Lapa te enseñará Linux: 14 capítulos, tests y un sandbox donde no puedes romper nada. "
         "Su escuela se abre justo después de esta ventana."),
    ], "back": "Atrás", "next": "Siguiente", "done": "Abrir la Escuela de Lapa", "skip": "Saltar",
        "help": "¿Preguntas? Estamos en <a style='color:#FF8CBE' href='{d}'>Discord</a> y <a style='color:#FF8CBE' href='{t}'>Telegram</a>"},
}

CSS = """
#card { background: #1E1218; border: 3px solid #0E080B; border-radius: 22px; }
QLabel { color: #FFECEC; }
#title { font-size: 26px; font-weight: 900; }
#text { font-size: 16px; color: #F2DCE2; }
#help { font-size: 14px; color: #C8AAB4; }
#dot { background: #3A2430; border-radius: 5px; }
#dot[on="true"] { background: #FF8CBE; }
QPushButton { font-size: 15px; font-weight: 800; border: 3px solid #0E080B; border-radius: 14px; padding: 8px 20px;
  background: #3A2430; color: #FFECEC; }
QPushButton:hover { background: #4A2E3C; }
QPushButton#primary { background: #7FF0F0; color: #0E080B; }
QPushButton#primary:hover { background: #A6F6F6; }
QPushButton#skip { background: transparent; border: 0; color: #C8AAB4; padding: 4px 8px; }
QPushButton#skip:hover { color: #FFECEC; }
"""


def compositing():
    """Is a compositor running? Without one (LXQt/Openbox, plain X11 WMs) a translucent window paints its
    see-through corners black, so the popup then drops the rounded-corner trick. Wayland always composites;
    on X11 the compositor owns the _NET_WM_CM_S<screen> selection (EWMH)."""
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    try:
        import ctypes
        import ctypes.util
        x = ctypes.CDLL(ctypes.util.find_library("X11") or "libX11.so.6")
        x.XOpenDisplay.argtypes, x.XOpenDisplay.restype = [ctypes.c_char_p], ctypes.c_void_p
        x.XDefaultScreen.argtypes = [ctypes.c_void_p]
        x.XInternAtom.argtypes, x.XInternAtom.restype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int], ctypes.c_ulong
        x.XGetSelectionOwner.argtypes, x.XGetSelectionOwner.restype = [ctypes.c_void_p, ctypes.c_ulong], ctypes.c_ulong
        x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        d = x.XOpenDisplay(None)
        if not d:
            return True
        owner = x.XGetSelectionOwner(d, x.XInternAtom(d, f"_NET_WM_CM_S{x.XDefaultScreen(d)}".encode(), 0))
        x.XCloseDisplay(d)
        return owner != 0
    except Exception:
        return True


class Welcome(QDialog):
    def __init__(self, lang):
        super().__init__()
        self.t = T.get(lang, T["en"])
        self.setWindowTitle(self.t["pages"][0][1])
        self.setWindowIcon(QIcon(str(SHARE / "furros-logo.png")))
        # a borderless popup with rounded corners, not an app window
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        comp = compositing()
        if comp:
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setStyleSheet(CSS)
        else:  # no compositor: a plain square card, no see-through corners or shadow margin
            self.setStyleSheet(CSS + "QDialog { background: #1E1218; } #card { border-radius: 0; }")
        self.drag = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(*(4 * [24 if comp else 0]))
        card = QFrame(objectName="card")
        if comp:
            shadow = QGraphicsDropShadowEffect(blurRadius=40, offset=QPoint(0, 10), color=QColor(0, 0, 0, 170))
            card.setGraphicsEffect(shadow)
        outer.addWidget(card)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(34, 18, 34, 24)

        top = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap(str(SHARE / "furros-lockup.png")).scaledToHeight(30, Qt.SmoothTransformation))
        top.addWidget(logo)
        top.addStretch()
        skip = QPushButton(self.t["skip"], objectName="skip", cursor=Qt.PointingHandCursor)
        skip.clicked.connect(self.accept)
        top.addWidget(skip)
        lay.addLayout(top)

        self.stack = QStackedWidget()
        # the FurrBoot page only where FurrBoot boots this PC (UEFI); old PCs get Limine (BIOS)
        furrboot = Path("/sys/firmware/efi").is_dir() and Path("/usr/bin/furrboot-theme").exists()
        self.t = dict(self.t, pages=[pg for pg in self.t["pages"] if pg[0] != "slides/furrboot.png" or furrboot
                                     or "--all" in sys.argv])
        for img, title, text in self.t["pages"]:
            self.stack.addWidget(self.page(img, title, text))
        lay.addWidget(self.stack, 1)

        self.help = QLabel(self.t["help"].format(d=DISCORD, t=TELEGRAM), objectName="help", alignment=Qt.AlignCenter)
        self.help.setOpenExternalLinks(True)
        lay.addWidget(self.help)

        bottom = QHBoxLayout()
        self.back = QPushButton(self.t["back"], cursor=Qt.PointingHandCursor)
        self.back.clicked.connect(lambda: self.go(self.stack.currentIndex() - 1))
        bottom.addWidget(self.back)
        bottom.addStretch()
        self.dots = []
        for _ in self.t["pages"]:
            d = QFrame(objectName="dot")
            d.setFixedSize(10, 10)
            self.dots.append(d)
            bottom.addWidget(d)
        bottom.addStretch()
        self.next = QPushButton(objectName="primary", cursor=Qt.PointingHandCursor)
        self.next.clicked.connect(self.forward)
        bottom.addWidget(self.next)
        lay.addLayout(bottom)

        self.resize(780, 560)
        self.go(0)

    def page(self, img, title, text):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 6, 0, 6)
        v.addStretch()
        if img:
            pic = QLabel(alignment=Qt.AlignCenter)
            pm = QPixmap(str(SHARE / img))
            pic.setPixmap(pm.scaled(520, 230, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            v.addWidget(pic)
        t = QLabel(title, objectName="title", alignment=Qt.AlignCenter)
        v.addWidget(t)
        x = QLabel(text, objectName="text", alignment=Qt.AlignLeft if not img else Qt.AlignCenter)
        x.setWordWrap(True)
        x.setTextFormat(Qt.RichText)
        if not img:
            x.setStyleSheet("font-size: 17px; line-height: 160%;")
        v.addWidget(x)
        v.addStretch()
        return w

    def go(self, i):
        n = self.stack.count()
        i = max(0, min(i, n - 1))
        self.stack.setCurrentIndex(i)
        self.back.setVisible(i > 0)
        self.help.setVisible(i == n - 1)
        self.next.setText(self.t["done"] if i == n - 1 else self.t["next"])
        for k, d in enumerate(self.dots):
            d.setProperty("on", "true" if k == i else "false")
            d.style().unpolish(d)
            d.style().polish(d)

    def forward(self):
        if self.stack.currentIndex() == self.stack.count() - 1:
            self.accept()
        else:
            self.go(self.stack.currentIndex() + 1)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Right, Qt.Key_Return, Qt.Key_Enter):
            self.forward()
        elif e.key() == Qt.Key_Left:
            self.go(self.stack.currentIndex() - 1)
        else:
            super().keyPressEvent(e)  # Esc closes, like skip

    # borderless: drag the popup by any empty spot
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag)

    def mouseReleaseEvent(self, _e):
        self.drag = None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("furros-welcome")
    app.setDesktopFileName("furros-welcome")
    if "Nunito" in QFontDatabase.families():
        app.setFont(QFont("Nunito", 11))
    w = Welcome(ui_lang())
    if "--screenshot" in sys.argv:
        i = sys.argv.index("--screenshot")
        page = int(sys.argv[i + 2]) if len(sys.argv) > i + 2 else 0
        w.go(page)
        w.show()
        QTimer.singleShot(500, lambda: (w.grab().save(sys.argv[i + 1]), app.quit()))
        return app.exec()
    w.show()
    app.exec()
    # then Lapa's School, starting from its home page
    if "--no-school" not in sys.argv and shutil.which("furros-academy"):
        subprocess.Popen(["furros-academy", "--welcome"], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
