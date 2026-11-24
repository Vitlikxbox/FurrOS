/* Hotkeys per desktop. Descriptions are translated via CONTENT[lang].keydesc[id]. */
window.FURROS_KEYS = {
  common: { name: "FurrOS", keys: [
    ["Ctrl + C", "copy"], ["Ctrl + V", "paste"], ["Ctrl + Z", "undo"], ["Ctrl + S", "save"],
    ["Ctrl + Shift + C", "termCopy"], ["Ctrl + Shift + V", "termPaste"], ["Tab", "complete"],
    ["Ctrl + Alt + F3", "tty"], ["Alt + Shift", "layout"],
  ] },
  kde: { name: "KDE Plasma", keys: [
    ["Super", "menu"], ["Alt + Space", "krunner"], ["Ctrl + Alt + T", "term"], ["Super + E", "files"],
    ["Alt + F4", "close"], ["Alt + Tab", "switch"], ["Super + W", "overview"], ["Super + D", "desktop"],
    ["Super + ←/→", "tile"], ["Super + PgUp", "maximize"], ["Ctrl + F1…F4", "ws"], ["Super + L", "lock"],
    ["Print", "screenshot"], ["Ctrl + Esc", "taskmgr"],
  ] },
  gnome: { name: "GNOME", keys: [
    ["Super", "overview"], ["Super + A", "apps"], ["Super + Tab", "switch"], ["Alt + F4", "close"],
    ["Super + ←/→", "tile"], ["Super + ↑", "maximize"], ["Super + PgUp/PgDn", "ws"], ["Super + H", "hide"],
    ["Super + V", "notifications"], ["Super + L", "lock"], ["Print", "screenshot"], ["Ctrl + Alt + Del", "logout"],
  ] },
  cosmic: { name: "COSMIC", keys: [
    ["Super", "menu"], ["Super + A", "apps"], ["Super + T", "term"], ["Super + F", "files"], ["Super + Q", "close"],
    ["Super + Y", "tilingToggle"], ["Super + ←/→/↑/↓", "focus"], ["Super + Shift + ←/→", "move"],
    ["Super + 1…9", "ws"], ["Super + W", "overview"], ["Super + Esc", "lock"], ["Print", "screenshot"],
  ] },
  cinnamon: { name: "Cinnamon", keys: [
    ["Super", "menu"], ["Ctrl + Alt + T", "term"], ["Super + E", "files"], ["Alt + F4", "close"],
    ["Alt + Tab", "switch"], ["Super + D", "desktop"], ["Super + ←/→", "tile"], ["Ctrl + Alt + ←/→", "ws"],
    ["Ctrl + Alt + ↑", "overview"], ["Ctrl + Alt + L", "lock"], ["Print", "screenshot"],
  ] },
  xfce: { name: "Xfce", keys: [
    ["Alt + F1", "menu"], ["Alt + F2", "launcher"], ["Super + T", "term"], ["Super + E", "files"],
    ["Alt + F4", "close"], ["Alt + Tab", "switch"], ["Ctrl + Alt + D", "desktop"], ["Ctrl + F1…F4", "ws"],
    ["Ctrl + Alt + L", "lock"], ["Print", "screenshot"],
  ] },
  mate: { name: "MATE", keys: [
    ["Alt + F1", "menu"], ["Alt + F2", "launcher"], ["Ctrl + Alt + T", "term"], ["Alt + F4", "close"],
    ["Alt + Tab", "switch"], ["Ctrl + Alt + D", "desktop"], ["Ctrl + Alt + ←/→", "ws"], ["Ctrl + Alt + L", "lock"],
    ["Print", "screenshot"],
  ] },
  budgie: { name: "Budgie", keys: [
    ["Super", "menu"], ["Ctrl + Alt + T", "term"], ["Super + N", "notifications"], ["Alt + F4", "close"],
    ["Alt + Tab", "switch"], ["Super + ←/→", "tile"], ["Super + L", "lock"], ["Print", "screenshot"],
  ] },
  lxqt: { name: "LXQt", keys: [
    ["Alt + F1", "menu"], ["Alt + F2", "launcher"], ["Ctrl + Alt + T", "term"], ["Super + E", "files"],
    ["Alt + F4", "close"], ["Alt + Tab", "switch"], ["Super + D", "desktop"], ["Ctrl + Alt + L", "lock"],
  ] },
  deepin: { name: "Deepin", keys: [
    ["Super", "menu"], ["Ctrl + Alt + T", "term"], ["Super + E", "files"], ["Alt + F4", "close"],
    ["Super + S", "overview"], ["Super + D", "desktop"], ["Super + L", "lock"], ["Ctrl + Alt + A", "screenshot"],
  ] },
  hyprland: { name: "Hyprland", keys: [
    ["Super + Enter", "term"], ["Super + D", "launcher"], ["Super + E", "files"], ["Super + Q", "close"],
    ["Super + F", "fullscreen"], ["Super + V", "float"], ["Super + ←/→/↑/↓", "focus"], ["Super + Shift + ←/→", "move"],
    ["Super + 1…9", "ws"], ["Super + Shift + 1…9", "moveWs"], ["Super + LMB", "dragWin"], ["Super + RMB", "resize"],
    ["Super + L", "lock"], ["Print", "screenshot"], ["Super + F1", "help"], ["Super + Shift + E", "exit"],
  ] },
  niri: { name: "Niri", keys: [
    ["Super + Enter", "term"], ["Super + D", "launcher"], ["Super + Q", "close"], ["Super + ←/→", "scroll"],
    ["Super + Shift + ←/→", "move"], ["Super + R", "colWidth"], ["Super + F", "maximize"], ["Super + 1…5", "ws"],
    ["Super + Shift + 1…5", "moveWs"], ["Super + V", "float"], ["Super + O", "overview"], ["Super + Shift + /", "help"], ["Super + L", "lock"], ["Print", "screenshot"], ["Super + Shift + E", "exit"],
  ] },
  sway: { name: "Sway", keys: [
    ["Super + Enter", "term"], ["Super + D", "launcher"], ["Super + Q", "close"], ["Super + F", "fullscreen"],
    ["Super + V", "float"], ["Super + ←/→/↑/↓", "focus"], ["Super + Shift + ←/→", "move"], ["Super + W", "tabbed"],
    ["Super + R", "resize"], ["Super + 1…9", "ws"], ["Super + Shift + 1…9", "moveWs"], ["Super + L", "lock"],
    ["Super + Shift + C", "reload"], ["Super + F1", "help"], ["Super + Shift + E", "exit"],
  ] },
  i3: { name: "i3", keys: [
    ["Super + Enter", "term"], ["Super + D", "launcher"], ["Super + Q", "close"], ["Super + F", "fullscreen"],
    ["Super + V", "float"], ["Super + ←/→/↑/↓", "focus"], ["Super + Shift + ←/→", "move"], ["Super + W", "tabbed"],
    ["Super + R", "resize"], ["Super + 1…9", "ws"], ["Super + Shift + 1…9", "moveWs"], ["Super + L", "lock"],
    ["Super + Shift + R", "reload"], ["Super + F1", "help"], ["Super + Shift + E", "exit"],
  ] },
  bspwm: { name: "bspwm", keys: [
    ["Super + Enter", "term"], ["Super + D", "launcher"], ["Super + Q", "close"], ["Super + F", "fullscreen"],
    ["Super + V", "float"], ["Super + ←/→/↑/↓", "focus"], ["Super + Shift + ←/→", "move"], ["Super + 1…9", "ws"],
    ["Super + Shift + 1…9", "moveWs"], ["Super + Esc", "reload"], ["Super + F1", "help"], ["Super + Shift + E", "exit"],
  ] },
  awesome: { name: "Awesome", keys: [
    ["Super + Enter", "term"], ["Super + R", "launcher"], ["Super + Shift + C", "close"], ["Super + F", "fullscreen"],
    ["Super + Space", "nextLayout"], ["Super + J/K", "focus"], ["Super + 1…9", "ws"], ["Super + Ctrl + R", "reload"],
    ["Super + S", "help"], ["Super + Shift + Q", "exit"],
  ] },
  qtile: { name: "Qtile", keys: [
    ["Super + Enter", "term"], ["Super + D", "launcher"], ["Super + Q", "close"], ["Super + F", "fullscreen"],
    ["Super + V", "float"], ["Super + Tab", "nextLayout"], ["Super + ←/→/↑/↓", "focus"], ["Super + 1…9", "ws"],
    ["Super + Shift + 1…9", "moveWs"], ["Super + Shift + R", "reload"], ["Super + F1", "help"], ["Super + Shift + E", "exit"],
  ] },
};
