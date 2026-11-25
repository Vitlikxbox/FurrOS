"""What FurrOS can install: desktops, app bundles, wallpapers. Shared by the GUI and the backend."""

BASE_PACKAGES = [
    "base", "linux", "linux-firmware", "intel-ucode", "amd-ucode", "sof-firmware",
    "grub", "efibootmgr", "os-prober", "dosfstools", "ntfs-3g", "ntfsprogs", "exfatprogs", "btrfs-progs",
    "networkmanager", "sudo", "nano", "vim", "bash-completion", "man-db", "man-pages",
    "pipewire", "pipewire-pulse", "pipewire-alsa", "pipewire-jack", "wireplumber", "rtkit",
    "noto-fonts", "noto-fonts-emoji", "ttf-dejavu",
    # Japanese/Chinese/Korean text (names in games, Discord, sites) showed as boxes everywhere (tester report 22.11)
    "noto-fonts-cjk", "ttf-jetbrains-mono", "ttf-hack",
    "fastfetch", "plymouth", "papirus-icon-theme", "adw-gtk-theme", "xdg-user-dirs", "xdg-utils",
    "git", "htop", "pciutils", "ufw", "zram-generator", "power-profiles-daemon", "pacman-contrib", "reflector", "gvfs",  # gvfs (+ udisks2): file managers see USB sticks (tester report 24.11, Thunar)
    "fuse2", "fuse3", "fwupd", "unzip", "7zip", "wget", "which",
    "python", "pyside6", "qt6-webengine", "qt6-svg", "libnotify",
    # laptop/multimedia keys in the tiling desktops (brightness, play/pause/next)
    "brightnessctl", "playerctl",
    "cowsay", "lolcat", "cmatrix", "sl",
]

# id, title, blurb, ram (MB idle, approx), level, display manager, packages, session name, x11?
# desktops the testers haven't confirmed yet (beta, 24.11: MATE, Deepin)
EXPERIMENTAL = " Экспериментальная: тестеры её ещё не проверили, возможны ошибки."
# Zen / LTS: the stock and FurrOS kernels go in next to them as spares (backend.FURROS_KERNEL_WITH)
KERNEL_SPARES = " Обычное ядро и ядро FurrOS ставятся рядом запасными (нужен интернет)."

