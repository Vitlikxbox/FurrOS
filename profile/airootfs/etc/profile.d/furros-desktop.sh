# shellcheck shell=sh
# FurrOS: the session files of i3, Awesome and Qtile (and Sway, Niri) have no DesktopNames=, so the login screen
# leaves XDG_CURRENT_DESKTOP unset and everything that looks at it (portals, the wallpaper tools, $TERMINAL below)
# can't tell which desktop runs (tester report 20.11, Qtile). The login screen still names the session in
# XDG_SESSION_DESKTOP / DESKTOP_SESSION: take it from there. SDDM's Xsession and wayland-session scripts source
# /etc/profile before starting the session, so the window manager and every app inherit it.
# Sorted before furros-terminal.sh, which uses it.
if [ -z "${XDG_CURRENT_DESKTOP:-}" ]; then
    _furros_s=${XDG_SESSION_DESKTOP:-${DESKTOP_SESSION:-}}
    _furros_s=${_furros_s##*/}
    _furros_s=${_furros_s%.desktop}
    case "$_furros_s" in
        qtile*) export XDG_CURRENT_DESKTOP=qtile ;;          # qtile, qtile-wayland, qtile-generic
        i3*) export XDG_CURRENT_DESKTOP=i3 ;;                # i3, i3-with-shmlog
        awesome | sway | niri | bspwm) export XDG_CURRENT_DESKTOP="$_furros_s" ;;
    esac
    unset _furros_s
fi
