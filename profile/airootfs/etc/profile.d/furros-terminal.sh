# shellcheck shell=sh
# FurrOS: $TERMINAL = the terminal of the running desktop. App launchers open console programs (htop, nano, …,
# Terminal=true in their .desktop file) through it: fuzzel runs "$TERMINAL -e" by default and fails when it is
# unset (htop didn't open on Niri), rofi-sensible-terminal tries it first. Login shells and SDDM sessions read this.
if [ -z "${TERMINAL:-}" ]; then
    case "$(printf '%s' "${XDG_CURRENT_DESKTOP:-}${XDG_SESSION_DESKTOP:-}" | tr '[:upper:]' '[:lower:]')" in
        *kde*|*plasma*) _furros_terms="konsole" ;;
        *gnome*)        _furros_terms="kgx gnome-terminal" ;;
        *hyprland*)     _furros_terms="kitty" ;;
        *sway*)         _furros_terms="foot" ;;
        *xfce*)         _furros_terms="xfce4-terminal" ;;
        *mate*)         _furros_terms="mate-terminal" ;;
        *lxqt*)         _furros_terms="qterminal" ;;
        *cosmic*)       _furros_terms="cosmic-term" ;;
        *deepin*)       _furros_terms="deepin-terminal" ;;
        *)              _furros_terms="" ;;
    esac
    for _t in $_furros_terms alacritty kitty foot konsole kgx gnome-terminal xfce4-terminal qterminal xterm; do
        if command -v "$_t" >/dev/null 2>&1; then
            export TERMINAL="$_t"
            break
        fi
    done
    unset _t _furros_terms
fi