DESKTOPS = [
    {
        "id": "kde", "name": "KDE Plasma", "tag": "Рекомендуем",
        "blurb": "Красивая и очень настраиваемая. Похожа на Windows: меню внизу слева, панель задач. "
                 "Лучше всего оформлена в стиле FurrOS.",
        "ram": 900, "level": "Новичкам", "dm": "sddm", "session": "plasma", "x11": False,
        "packages": ["plasma-desktop", "plasma-nm", "plasma-pa", "powerdevil", "kscreen", "bluedevil",
                     "kde-gtk-config", "breeze-gtk", "sddm", "sddm-kcm", "plasma-systemmonitor", "kinfocenter",
                     "systemsettings", "xdg-desktop-portal-kde", "konsole", "dolphin", "kate", "ark",
                     "spectacle", "gwenview", "okular", "kcalc", "filelight", "partitionmanager",
                     "plasma-browser-integration", "kwalletmanager", "kdeconnect", "plasma-firewall"],
    },
    {
        "id": "gnome", "name": "GNOME", "tag": "Минимализм",
        "blurb": "Чистая и современная, управляется жестами и клавишей Super. "
                 "Всё в одном обзоре: окна, приложения, поиск.",
        "ram": 1100, "level": "Новичкам", "dm": "gdm", "session": "gnome", "x11": False,
        "packages": ["gnome-shell", "gnome-control-center", "gnome-console", "nautilus", "gnome-tweaks",
                     "gnome-text-editor", "loupe", "papers", "gnome-system-monitor", "gnome-calculator",
                     "gnome-disk-utility", "gnome-shell-extensions", "gnome-shell-extension-appindicator",
                     "xdg-desktop-portal-gnome", "gnome-backgrounds", "gdm", "file-roller", "gnome-keyring"],
    },
    {
        "id": "cosmic", "name": "COSMIC", "tag": "Новинка",
        "blurb": "Новая быстрая оболочка на Rust от System76. Плавающая док-панель и "
                 "удобная автоплитка окон одним переключателем.",
        "ram": 700, "level": "Новичкам", "dm": "cosmic-greeter", "session": "cosmic", "x11": False,
        "packages": ["cosmic"],
    },
    {
        "id": "cinnamon", "name": "Cinnamon", "tag": "Как Windows",
        "blurb": "Классический рабочий стол: меню «Пуск», панель снизу, значки на столе. "
                 "Самый привычный вариант после Windows.",
        "ram": 650, "level": "Новичкам", "dm": "sddm", "session": "cinnamon", "x11": True,
        "packages": ["cinnamon", "nemo-fileroller", "gnome-terminal", "gnome-text-editor", "loupe",
                     "papers", "gnome-calculator", "gnome-system-monitor", "network-manager-applet",
                     "blueman", "gnome-keyring", "sddm"],
    },
    {
        "id": "xfce", "name": "Xfce", "tag": "Экспериментальная",
        # tester-confirmed on X11 (24.11); the Wayland session (labwc) is not confirmed on real hardware yet
        "blurb": "Лёгкая и надёжная. Отлично работает на старых ноутбуках и слабых ПК, "
                 "при этом всё настраивается мышкой. Экспериментальная: в обычном сеансе (X11) проверена тестерами, "
                 "сеанс Wayland пока может работать с ошибками.",
        "ram": 450, "level": "Новичкам", "dm": "sddm", "session": "xfce", "x11": True,
        # labwc: Xfce 4.20's Wayland session (startxfce4 --wayland) runs on it; without it that session dies at once
        # and the monitor shows "no signal" (tester report 23.11)
        "packages": ["xfce4", "xfce4-goodies", "network-manager-applet", "pavucontrol", "blueman",
                     "gnome-keyring", "sddm", "labwc"],
    },
    {
        "id": "mate", "name": "MATE", "tag": "Экспериментальная",
        "blurb": "Наследник старого доброго GNOME 2: две панели, меню, всё на своих местах. "
                 "Лёгкая и спокойная." + EXPERIMENTAL,
        "ram": 500, "level": "Новичкам", "dm": "sddm", "session": "mate", "x11": True,
        "packages": ["mate", "mate-extra", "network-manager-applet", "blueman", "gnome-keyring", "sddm"],
    },
    {
        "id": "budgie", "name": "Budgie", "tag": "Стильная",
        "blurb": "Аккуратная панель сверху и боковая шторка уведомлений Raven. "
                 "Простая, но современная.",
        "ram": 600, "level": "Новичкам", "dm": "sddm", "session": "budgie-desktop", "x11": True,
        "packages": ["budgie-desktop", "budgie-control-center", "budgie-desktop-view",
                     "budgie-backgrounds", "nemo", "gnome-terminal", "gnome-text-editor",
                     "network-manager-applet", "blueman", "gnome-keyring", "sddm"],
    },
    {
        "id": "lxqt", "name": "LXQt", "tag": "Сверхлёгкая",
        "blurb": "Самая экономная из полноценных оболочек. Подойдёт даже для очень старых "
                 "компьютеров с 2 ГБ памяти.",
        "ram": 350, "level": "Новичкам", "dm": "sddm", "session": "lxqt", "x11": True,
        "packages": ["lxqt", "openbox", "breeze-icons", "featherpad", "network-manager-applet",
                     "pavucontrol-qt", "xdg-desktop-portal-lxqt", "sddm"],
    },
    {
        "id": "deepin", "name": "Deepin", "tag": "Экспериментальная",
        "blurb": "Очень красивая оболочка с док-панелью и плавными эффектами, похожа на macOS. "
                 "Иногда капризничает после обновлений." + EXPERIMENTAL,
        "ram": 1000, "level": "Новичкам", "dm": "sddm", "session": "deepin", "x11": True,
        "packages": ["deepin", "deepin-kwin", "deepin-terminal", "deepin-editor", "deepin-image-viewer",
                     "deepin-calculator", "deepin-system-monitor", "sddm"],
    },
    {
        "id": "hyprland", "name": "Hyprland", "tag": "Для красоты",
        "blurb": "Плиточный композитор с анимациями и скруглёнными окнами. Управление с клавиатуры. "
                 "FurrOS ставит готовый «райс» с Waybar.",
        "ram": 500, "level": "Опытным", "dm": "sddm", "session": "hyprland", "x11": False,
        "packages": ["hyprland", "swaybg", "hyprlock", "hypridle", "waybar", "wofi", "kitty", "mako",
                     "thunar", "grim", "slurp", "wl-clipboard", "brightnessctl", "pavucontrol",
                     "network-manager-applet", "polkit-kde-agent", "xdg-desktop-portal-hyprland",
                     "qt5-wayland", "qt6-wayland", "sddm"],
    },
    {
        "id": "niri", "name": "Niri", "tag": "Прокрутка",
        "blurb": "Модный композитор, где окна стоят в бесконечной ленте и прокручиваются вбок. "
                 "Очень удобно на широких мониторах.",
        "ram": 350, "level": "Опытным", "dm": "sddm", "session": "niri", "x11": False,
        "packages": ["niri", "waybar", "fuzzel", "alacritty", "mako", "swaybg", "swaylock", "xwayland-satellite",
                     "xdg-desktop-portal-gnome", "thunar", "pavucontrol", "network-manager-applet", "polkit-gnome",
                     "brightnessctl", "wl-clipboard", "grim", "slurp", "sddm"],
    },
    {
        "id": "sway", "name": "Sway", "tag": "Плитки",
        "blurb": "Строгий плиточный менеджер окон для Wayland, совместимый с i3. "
                 "Минимум отвлекающего, максимум клавиатуры.",
        "ram": 300, "level": "Опытным", "dm": "sddm", "session": "sway", "x11": False,
        "packages": ["sway", "swaybg", "swayidle", "swaylock", "waybar", "wofi", "foot", "mako", "thunar",
                     "grim", "slurp", "wl-clipboard", "brightnessctl", "pavucontrol",
                     "network-manager-applet", "polkit-gnome", "xdg-desktop-portal-wlr", "sddm"],
    },
    {
        "id": "i3", "name": "i3", "tag": "Хардкор",
        "blurb": "Легендарный плиточный менеджер для X11. Очень быстрый, всё через "
                 "горячие клавиши и текстовый конфиг.",
        "ram": 250, "level": "Опытным", "dm": "sddm", "session": "i3", "x11": True,
        "packages": ["i3-wm", "i3status", "i3lock", "rofi", "alacritty", "picom", "feh", "dunst", "thunar",
                     "maim", "xclip", "network-manager-applet", "pavucontrol", "polkit-gnome", "sddm"],
    },
    {
        "id": "bspwm", "name": "bspwm", "tag": "Минимал",
        "blurb": "Окна делят экран как двоичное дерево. Горячие клавиши в sxhkd, панель Polybar. "
                 "Любимец «райсеров» на r/unixporn.",
        "ram": 220, "level": "Опытным", "dm": "sddm", "session": "bspwm", "x11": True,
        "packages": ["bspwm", "sxhkd", "polybar", "rofi", "alacritty", "picom", "feh", "dunst", "thunar", "maim", "i3lock",
                     "xclip", "network-manager-applet", "pavucontrol", "polkit-gnome", "sddm"],
    },
    {
        "id": "awesome", "name": "Awesome", "tag": "На Lua",
        "blurb": "Плиточный менеджер с встроенной панелью, настраивается на языке Lua. "
                 "Можно запрограммировать что угодно.",
        "ram": 250, "level": "Опытным", "dm": "sddm", "session": "awesome", "x11": True,
        "packages": ["maim", "xclip", "awesome", "alacritty", "rofi", "picom", "thunar", "network-manager-applet", "pavucontrol",
                     "polkit-gnome", "sddm"],
    },
    {
        "id": "qtile", "name": "Qtile", "tag": "На Python",
        "blurb": "Плиточный менеджер, который целиком настраивается на Python. "
                 "Идеален, если ты программист.",
        "ram": 280, "level": "Опытным", "dm": "sddm", "session": "qtile", "x11": True,
        "packages": ["maim", "xclip", "qtile", "python-psutil", "alacritty", "rofi", "picom", "feh", "dunst", "thunar",
                     "network-manager-applet", "pavucontrol", "polkit-gnome", "sddm"],
    },
    {
        "id": "console", "name": "Только консоль", "tag": "Без графики",
        "blurb": "Никакой графики: только терминал. Для серверов и тех, кто хочет собрать "
                 "всё сам с нуля.",
        "ram": 120, "level": "Экспертам", "dm": None, "session": None, "x11": False,
        "packages": [],
    },
]

