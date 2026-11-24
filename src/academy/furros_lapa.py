#!/usr/bin/env python3
"""Lapa in the tray (furros-lapa): a menu with the FurrOS apps, a nudge when the disk is almost full, and
achievements as they are earned. Started at login (/etc/xdg/autostart/furros-lapa.desktop).
Update reminders stay with furros-update --notify (furros-update-check.timer), so Lapa doesn't repeat them.
Without a tray (GNOME without the AppIndicator extension) Lapa still checks and speaks through notify-send."""
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import furros_achievements as ach  # noqa: E402
from furros_academy import SHARE, terminal_cmd, ui_lang  # noqa: E402

T = {
    "ru": {"tip": "Лапа · FurrOS", "about": "О системе", "ach": "Достижения", "school": "Школа Лапы",
           "walls": "Обои FurrOS", "update": "Обновить систему", "hide": "Спрятать Лапу до следующего входа",
           "new": "Новое достижение!", "disk_t": "Гав! Диск почти полный",
           "disk": "Осталось {0} ГБ. Почисти кэш пакетов: sudo pacman -Sc — или удали лишнее из «Загрузок»."},
    "en": {"tip": "Lapa · FurrOS", "about": "About FurrOS", "ach": "Achievements", "school": "Lapa's School",
           "walls": "FurrOS Wallpapers", "update": "Update the system", "hide": "Hide Lapa until next login",
           "new": "New achievement!", "disk_t": "Woof! The disk is almost full",
           "disk": "{0} GB left. Clean the package cache: sudo pacman -Sc — or remove old stuff from Downloads."},
    "pl": {"tip": "Łapa · FurrOS", "about": "O systemie", "ach": "Osiągnięcia", "school": "Szkoła Łapy",
           "walls": "Tapety FurrOS", "update": "Zaktualizuj system", "hide": "Schowaj Łapę do następnego logowania",
           "new": "Nowe osiągnięcie!", "disk_t": "Hau! Dysk jest prawie pełny",
           "disk": "Zostało {0} GB. Wyczyść pamięć podręczną pakietów: sudo pacman -Sc — albo usuń zbędne pliki z Pobranych."},
    "es": {"tip": "Lapa · FurrOS", "about": "Acerca de FurrOS", "ach": "Logros", "school": "Escuela de Lapa",
           "walls": "Fondos de FurrOS", "update": "Actualizar el sistema", "hide": "Ocultar a Lapa hasta el próximo inicio",
           "new": "¡Nuevo logro!", "disk_t": "¡Guau! El disco está casi lleno",
           "disk": "Quedan {0} GB. Limpia la caché de paquetes: sudo pacman -Sc, o borra cosas viejas de Descargas."},
}
# the menu in FurrOS colours, like the windows (it would otherwise follow the desktop's light/dark theme)
MENU_CSS = """
QMenu { background: #1E1218; color: #FFECEC; border: 3px solid #0E080B; border-radius: 12px; padding: 6px;
  font-size: 14px; font-weight: 700; }
QMenu::item { padding: 8px 18px; border-radius: 8px; }
QMenu::item:selected { background: #FF8CBE; color: #0E080B; }
QMenu::separator { height: 2px; background: #3A2430; margin: 5px 8px; }
"""
CHECK_MS = 5 * 60 * 1000    # achievements and disk every 5 minutes
DISK_EVERY = 24 * 3600       # the disk nudge at most once a day
LOW_FREE, LOW_PART = 5 * 1024 ** 3, 0.05   # less than 5 GB free, or less than 5 % of the disk


def launch(*cmd):
    if shutil.which(cmd[0]):
        subprocess.Popen(list(cmd), start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Lapa:
    def __init__(self, app, lang):
        self.app, self.t, self.lang = app, T.get(lang, T["en"]), lang
        self.last_disk = 0
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(QIcon(str(SHARE / "lapa" / "lapa-wave-small.png")))
            self.tray.setToolTip(self.t["tip"])
            menu = QMenu()
            menu.setStyleSheet(MENU_CSS)
            for key, cmd in [("about", ["furros-about"]), ("ach", ["furros-about", "--tab", "ach"]),
                             ("school", ["furros-academy"]), ("walls", ["furros-wallpapers-app"])]:
                a = QAction(self.t[key], menu)
                a.triggered.connect(lambda _=False, c=cmd: launch(*c))
                menu.addAction(a)
            up = QAction(self.t["update"], menu)
            up.triggered.connect(lambda: terminal_cmd("furros-update"))
            menu.addAction(up)
            menu.addSeparator()
            hide = QAction(self.t["hide"], menu)
            hide.triggered.connect(app.quit)
            menu.addAction(hide)
            self.menu = menu
            self.tray.setContextMenu(menu)
            self.tray.activated.connect(
                lambda r: launch("furros-about") if r == QSystemTrayIcon.ActivationReason.Trigger else None)
            self.tray.messageClicked.connect(lambda: launch("furros-about", "--tab", "ach"))
            self.tray.show()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
        self.timer.start(CHECK_MS)
        QTimer.singleShot(20 * 1000, self.check)   # not right at login: let the desktop settle

    def say(self, title, text):
        if self.tray and self.tray.supportsMessages():
            self.tray.showMessage(title, text, QIcon(str(SHARE / "lapa" / "lapa-heart-small.png")), 8000)
        elif shutil.which("notify-send"):
            subprocess.run(["notify-send", "-a", "FurrOS", "-i", str(SHARE / "lapa" / "lapa-heart-small.png"),
                            title, text], check=False)

    def check(self):
        try:
            for aid in ach.check():
                emoji, title, how = ach.text(aid, self.lang)
                self.say(self.t["new"], f"{emoji} {title} — {how}")
        except OSError:
            pass
        du = shutil.disk_usage("/")
        if (du.free < LOW_FREE or du.free < du.total * LOW_PART) and time.time() - self.last_disk > DISK_EVERY:
            self.last_disk = time.time()
            self.say(self.t["disk_t"], self.t["disk"].format(f"{du.free / 1024 ** 3:.1f}"))


def main():
    if Path("/run/archiso").exists():   # the live USB: nothing to track there
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName("furros-lapa")
    app.setDesktopFileName("furros-lapa")
    app.setQuitOnLastWindowClosed(False)
    lapa = Lapa(app, ui_lang())  # noqa: F841  (keeps the tray icon alive)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
