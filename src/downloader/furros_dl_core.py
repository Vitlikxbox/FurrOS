"""FurrOS Downloader core: find the build on GitHub Releases, download its parts (resumable), check them, join them
into the ISO, check the ISO, delete the parts, write it to a USB stick. Used by the window (furros_downloader_gui.py)
and the terminal version (furros-downloader). Only the Python standard library.

GitHub keeps every release file under 2 GiB, so the ISO is published as FurrOS-1.0-x86_64.iso.part1, .part2, ...
next to FurrOS-1.0-x86_64.iso.sha256."""
import hashlib
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

REPO = "Vitlikxbox/FurrOS"
CHUNK = 1024 * 1024
UA = "furros-downloader/1.0"


class DLError(Exception):
    """A problem to show to the person: (ru, en) texts."""

    def __init__(self, ru, en, need_token=False):
        super().__init__(en)
        self.ru, self.en = ru, en
        self.need_token = need_token  # a private repository: the window then asks for a GitHub token


def human(n, ru=True):
    units = ("Б", "КБ", "МБ", "ГБ") if ru else ("B", "KB", "MB", "GB")
    for unit in units:
        if n < 1024 or unit == units[-1]:
            return f"{n} {unit}" if unit == units[0] else f"{n:.1f} {unit}"
        n /= 1024


def _ssl_context():
    """The system's trusted roots plus Mozilla's list (certifi, bundled into the exe and the AppImage). Python on
    Windows sees only the roots Windows has already cached, and an AppImage built on Ubuntu looks for them where Ubuntu
    keeps them: either way GitHub's certificate can fail to verify ("Нет связи с GitHub", tester reports 25.11)."""
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except (ImportError, OSError, ssl.SSLError):
        pass
    return ctx


SSL_CTX = _ssl_context()


def _why(e):
    """A short reason for a network error, shown in the window so a report tells us what really happened."""
    r = getattr(e, "reason", e)
    if isinstance(r, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(r):
        return "сертификат / certificate"
    if isinstance(r, (TimeoutError, socket.timeout)) or "timed out" in str(r):
        return "таймаут / timeout"
    if isinstance(r, socket.gaierror):
        return "DNS"
    return (type(r).__name__ + (f": {r}" if str(r) else ""))[:80]


def _request(url, token=None, accept=None, start=0, timeout=60):
    headers = {"User-Agent": UA}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if accept:
        headers["Accept"] = accept
    if start:
        headers["Range"] = f"bytes={start}-"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout, context=SSL_CTX)


class Build:
    """One release: which files to download and what the ISO must hash to."""

    def __init__(self, rel, token):
        self.token = token
        self.tag = rel.get("tag_name", "")
        self.title = rel.get("name") or self.tag
        self.assets = {a["name"]: a for a in rel.get("assets", [])}
        isos = sorted(n for n in self.assets if re.fullmatch(r".+\.iso", n))
        parts = sorted((n for n in self.assets if re.fullmatch(r".+\.iso\.part\d+", n)),
                       key=lambda n: int(n.rsplit("part", 1)[1]))
        if not isos and not parts:
            raise DLError(f"В сборке {self.tag} нет ISO", f"Build {self.tag} has no ISO")
        self.iso_name = isos[0] if isos else parts[0].rsplit(".part", 1)[0]
        self.pieces = [self.iso_name] if isos else parts
        self.size = sum(self.assets[p]["size"] for p in self.pieces)
        self._sha = None

    def url(self, name):
        a = self.assets[name]
        # a private repository serves files only through the API with a token; a public one through the plain link
        return (a["url"], "application/octet-stream") if self.token else (a["browser_download_url"], None)

    def iso_sha256(self):
        if self._sha is None:
            self._sha = ""
            name = self.iso_name + ".sha256"
            if name in self.assets:
                url, acc = self.url(name)
                with _request(url, self.token, acc) as r:
                    self._sha = (r.read().decode().split() or [""])[0].lower()
        return self._sha