TILING = {"hyprland", "niri", "sway", "i3", "bspwm", "awesome", "qtile"}

X11_PACKAGES =["xorg-server", "xorg-xinit", "xorg-xrandr"]

# id, title, blurb, packages, default-on
APP_BUNDLES = [
    {"id": "browser-firefox", "group": "browser", "name": "Firefox", "blurb": "Свободный браузер от Mozilla.",
     "packages": ["firefox", "firefox-i18n-ru"], "default": True},
    {"id": "browser-chromium", "group": "browser", "name": "Chromium", "blurb": "Открытая основа Google Chrome.",
     "packages": ["chromium"], "default": False},
    {"id": "browser-none", "group": "browser", "name": "Без браузера", "blurb": "Поставлю сам потом.",
     "packages": [], "default": False},
    {"id": "office", "name": "Офис", "blurb": "LibreOffice: документы, таблицы, презентации.",
     "packages": ["libreoffice-fresh", "libreoffice-fresh-ru", "hunspell-ru", "hunspell-en_us"], "default": True},
    {"id": "media", "name": "Музыка и видео", "blurb": "VLC, mpv и кодеки, чтобы открывалось всё.",
     "packages": ["vlc", "vlc-plugins-all", "mpv", "gst-plugins-good", "gst-plugins-bad", "gst-plugins-ugly",
                  "gst-libav", "ffmpeg"], "default": True},
    {"id": "graphics", "name": "Рисование и фото", "blurb": "Krita для рисования, GIMP для фото, Inkscape для векторов.",
     "packages": ["krita", "gimp", "inkscape"], "default": False},
    {"id": "gaming", "name": "Игры", "blurb": "Steam, Lutris, Wine, GameMode, MangoHud и Gamescope, а из Flathub — Bottles (программы Windows), Heroic (Epic и GOG) и ProtonPlus (версии Proton). Включает multilib и игровые настройки.",
     "packages": ["steam", "lutris", "wine", "winetricks", "protontricks", "gamemode", "lib32-gamemode", "mangohud", "gamescope",
                  "lib32-mangohud", "flatpak"], "default": False, "multilib": True},
    {"id": "chat", "name": "Общение", "blurb": "Telegram и Discord.",
     "packages": ["telegram-desktop", "discord"], "default": False},
    {"id": "stream", "name": "Стримы и запись", "blurb": "OBS Studio для записи экрана и стримов.",
     "packages": ["obs-studio"], "default": False},
    {"id": "dev", "name": "Программирование", "blurb": "VS Code (OSS), base-devel, Python, Node.js, Rust (rustup).",
     "packages": ["code", "base-devel", "python-pip", "nodejs", "npm", "rustup"], "default": False},
    {"id": "aur", "name": "Помощник AUR (yay)", "blurb": "Доступ к тысячам пакетов из AUR одной командой.",
     "packages": ["base-devel"], "default": True},
    {"id": "flatpak", "name": "Flatpak", "blurb": "Магазин приложений Flathub в песочнице. С ним Flatseal (права приложений) и Warehouse (управление Flatpak).",
     "packages": ["flatpak", "flatseal", "warehouse"], "default": False},
    {"id": "bluetooth", "name": "Bluetooth", "blurb": "Наушники, мышки, геймпады.",
     "packages": ["bluez", "bluez-utils"], "default": True},
    {"id": "printing", "name": "Принтеры", "blurb": "CUPS и драйверы для печати и сканеров.",
     "packages": ["cups", "cups-pdf", "system-config-printer", "sane"], "default": False},
    {"id": "a11y", "name": "Специальные возможности",
     "blurb": "Экранный диктор Orca и синтез речи для незрячих и слабовидящих. В KDE и GNOME включается Super+Alt+S.",
     "packages": ["orca", "espeak-ng", "speech-dispatcher"], "default": False},
    {"id": "snapshots", "name": "Снимки системы",
     "blurb": "Снимок перед каждым обновлением. Если что-то сломалось, загрузись в снимок прямо из меню загрузки (нужен Btrfs).",
     "packages": ["snapper", "snap-pac", "grub-btrfs", "inotify-tools", "btrfs-assistant"], "default": True,
     "needs_btrfs": True},
]

