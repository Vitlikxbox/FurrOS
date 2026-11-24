#!/usr/bin/env bash
# Checks the shipped desktop configs with each program's own validator, without installing FurrOS.
# Runs in the builder as root (needs the repo checkout in /root/furros-src). Two variants per config:
# the stock file, and the file after the installer's Super+Space fix (layout switch on Super+Space).
#   usage (in the builder): bash /root/furros-src/tools/check-configs.sh
set -uo pipefail
SRC=/root/furros-src
SK=$SRC/profile/airootfs/usr/share/furros/skel
W=/tmp/cfgcheck
FAILS=0
ok()   { printf 'PASS %s\n' "$1"; }
bad()  { printf 'FAIL %s\n%s\n' "$1" "$(echo "$2" | tail -15 | sed 's/^/     /')"; FAILS=$((FAILS + 1)); }
try()  { local name=$1; shift; local o; if o=$("$@" 2>&1); then ok "$name"; else bad "$name" "$o"; fi; }

pacman -S --noconfirm startup-notification >/dev/null 2>&1
pacman -S --needed --noconfirm sway i3-wm awesome qtile hyprland niri bspwm sxhkd polybar waybar \
    desktop-file-utils python lua >/dev/null 2>&1 || echo "WARN: some validator packages did not install"
pacman -Q sway i3-wm awesome qtile hyprland niri waybar 2>&1 | sed 's/^/  /'

# the installer's Super+Space edits (same expressions as SUPER_SPACE_BINDS in src/installer/backend.py)
declare -A FREE=(
  [niri/config.kdl]='/^\s*Mod+Space {/d'
  [hypr/hyprland.lua]='/^hl\.bind(mod \.\. " + Space"/d'
  [sway/config]='/^bindsym \$mod+space exec/d'
  [i3/config]='/^bindsym \$mod+space exec/d'
  [qtile/config.py]='/Key(\[mod\], "space"/d'
  [sxhkd/sxhkdrc]='s/^super + {d,space}$/super + d/'
)

for variant in stock superspace; do
    toggle=grp:alt_shift_toggle; [[ $variant == superspace ]] && toggle=grp:win_space_toggle
    H=$W/$variant; rm -rf "$H"; mkdir -p "$H/.config/furros"
    for d in "$SK"/*/; do cp -a "$d/." "$H/"; done
    # files the installer writes next to the configs (they are included from them)
    printf 'hl.config({ input = { kb_layout = "us,ru", kb_options = "%s" } })\n' "$toggle" > "$H/.config/furros/keyboard-hypr.lua"
    printf 'input type:keyboard {\n    xkb_layout "us,ru"\n    xkb_options "%s"\n}\n' "$toggle" > "$H/.config/furros/keyboard-sway.conf"
    sed -i "s/^\( *\)options \"grp:alt_shift_toggle\"/\1options \"$toggle\"/" "$H/.config/niri/config.kdl"
    # awesome: the installer builds rc.lua from the stock one
    rc=$H/.config/awesome/rc.lua; cp /etc/xdg/awesome/rc.lua "$rc"
    sed -i 's|beautiful.init(.*)|beautiful.init(os.getenv("HOME") .. "/.config/awesome/furros-theme.lua")|; s|terminal = "xterm"|terminal = "alacritty"|' "$rc"
    printf '\nawful.spawn.once("furros-firstrun")\nawful.spawn.once("picom -b")\nawful.spawn.once("nm-applet")\n' >> "$rc"
    if [[ $variant == superspace ]]; then
        for rel in "${!FREE[@]}"; do sed -i "${FREE[$rel]}" "$H/.config/$rel"; done
        sed -i '/awful\.layout\.inc( *1)/ s/{ *modkey, *}, *"space"/{ modkey, "Mod1" }, "space"/' "$rc"
    fi
    export HOME=$H XDG_CONFIG_HOME=$H/.config XDG_RUNTIME_DIR=/tmp/xdg-$variant; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
    echo "== $variant ($toggle)"
    try "$variant sway -C"            sway -C -c "$H/.config/sway/config"
    try "$variant i3 -C"              i3 -C -c "$H/.config/i3/config"
    try "$variant niri validate"      niri validate -c "$H/.config/niri/config.kdl"
    mkdir -p /tmp/xdg-hb-$variant; chown builder: /tmp/xdg-hb-$variant; chmod 700 /tmp/xdg-hb-$variant; chmod -R a+rX "$H"
    try "$variant Hyprland --verify-config" runuser -u builder -- env HOME="$H" XDG_CONFIG_HOME="$H/.config" XDG_RUNTIME_DIR=/tmp/xdg-hb-$variant Hyprland --verify-config -c "$H/.config/hypr/hyprland.lua"
    try "$variant awesome -k"         awesome -k -c "$rc"
    try "$variant qtile check"        qtile check -c "$H/.config/qtile/config.py"
    try "$variant bspwmrc syntax"     bash -n "$H/.config/bspwm/bspwmrc"
    for j in "$H"/.config/waybar/config.jsonc; do
        try "$variant waybar json"    python3 -c 'import json,re,sys; t=open(sys.argv[1]).read(); t=re.sub(r"(?m)^\s*//.*$","",t); t=re.sub(r",(\s*[}\]])",r"\1",t); json.loads(t)' "$j"
    done
    # Super+Space must not open anything in the superspace variant
    if [[ $variant == superspace ]]; then
        # the last alternative is Hyprland's Lua: hl.bind(mod .. " + Space", ...)
        left=$(grep -rniE 'mod\+space|Mod\+Space|"space".*(fuzzel|wofi|rofi|drun|menu)|\$mod\+space exec|\+ space"' \
               "$H/.config/sway/config" "$H/.config/i3/config" "$H/.config/niri/config.kdl" "$H/.config/hypr/hyprland.lua" \
               "$H/.config/qtile/config.py" 2>/dev/null | grep -viE 'shift|ctrl|alt|#' )
        left+=$(grep -nE '^super \+ (\{[^}]*space|space)' "$H/.config/sxhkd/sxhkdrc")
        [[ -z $left ]] && ok "superspace: no Super+Space launcher left" || bad "superspace: Super+Space still bound" "$left"
    fi
done
# shared files every desktop gets
for f in "$SRC"/profile/airootfs/etc/skel/.config/autostart/*.desktop "$SRC"/profile/airootfs/etc/xdg/autostart/*.desktop; do
    [[ -f $f ]] && try "desktop file ${f##*/}" desktop-file-validate "$f"
done
echo "CONFIG CHECK DONE: $FAILS failed"