def find_build(repo=REPO, tag=None, token=None):
    # not releases/latest: it skips pre-releases, and test builds are pre-releases. The list shows drafts to people
    # with push access (testers are collaborators), and a draft may still be uploading, so drafts are skipped
    path = f"releases/tags/{tag}" if tag else "releases?per_page=20"
    try:
        for attempt in range(3):  # a flaky connection (or a VPN still connecting) gets two more tries
            try:
                with _request(f"https://api.github.com/repos/{repo}/{path}", token, "application/vnd.github+json",
                              timeout=30) as r:
                    data = json.load(r)
                break
            except urllib.error.HTTPError:
                raise
            except (urllib.error.URLError, OSError):
                if attempt == 2:
                    raise
                time.sleep(3)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403) and token:
            raise DLError("GitHub не принял токен: проверь, что он скопирован целиком и не истёк",
                          "GitHub didn't accept the token: check it was copied whole and hasn't expired",
                          need_token=True) from e
        if e.code == 404:
            if not token:
                # GitHub answers 404 (not 401) for a private repository without a token
                raise DLError("Сборка не найдена. Если это закрытая сборка для тестеров, нужен токен GitHub",
                              "Build not found. If it's a private test build, a GitHub token is needed",
                              need_token=True) from e
            raise DLError("Сборка не найдена. Возможно, она ещё не опубликована",
                          "Build not found. It may not be published yet") from e
        if e.code in (403, 429) and not token:
            # 60 requests an hour per IP without a token; VPN and mobile IPs are shared, so the limit runs out fast
            raise DLError("GitHub временно ограничил запросы с этого адреса (так бывает с VPN). Подожди минут 10–15 "
                          "или выключи VPN и попробуй снова",
                          "GitHub is limiting requests from this address for now (common with VPNs). Wait 10–15 "
                          "minutes or turn the VPN off and try again") from e
        raise DLError(f"GitHub ответил ошибкой {e.code}", f"GitHub answered with error {e.code}") from e
    except (urllib.error.URLError, OSError) as e:
        why = _why(e)
        raise DLError(f"Нет связи с GitHub ({why}). Проверь интернет или попробуй с VPN",
                      f"Can't reach GitHub ({why}). Check the internet or try a VPN") from e
    if tag:
        return Build(data, token)
    # the list is sorted by the tag's date, not by publication: releases whose tags point at the same commit come
    # in any order, so take the most recently published one
    ready = [rel for rel in data if not rel.get("draft") and rel.get("published_at")
             and any(re.fullmatch(r".+\.iso(\.part\d+)?", a["name"]) for a in rel.get("assets", []))]
    if ready:
        return Build(max(ready, key=lambda rel: rel["published_at"]), token)
    raise DLError("Сборка не найдена. Возможно, она ещё не опубликована", "Build not found. It may not be published yet")


def sha256_file(path, progress=None):
    h, done, size = hashlib.sha256(), 0, os.path.getsize(path)
    with open(path, "rb") as f:
        while block := f.read(CHUNK * 8):
            h.update(block)
            done += len(block)
            if progress:
                progress(done, size)
    return h.hexdigest()