WALLPAPERS = [
    ("furros-default.png", "FurrOS"),
    ("furros-pixie-lying.png", "Пикси: лежит"),
    ("furros-lapa-wave.png", "Лапа: привет"),
    ("furros-lapa-timer.png", "Лапа: таймер"),
    ("furros-lapa-grr.png", "Лапа: грр"),
    ("furros-lapa-hoodie.png", "Лапа: худи"),
    ("furros-lapa-sip.png", "Лапа: прочитано"),
    ("furros-lapa-heart.png", "Лапа: ♥"),
    ("furros-velvet.png", "Велвет"),
    ("furros-velvet-2.png", "Велвет: вкусняшка"),
    ("furros-mimi.png", "Мими"),
    ("furros-bubblegum.png", "Bubblegum"),
    ("furros-danyok.png", "Данёк"),
    ("furros-danyok-lemon.png", "Данёк: лимон"),
]

# UI language code -> (system locale, native name, default keyboard layouts, default timezone)
LANGUAGES = {
    "ru": ("ru_RU.UTF-8", "Русский", ["us", "ru"], "Europe/Moscow"),
    "en": ("en_US.UTF-8", "English", ["us"], "America/New_York"),
    "pl": ("pl_PL.UTF-8", "Polski", ["pl"], "Europe/Warsaw"),
    "es": ("es_ES.UTF-8", "Español", ["es"], "Europe/Madrid"),
}

