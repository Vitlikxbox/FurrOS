#!/usr/bin/env python3
"""FurrOS achievements: little badges for first steps in Linux. Checked by Lapa in the tray (furros-lapa),
shown in «About FurrOS» (furros-about). Stored in ~/.local/share/furros/achievements.json as {id: unix time}.

Counters that existed before the first check (pacman runs during installation, old shell history) go into a
baseline, so only what the user does by themselves counts."""
import json
import os
import re
import time
from pathlib import Path

DATA = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "furros"
STORE = DATA / "achievements.json"
SCHOOL = DATA / "school.json"          # written by Lapa's School (furros-academy) on every save
PACMAN_LOG = Path("/var/log/pacman.log")

# id, emoji, then (title, how to get it) in ru / en / pl / es
ACH = [
    ("hello", "🐾", {"ru": ("Привет, FurrOS!", "Первый вход в систему"),
                    "en": ("Hello, FurrOS!", "Log in for the first time"),
                    "pl": ("Cześć, FurrOS!", "Pierwsze logowanie"),
                    "es": ("¡Hola, FurrOS!", "Inicia sesión por primera vez")}),
    ("update", "⟳", {"ru": ("Свежая шёрстка", "Обнови систему: furros-update"),
                    "en": ("Fresh fur", "Update the system: furros-update"),
                    "pl": ("Świeże futerko", "Zaktualizuj system: furros-update"),
                    "es": ("Pelaje nuevo", "Actualiza el sistema: furros-update")}),
    ("install", "📦", {"ru": ("Своя миска", "Сам установи программу через pacman или yay"),
                      "en": ("My own bowl", "Install a program yourself with pacman or yay"),
                      "pl": ("Własna miska", "Sam zainstaluj program przez pacman lub yay"),
                      "es": ("Mi propio cuenco", "Instala un programa tú mismo con pacman o yay")}),
    ("terminal", "⌨", {"ru": ("Хвост в терминале", "100 команд в истории терминала"),
                      "en": ("Terminal tail", "100 commands in the terminal history"),
                      "pl": ("Ogon w terminalu", "100 poleceń w historii terminala"),
                      "es": ("Cola en la terminal", "100 comandos en el historial de la terminal")}),
    ("school1", "🎓", {"ru": ("Первый урок", "Пройди первую главу в Школе Лапы"),
                      "en": ("First lesson", "Finish the first chapter in Lapa's School"),
                      "pl": ("Pierwsza lekcja", "Ukończ pierwszy rozdział w Szkole Łapy"),
                      "es": ("Primera lección", "Termina el primer capítulo de la Escuela de Lapa")}),
    ("school_half", "📚", {"ru": ("Отличница Лапы", "Половина глав Школы Лапы"),
                          "en": ("Lapa's top student", "Half of the chapters of Lapa's School"),
                          "pl": ("Prymus Łapy", "Połowa rozdziałów Szkoły Łapy"),
                          "es": ("Alumno estrella de Lapa", "La mitad de los capítulos de la Escuela de Lapa")}),
    ("school_all", "🏆", {"ru": ("Хороший пёс", "Все главы Школы Лапы"),
                         "en": ("Good dog", "All chapters of Lapa's School"),
                         "pl": ("Dobry pies", "Wszystkie rozdziały Szkoły Łapy"),
                         "es": ("Buen perro", "Todos los capítulos de la Escuela de Lapa")}),
    ("about", "🔍", {"ru": ("Любопытный нос", "Загляни в «О системе»"),
                    "en": ("Curious nose", "Peek into «About FurrOS»"),
                    "pl": ("Ciekawski nos", "Zajrzyj do «O systemie»"),
                    "es": ("Nariz curiosa", "Echa un vistazo a «Acerca de FurrOS»")}),
    ("night", "🌙", {"ru": ("Ночная лапа", "Посиди за компьютером после 3 часов ночи"),
                    "en": ("Night paw", "Be at the computer after 3 a.m."),
                    "pl": ("Nocna łapa", "Siedź przy komputerze po 3 w nocy"),
                    "es": ("Pata nocturna", "Usa el ordenador después de las 3 de la madrugada")}),
    ("week", "📅", {"ru": ("Неделя в стае", "Неделя с FurrOS"),
                   "en": ("A week in the pack", "A week with FurrOS"),
                   "pl": ("Tydzień w stadzie", "Tydzień z FurrOS"),
                   "es": ("Una semana en la manada", "Una semana con FurrOS")}),
]
LAPA_CHAPTERS = 14   # chapters of Lapa's own level in the school (see web/content/*.js)


def load():
    try:
        d = json.loads(STORE.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save(d):
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    tmp.replace(STORE)


def _pacman_counts():
    """(full upgrades, package installs) in pacman.log: pacman -Syu / furros-update and pacman -S / yay -S."""
    up = inst = 0
    try:
        with PACMAN_LOG.open(errors="replace") as f:
            for line in f:
                m = re.search(r"\[PACMAN\] Running '(.*)'", line)
                if not m:
                    continue
                words = m.group(1).split()
                op = next((w for w in words[1:] if re.fullmatch(r"-S[a-zA-Z]*", w)), None)
                if not op:
                    continue
                if "u" in op:
                    up += 1
                elif "--asdeps" not in words and any(not w.startswith("-") for w in words[words.index(op) + 1:]):
                    inst += 1
    except OSError:
        pass
    return up, inst


def _history_len():
    n = 0
    for name in (".bash_history", ".zsh_history", ".local/share/fish/fish_history"):
        try:
            text = (Path.home() / name).read_text(errors="replace")
        except OSError:
            continue
        n += text.count("- cmd:") if name.endswith("fish_history") else len(text.splitlines())
    return n


def _school_done():
    try:
        st = json.loads(SCHOOL.read_text())
        return sum(1 for v in (st.get("done") or {}).values() if v)
    except (OSError, ValueError, AttributeError):
        return 0


def unlock(aid, d=None):
    """Mark one achievement as earned (e.g. furros-about calls this for "about"). True if it is new."""
    d = load() if d is None else d
    if aid in d:
        return False
    d[aid] = int(time.time())
    save(d)
    return True


def check():
    """Look at the system, save what's newly earned and return those ids."""
    d = load()
    now = time.time()
    up, inst = _pacman_counts()
    hist = _history_len()
    base = d.get("_base")
    if not isinstance(base, dict):   # the first run: whatever happened before doesn't count
        base = d["_base"] = {"up": up, "inst": inst, "hist": hist, "since": int(now)}
    new = []

    def give(aid, cond):
        if cond and aid not in d:
            d[aid] = int(now)
            new.append(aid)

    done = _school_done()
    give("hello", True)
    give("update", up > base["up"])
    give("install", inst > base["inst"])
    give("terminal", hist >= base["hist"] + 100)
    give("school1", done >= 1)
    give("school_half", done >= LAPA_CHAPTERS // 2)
    give("school_all", done >= LAPA_CHAPTERS)
    give("night", 3 <= time.localtime(now).tm_hour < 5)
    give("week", now - base.get("since", now) >= 7 * 86400)
    save(d)
    return new


def text(aid, lang):
    for a, emoji, t in ACH:
        if a == aid:
            title, how = t.get(lang, t["en"])
            return emoji, title, how
    return "🐾", aid, ""
