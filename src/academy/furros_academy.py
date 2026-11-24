#!/usr/bin/env python3
"""Lapa's School (furros-academy): the FurrOS tutorial app. A Qt window around the HTML lessons."""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
WEB = HERE / "web"
LINUX = platform.system() == "Linux"
ROOT = Path(os.environ.get("FURROS_ROOT", "/" if LINUX else r"D:\FurrOS\profile\airootfs"))
SHARE = ROOT / "usr/share/furros"


def detect_desktop():
    cur = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    for key, names in [("kde", ("kde", "plasma")), ("gnome", ("gnome",)), ("cosmic", ("cosmic",)),
                       ("cinnamon", ("cinnamon", "x-cinnamon")), ("xfce", ("xfce",)), ("mate", ("mate",)),
                       ("budgie", ("budgie",)), ("lxqt", ("lxqt",)), ("deepin", ("deepin", "dde")),
                       ("hyprland", ("hyprland",)), ("niri", ("niri",)),
                       ("sway", ("sway",)), ("i3", ("i3",)), ("bspwm", ("bspwm",)), ("awesome", ("awesome",)),
                       ("qtile", ("qtile",))]:
        if any(n in cur for n in names):
            return key
    try:
        for line in Path("/etc/furros/settings.conf").read_text().splitlines():
            if line.startswith("DESKTOP="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return "kde"


def ui_lang():
    try:
        for line in Path("/etc/furros/settings.conf").read_text().splitlines():
            if line.startswith("UI_LANG="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    lang = (os.environ.get("LANG") or "ru")[:2]
    return lang if lang in ("ru", "en", "pl", "es") else "en"


def terminal_cmd(cmd):
    """Open a terminal with the command typed in but not executed (the user presses Enter)."""
    script = (f"printf '\\e[38;2;255;140;190m🐾 Лапа вставила команду. Нажми Enter, чтобы выполнить, "
              f"или Ctrl+C, чтобы отменить.\\e[0m\\n'; "
              f"read -e -i {shlex_quote(cmd)} -p '$ ' c && eval \"$c\"; exec bash")
    for term, args in [("konsole", ["-e", "bash", "-c", script]), ("kitty", ["bash", "-c", script]),
                       ("alacritty", ["-e", "bash", "-c", script]), ("foot", ["bash", "-c", script]),
                       ("gnome-console", ["--", "bash", "-c", script]), ("kgx", ["--", "bash", "-c", script]),
                       ("gnome-terminal", ["--", "bash", "-c", script]), ("xfce4-terminal", ["-x", "bash", "-c", script]),
                       ("mate-terminal", ["-x", "bash", "-c", script]), ("qterminal", ["-e", "bash", "-c", script]),
                       ("deepin-terminal", ["-e", "bash", "-c", script]), ("terminology", ["-e", "bash", "-c", script]),
                       ("cosmic-term", ["-e", "bash", "-c", script]), ("xterm", ["-e", "bash", "-c", script])]:
        if shutil.which(term):
            subprocess.Popen([term] + args)
            return True
    return False


def shlex_quote(s):
    import shlex
    return shlex.quote(s)


def build_url(mode):
    q = {"lang": ui_lang(), "de": detect_desktop(), "assets": SHARE.as_uri()}
    if mode:
        q["mode"] = mode
    return (WEB / "index.html").as_uri() + "?" + urlencode(q)


def run_browser_fallback(url):
    subprocess.Popen(["xdg-open", url] if LINUX else ["cmd", "/c", "start", "", url])


def main():
    mode = "keys" if "--keys" in sys.argv else ("welcome" if "--welcome" in sys.argv else "")
    url = build_url(mode)
    try:
        from PySide6.QtCore import QObject, QUrl, Slot, QTimer
        from PySide6.QtGui import QIcon, QGuiApplication, QDesktopServices
        from PySide6.QtWebChannel import QWebChannel
        from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWidgets import QApplication, QMainWindow
    except ImportError:
        run_browser_fallback(url)
        return 0

    class Bridge(QObject):
        @Slot(str)
        def runInTerminal(self, cmd):
            terminal_cmd(cmd)

        @Slot(str)
        def saveProgress(self, state):
            # ~/.local/share/furros/school.json: Lapa in the tray reads it for achievements
            out = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "furros" / "school.json"
            try:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(state)
            except OSError:
                pass

        @Slot(str)
        def copy(self, text):
            QGuiApplication.clipboard().setText(text)

    class Page(QWebEnginePage):
        # web links open in the normal browser: inside the school there is no back button
        def acceptNavigationRequest(self, url, nav_type, is_main_frame):
            if url.scheme() in ("http", "https", "mailto"):
                QDesktopServices.openUrl(url)
                return False
            return super().acceptNavigationRequest(url, nav_type, is_main_frame)

        def createWindow(self, _type):
            return None

    app = QApplication(sys.argv)
    app.setApplicationName("furros-academy")
    app.setDesktopFileName("furros-academy")
    data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "furros-academy"
    data.mkdir(parents=True, exist_ok=True)
    profile = QWebEngineProfile("furros-academy", app)
    profile.setPersistentStoragePath(str(data))
    s = profile.settings()
    s.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
    s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
    s.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)

    win = QMainWindow()
    win.setWindowTitle("Школа Лапы · FurrOS")
    win.setWindowIcon(QIcon(str(SHARE / "furros-logo.png")))
    win.resize(1280, 860)
    view = QWebEngineView()
    page = Page(profile, view)
    view.setPage(page)
    channel = QWebChannel(page)
    bridge = Bridge()
    channel.registerObject("furros", bridge)
    page.setWebChannel(channel)
    page.titleChanged.connect(lambda t: win.setWindowTitle(f"{t} · FurrOS"))
    view.setUrl(QUrl(url))
    win.setCentralWidget(view)
    win.show()

    if "--screenshot" in sys.argv:
        i = sys.argv.index("--screenshot")
        out, js = sys.argv[i + 1], (sys.argv[i + 2] if len(sys.argv) > i + 2 else "")

        def shot():
            view.grab().save(out)
            app.quit()

        def after_load(_ok):
            if js:
                page.runJavaScript(js)
            QTimer.singleShot(1800, shot)

        page.loadFinished.connect(after_load)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