# animated wallpapers: (file stem in /usr/share/backgrounds/furros/animated, title, has flashing colours)
ANIMATED = [
    ("anim-pitbull-terrier", "Pitbull Terrier", False),
    ("anim-just-be-competent", "Just Be Competent", False),
    ("anim-bothered", "Bothered", True),
    ("anim-two", "Two", True),
    ("anim-kiss-me", "Kiss Me", False),
    ("anim-number", "Number", False),
    ("anim-you-got-curves", "You Got Curves", False),
    ("anim-do-not-push", "Do Not Push", False),
    ("anim-if-i-take-you-home", "If I Take You Home", False),
    # 13.11.2026: Typh, sashley, Oniixide, RIGOR MORT1S clips (art/yt-new -> tools/make_anim_new.sh)
    ("anim-pretty-cvnt", "Pretty Cvnt", True),
    ("anim-paper-planes", "Paper Planes", True),
    ("anim-kismet", "Kismet", False),
    ("anim-i-wish-we-never-met", "I Wish We Never Met", False),
    ("anim-namida", "Namida", False),
    ("anim-close-eyes", "Close Eyes", False),
    ("anim-better-luck-next-time", "Better Luck Next Time", False),
    ("anim-contact", "Contact", False),
    ("anim-plug-me-in", "Plug Me In", False),
    ("anim-bloodpop", "Bloodpop", False),
    ("anim-gallery-piece", "Gallery Piece", False),
    ("anim-p3t", "P3T", True),
    ("anim-basshunter-dota", "Basshunter Dota", False),
    ("anim-emo-boy", "Emo Boy", False),
    ("anim-nasty-dog", "Nasty Dog", False),
    ("anim-mommy", "Mommy", False),
    ("anim-ch4insaww", "Ch4insaww", True),
]
# desktops where the video actually moves; everywhere else a still frame is used
# live (video) wallpapers: KDE (Smart Video Wallpaper), Wayland tilers (mpvpaper), X11 tilers (xwinwrap + mpv)
VIDEO_DESKTOPS = {"kde", "hyprland", "sway", "niri", "cosmic", "i3", "bspwm", "awesome", "qtile"}   # COSMIC: mpvpaper
X11_VIDEO_DESKTOPS = {"i3", "bspwm", "awesome", "qtile"}

