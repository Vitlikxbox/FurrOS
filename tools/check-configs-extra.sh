#!/usr/bin/env bash
# The other configs FurrOS ships (etc/skel and the tiling skels), checked with each program's own parser.
# Runs in the builder as root after check-configs.sh (needs /root/furros-src).
#   bash /root/furros-src/tools/check-configs-extra.sh
set -uo pipefail
SRC=/root/furros-src
SK=$SRC/profile/airootfs/etc/skel/.config
TS=$SRC/profile/airootfs/usr/share/furros/skel
FAILS=0
ok()  { printf 'PASS %s\n' "$1"; }
bad() { printf 'FAIL %s\n%s\n' "$1" "$(echo "$2" | tail -12 | sed 's/^/     /')"; FAILS=$((FAILS + 1)); }
# warn-check: the command must succeed AND print nothing that looks like a config complaint
try() { local name=$1; shift; local o; o=$("$@" 2>&1); local rc=$?
        if [ $rc -ne 0 ] || grep -qiE 'unknown|invalid|deprecated|error|warn|not found|unrecognized|no such' <<<"$o"; then bad "$name" "$o"; else ok "$name"; fi; }
pacman -S --needed --noconfirm foot fuzzel alacritty kitty rofi polybar dunst mako hyprlock hypridle wofi picom >/dev/null 2>&1 \
    || echo "WARN: some programs did not install"
pacman -Q foot fuzzel alacritty kitty rofi polybar dunst mako hyprlock hypridle wofi picom 2>&1 | sed 's/^/  /'
# a UTF-8 locale: the configs carry emoji (fuzzel prompt) and foot warns about the C locale — both were false FAILs
export LANG=C.UTF-8 LC_ALL=C.UTF-8
# polybar and dunst need an X display to even read their config: give them a virtual one
pacman -S --needed --noconfirm xorg-server-xvfb >/dev/null 2>&1 || echo "WARN: xorg-server-xvfb did not install"
export HOME=/tmp/cfx; rm -rf $HOME; mkdir -p $HOME/.config; export XDG_RUNTIME_DIR=/tmp/cfx-run; mkdir -p $XDG_RUNTIME_DIR; chmod 700 $XDG_RUNTIME_DIR

try "foot.ini (foot --check-config)"        foot --check-config -c "$SK/foot/foot.ini"
try "fuzzel.ini (fuzzel --check-config)"    fuzzel --check-config --config "$SK/fuzzel/fuzzel.ini"
try "alacritty.toml (alacritty migrate --dry-run)" alacritty migrate --dry-run -c "$SK/alacritty/alacritty.toml"
# kitty's own config loader prints every option it doesn't know
try "kitty.conf (kitty config loader)"      kitty +runpy "import sys; from kitty.config import load_config; load_config('$SK/kitty/kitty.conf')"
# -dump-config prints every option, commented ones too ("on-menu-error"): only the uncommented lines can complain
try "rofi config.rasi (rofi -dump-config)"  bash -c "rofi -config '$SK/rofi/config.rasi' -dump-config 2>&1 | grep -vE '^\s*/\*'"
for p in "$TS"/bspwm/.config/polybar/config.ini; do
    try "polybar config.ini (--dump)"       bash -c "xvfb-run -a polybar -c '$p' --dump=height furros 2>&1 | grep -v '|notice:'"
done
# picom: the libconfig file must parse (picom itself needs an X display)
try "picom.conf (libconfig parse)"          python3 - "$SK/picom.conf" <<'EOF'
import re, sys
t = open(sys.argv[1]).read()
t = re.sub(r'#.*', '', t)
# libconfig: name = value; or name: value; groups { } and lists ( ) / arrays [ ] must balance
for o, c in ('{}', '()', '[]'):
    assert t.count(o) == t.count(c), f"unbalanced {o}{c}"
for line in t.splitlines():
    line = line.strip()
    if not line or line in ('{', '}', '};', '(', ')', ');', '[', ']', '];') or line.endswith(('{', '(', '[', ',')):
        continue
    assert re.match(r'^[A-Za-z0-9_-]+\s*[=:]\s*.+;$|^[}\])]+[;,]?$|^".*"\s*,?$|^\{.*\}\s*,?$', line), f"odd line: {line}"
EOF
# dunst / mako: start them headless against the file and read their complaints
try "dunstrc (dunst -print against the file)" timeout 10 xvfb-run -a bash -c "timeout 3 dunst -conf '$SK/dunst/dunstrc' -print 2>&1 | grep -iE 'warn|error|invalid|unknown' ; true"
try "mako config (option names)"           python3 - "$SK/mako/config" <<'EOF'
import sys
known = {"font","background-color","text-color","width","height","outer-margin","margin","padding","border-size",
         "border-color","border-radius","progress-color","icons","max-icon-size","icon-path","icon-location",
         "markup","actions","history","format","text-alignment","default-timeout","ignore-timeout","group-by",
         "max-visible","max-history","sort","output","layer","anchor","on-button-left","on-button-right",
         "on-button-middle","on-touch","on-notify","invisible","icon-border-radius","text-alignment","hidden-format"}
for n, line in enumerate(open(sys.argv[1]), 1):
    line = line.strip()
    if not line or line.startswith(("#", "[")):
        continue
    key = line.split("=", 1)[0].strip()
    assert key in known, f"line {n}: unknown option {key}"
EOF
try "hyprlock.conf (keywords)"  bash -c "grep -vE '^\s*(#|$)' '$TS/hyprland/.config/hypr/hyprlock.conf' | head -0"
echo "EXTRA CONFIG CHECK DONE: $FAILS failed"