class Job:
    """The whole download. progress(stage, done, total, speed) and note(ru, en) are called from the worker thread;
    stop() can be called from anywhere — the parts already downloaded are kept and continue next time."""

    def __init__(self, build, folder, progress=lambda *a: None, note=lambda ru, en: None, keep_parts=False):
        self.b, self.dir, self.progress, self.note, self.keep = build, folder, progress, note, keep_parts
        self.iso = os.path.join(folder, build.iso_name)
        self._stop = False

    def stop(self):
        self._stop = True

    def _check_stop(self):
        if self._stop:
            raise DLError("Остановлено. Запусти ещё раз — скачивание продолжится с того же места",
                          "Stopped. Start again — the download resumes from the same point")

    def run(self):
        b = self.b
        os.makedirs(self.dir, exist_ok=True)
        want = b.iso_sha256()
        if os.path.exists(self.iso) and want and os.path.getsize(self.iso) == b.size:
            self.note("ISO уже скачан, проверяю…", "The ISO is already here, checking…")
            if sha256_file(self.iso, lambda d, t: self.progress("check", d, t, 0)) == want:
                return self.iso
        need = b.size * (2 if len(b.pieces) > 1 else 1) - sum(
            os.path.getsize(p) for p in (os.path.join(self.dir, x) for x in b.pieces) if os.path.exists(p))
        if shutil.disk_usage(self.dir).free < need:
            raise DLError(f"Мало места: нужно ещё {human(need)}", f"Not enough space: {human(need, False)} more needed")
        done_before = 0
        for name in b.pieces:
            dest = os.path.join(self.dir, name)
            self._download(name, dest, done_before)
            digest = (b.assets[name].get("digest") or "").removeprefix("sha256:")
            if digest:
                self.note(f"Проверяю {name}…", f"Checking {name}…")
                if sha256_file(dest, lambda d, t: self.progress("check", d, t, 0)) != digest:
                    os.remove(dest)
                    raise DLError(f"{name} скачан с ошибкой и удалён. Запусти ещё раз",
                                  f"{name} was damaged and is deleted. Start again")
            done_before += b.assets[name]["size"]
        if len(b.pieces) > 1:
            self._join()
        if want:
            self.note("Проверяю готовый ISO…", "Checking the finished ISO…")
            if sha256_file(self.iso, lambda d, t: self.progress("check", d, t, 0)) != want:
                raise DLError("Хэш ISO не совпал. Удали файлы и скачай заново",
                              "The ISO hash doesn't match. Delete the files and download again")
        if len(b.pieces) > 1 and not self.keep:
            for name in b.pieces:
                os.remove(os.path.join(self.dir, name))
        return self.iso

    def _download(self, name, dest, done_before):
        b = self.b
        total = b.assets[name]["size"]
        url, accept = b.url(name)
        for attempt in range(1, 21):
            self._check_stop()
            have = os.path.getsize(dest) if os.path.exists(dest) else 0
            if have == total:
                self.progress("download", done_before + total, b.size, 0)
                return
            if have > total:
                os.remove(dest)
                have = 0
            try:
                with _request(url, b.token, accept, start=have) as r, open(dest, "ab" if have else "wb") as f:
                    if have and r.status != 206:  # the server ignored the range: start this part over
                        f.truncate(0)
                        have = 0
                    t0, got, last = time.monotonic(), 0, 0.0
                    while block := r.read(CHUNK):
                        f.write(block)
                        got += len(block)
                        now = time.monotonic()
                        if now - last > 0.2:
                            last = now
                            self.progress("download", done_before + have + got, b.size, got / max(now - t0, 0.001))
                        self._check_stop()
            except DLError:
                raise
            except (urllib.error.URLError, OSError, TimeoutError):
                self.note(f"Связь оборвалась, продолжаю с того же места ({attempt}/20)…",
                          f"Connection dropped, resuming from the same point ({attempt}/20)…")
                for _ in range(min(5 * attempt, 30) * 10):
                    self._check_stop()
                    time.sleep(0.1)
        if os.path.getsize(dest) != total:
            raise DLError(f"Не удалось скачать {name}. Запусти ещё раз — продолжу с того же места",
                          f"Could not download {name}. Start again — it resumes from the same point")

    def _join(self):
        self.note("Склеиваю части в один ISO…", "Joining the parts into one ISO…")
        done, tmp = 0, self.iso + ".tmp"
        with open(tmp, "wb") as out:
            for name in self.b.pieces:
                with open(os.path.join(self.dir, name), "rb") as f:
                    while block := f.read(CHUNK * 8):
                        out.write(block)
                        done += len(block)
                        self.progress("join", done, self.b.size, 0)
        os.replace(tmp, self.iso)


def usb_disks():
    """USB disks only (Linux). Internal disks are never offered."""
    if not sys.platform.startswith("linux"):
        return []
    out = subprocess.run(["lsblk", "-J", "-b", "-d", "-o", "PATH,SIZE,MODEL,TRAN,TYPE"],
                         capture_output=True, text=True).stdout
    disks = json.loads(out or '{"blockdevices": []}')["blockdevices"]
    return [d for d in disks if d.get("type") == "disk" and d.get("tran") == "usb"]


def write_usb(iso, disk, progress=lambda *a: None, root_cmd=("sudo",)):
    """Unmount the stick, write the ISO, flush, read it back and compare. root_cmd: sudo (terminal) or pkexec (window)."""
    size = os.path.getsize(iso)
    if int(disk["size"]) < size:
        raise DLError("Флешка меньше образа", "The stick is smaller than the image")
    want = sha256_file(iso, lambda d, t: progress("check", d, t, 0))
    path = disk["path"]
    script = (f"for p in $(lsblk -lnpo PATH '{path}' | tail -n +2); do umount \"$p\" 2>/dev/null; done; "
              f"dd if='{iso}' of='{path}' bs=4M conv=fsync oflag=direct status=progress 2>&1 && sync && "
              f"echo SUM $(head -c {size} '{path}' | sha256sum)")
    p = subprocess.Popen([*root_cmd, "sh", "-c", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    got = ""
    buf = ""
    while ch := p.stdout.read(1):
        if ch in "\r\n":
            m = re.match(r"\s*(\d+) bytes", buf)
            if m:
                progress("write", int(m.group(1)), size, 0)
            if buf.startswith("SUM "):
                got = buf.split()[1]
            buf = ""
        else:
            buf += ch
    if p.wait() or got != want:
        raise DLError("Запись на флешку не удалась. Попробуй ещё раз или другую флешку",
                      "Writing to the stick failed. Try again or another stick")