# the kernel; "linux-furros" comes from [furros] once it is set up, so the stock kernel stays as the spare one
KERNELS = [
    {"id": "linux", "name": "Обычное", "blurb": "Свежее ядро Arch. Подходит почти всем", "default": True},
    {"id": "linux-zen", "name": "Zen", "blurb": "Отзывчивее под нагрузкой: игры, стримы, музыка." + KERNEL_SPARES, "default": False},
    {"id": "linux-lts", "name": "LTS", "blurb": "Долгой поддержки: меньше сюрпризов, для работы и старого железа." + KERNEL_SPARES, "default": False},
    {"id": "linux-furros", "name": "FurrOS", "blurb": "Наше ядро для игр и рабочего стола. Нужен интернет во время установки",
     "default": False},
]
KERNEL_IDS = {k["id"] for k in KERNELS}

# Languages of the installed system (the installer itself speaks only the 4 UI languages above).
# (locale exactly as the first field of glibc's /usr/share/i18n/SUPPORTED — some have no ".UTF-8" suffix there,
#  native name, default keyboard layouts, input method for languages XKB can't type: "zh" "zh_tw" "ja" "ko" "vi")
SYSTEM_LANGUAGES = [
    ("en_US.UTF-8", "English (US)", ["us"], None),
    ("en_GB.UTF-8", "English (UK)", ["gb"], None),
    ("ru_RU.UTF-8", "Русский", ["us", "ru"], None),
    ("uk_UA.UTF-8", "Українська", ["us", "ua"], None),
    ("be_BY.UTF-8", "Беларуская", ["us", "by"], None),
    ("kk_KZ.UTF-8", "Қазақ тілі", ["us", "kz"], None),
    ("pl_PL.UTF-8", "Polski", ["pl"], None),
    ("de_DE.UTF-8", "Deutsch", ["de"], None),
    ("fr_FR.UTF-8", "Français", ["fr"], None),
    ("es_ES.UTF-8", "Español (España)", ["es"], None),
    ("es_MX.UTF-8", "Español (México)", ["latam"], None),
    ("it_IT.UTF-8", "Italiano", ["it"], None),
    ("pt_PT.UTF-8", "Português (Portugal)", ["pt"], None),
    ("pt_BR.UTF-8", "Português (Brasil)", ["br"], None),
    ("nl_NL.UTF-8", "Nederlands", ["us"], None),
    ("tr_TR.UTF-8", "Türkçe", ["tr"], None),
    ("cs_CZ.UTF-8", "Čeština", ["cz"], None),
    ("sk_SK.UTF-8", "Slovenčina", ["sk"], None),
    ("hu_HU.UTF-8", "Magyar", ["hu"], None),
    ("ro_RO.UTF-8", "Română", ["ro"], None),
    ("bg_BG.UTF-8", "Български", ["us", "bg(phonetic)"], None),
    ("sr_RS", "Српски", ["us", "rs"], None),
    ("sr_RS@latin", "Srpski (latinica)", ["rs(latin)"], None),
    ("hr_HR.UTF-8", "Hrvatski", ["hr"], None),
    ("sl_SI.UTF-8", "Slovenščina", ["si"], None),
    ("el_GR.UTF-8", "Ελληνικά", ["us", "gr"], None),
    ("he_IL.UTF-8", "עברית", ["us", "il"], None),
    ("ar_EG.UTF-8", "العربية", ["us", "ara"], None),
    ("fa_IR", "فارسی", ["us", "ir"], None),
    ("hi_IN", "हिन्दी", ["us", "in"], None),
    ("ja_JP.UTF-8", "日本語", ["jp"], "ja"),
    ("ko_KR.UTF-8", "한국어", ["kr"], "ko"),
    ("zh_CN.UTF-8", "中文（简体）", ["us"], "zh"),
    ("zh_TW.UTF-8", "中文（繁體）", ["us"], "zh_tw"),
    ("vi_VN", "Tiếng Việt", ["us"], "vi"),
    ("th_TH.UTF-8", "ไทย", ["us", "th"], None),
    ("id_ID.UTF-8", "Bahasa Indonesia", ["us"], None),
    ("ka_GE.UTF-8", "ქართული", ["us", "ge"], None),
    ("hy_AM", "Հայերեն", ["us", "am(phonetic)"], None),
    ("az_AZ", "Azərbaycan dili", ["az"], None),
    ("uz_UZ.UTF-8", "Oʻzbekcha", ["us", "uz(latin)"], None),
    ("ky_KG", "Кыргызча", ["us", "kg"], None),
    ("tg_TJ.UTF-8", "Тоҷикӣ", ["us", "tj"], None),
    ("mn_MN", "Монгол", ["us", "mn"], None),
    ("lt_LT.UTF-8", "Lietuvių", ["lt"], None),
    ("lv_LV.UTF-8", "Latviešu", ["lv"], None),
    ("et_EE.UTF-8", "Eesti", ["ee"], None),
    ("fi_FI.UTF-8", "Suomi", ["fi"], None),
    ("sv_SE.UTF-8", "Svenska", ["se"], None),
    ("nb_NO.UTF-8", "Norsk bokmål", ["no"], None),
    ("da_DK.UTF-8", "Dansk", ["dk"], None),
]
LOCALES = [(l[0], l[1]) for l in SYSTEM_LANGUAGES]

# Input methods for the languages XKB alone can't type (Chinese, Japanese, Korean, Vietnamese):
# Fcitx 5 everywhere, IBus on GNOME (built into GNOME Shell). All in [extra].
INPUT_METHODS = {
    "zh":    {"fcitx5": ["fcitx5-chinese-addons"], "ibus": ("ibus-libpinyin", "libpinyin"), "fonts": ["noto-fonts-cjk"]},
    "zh_tw": {"fcitx5": ["fcitx5-chewing"], "ibus": ("ibus-chewing", "chewing"), "fonts": ["noto-fonts-cjk"]},
    "ja":    {"fcitx5": ["fcitx5-mozc"], "ibus": ("ibus-anthy", "anthy"), "fonts": ["noto-fonts-cjk"]},
    "ko":    {"fcitx5": ["fcitx5-hangul"], "ibus": ("ibus-hangul", "hangul"), "fonts": ["noto-fonts-cjk"]},
    "vi":    {"fcitx5": ["fcitx5-unikey"], "ibus": ("ibus-unikey", "Unikey"), "fonts": []},
}

# Keyboard layouts: XKB "layout" or "layout(variant)" (xkeyboard-config 2.49, rules/evdev.lst), the native name of the
# language, and the variant's description (translated through i18n, shown after a dash)
KEYBOARDS = [
    ("us", "English (US)", None),
    ("us(intl)", "English (US)", "международная"),
    ("us(dvorak)", "English (US)", "Dvorak"),
    ("us(colemak)", "English (US)", "Colemak"),
    ("gb", "English (UK)", None),
    ("ru", "Русский", None),
    ("ru(phonetic)", "Русский", "фонетическая (ЯВЕРТЫ)"),
    ("ru(phonetic_winkeys)", "Русский", "фонетическая, Windows"),
    ("ru(phonetic_YAZHERTY)", "Русский", "фонетическая (ЯЖЕРТЫ)"),
    ("ru(phonetic_azerty)", "Русский", "фонетическая, AZERTY"),
    ("ru(phonetic_dvorak)", "Русский", "фонетическая, Dvorak"),
    ("ua", "Українська", None),
    ("ua(phonetic)", "Українська", "фонетическая"),
    ("by", "Беларуская", None),
    ("by(phonetic)", "Беларуская", "фонетическая"),
    ("kz", "Қазақша", None),
    ("bg", "Български", None),
    ("bg(phonetic)", "Български", "фонетическая (традиционная)"),
    ("bg(bas_phonetic)", "Български", "фонетическая (новая)"),
    ("rs", "Српски", None),
    ("rs(latin)", "Srpski", "латиница"),
    ("mk", "Македонски", None),
    ("pl", "Polski", None),
    ("de", "Deutsch", None),
    ("ch", "Deutsch (Schweiz)", None),
    ("fr", "Français", None),
    ("be", "Français (Belgique)", None),
    ("ca", "Français (Canada)", None),
    ("es", "Español", None),
    ("latam", "Español (Latinoamérica)", None),
    ("it", "Italiano", None),
    ("pt", "Português", None),
    ("br", "Português (Brasil)", None),
    ("nl", "Nederlands", None),
    ("tr", "Türkçe", None),
    ("cz", "Čeština", None),
    ("sk", "Slovenčina", None),
    ("hu", "Magyar", None),
    ("ro", "Română", None),
    ("hr", "Hrvatski", None),
    ("si", "Slovenščina", None),
    ("al", "Shqip", None),
    ("gr", "Ελληνικά", None),
    ("il", "עברית", None),
    ("il(phonetic)", "עברית", "фонетическая"),
    ("ara", "العربية", None),
    ("ir", "فارسی", None),
    ("in", "हिन्दी", None),
    ("in(hin-kagapa)", "हिन्दी", "фонетическая"),
    ("in(urd-phonetic)", "اردو", "фонетическая"),
    ("th", "ไทย", None),
    ("vn", "Tiếng Việt", None),
    ("jp", "日本語", None),
    ("kr", "한국어", None),
    ("ge", "ქართული", None),
    ("am", "Հայերեն", None),
    ("am(phonetic)", "Հայերեն", "фонетическая"),
    ("az", "Azərbaycanca", None),
    ("uz", "Oʻzbekcha", None),
    ("uz(latin)", "Oʻzbekcha", "латиница"),
    ("kg", "Кыргызча", None),
    ("kg(phonetic)", "Кыргызча", "фонетическая"),
    ("tj", "Тоҷикӣ", None),
    ("mn", "Монгол", None),
    ("lt", "Lietuvių", None),
    ("lv", "Latviešu", None),
    ("ee", "Eesti", None),
    ("fi", "Suomi", None),
    ("se", "Svenska", None),
    ("no", "Norsk", None),
    ("dk", "Dansk", None),
    ("is", "Íslenska", None),
]
KEYBOARD_CODES = {k[0] for k in KEYBOARDS}


def xkb_split(codes):
    """['us', 'ru(phonetic)'] -> ('us,ru', ',phonetic'): XKB takes layouts and variants as two parallel lists."""
    lay = [c.split("(")[0] for c in codes]
    var = [c[c.index("(") + 1:-1] if "(" in c else "" for c in codes]
    return ",".join(lay), ",".join(var)


def system_language(locale):
    return next((l for l in SYSTEM_LANGUAGES if l[0] == locale), SYSTEM_LANGUAGES[0])

LAYOUT_TOGGLES = [
    ("grp:alt_shift_toggle", "Alt + Shift"),
    ("grp:ctrl_shift_toggle", "Ctrl + Shift"),
    ("grp:win_space_toggle", "Super + Пробел"),
    ("grp:caps_toggle", "Caps Lock"),
]


def desktop(did):
    return next(d for d in DESKTOPS if d["id"] == did)
