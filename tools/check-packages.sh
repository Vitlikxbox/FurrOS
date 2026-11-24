#!/usr/bin/env bash
# Every desktop of the installer, with every app bundle: can pacman resolve the whole package list today?
# Catches renamed/removed packages and conflicts before a real install does. Runs in the builder as root
# (needs /root/furros-src). Multilib is enabled in a private pacman.conf for the 32-bit gaming packages.
#   bash /root/furros-src/tools/check-packages.sh
set -uo pipefail
SRC=/root/furros-src
CONF=/tmp/pkgcheck-pacman.conf
DB=/tmp/pkgcheck-db
cp /etc/pacman.conf "$CONF"
grep -q '^\[multilib\]' "$CONF" || printf '\n[multilib]\nInclude = /etc/pacman.d/mirrorlist\n' >> "$CONF"
mkdir -p "$DB"
pacman --config "$CONF" --dbpath "$DB" -Sy >/dev/null 2>&1 || { echo "FAIL pacman -Sy"; exit 1; }
FAILS=0
apps=$(python3 -c "import sys; sys.path.insert(0,'$SRC/src/installer'); import catalog; print(' '.join(b['id'] for b in catalog.APP_BUNDLES if b['id'] not in ('browser-none','aur','snapshots')))")
for de in $(python3 -c "import sys; sys.path.insert(0,'$SRC/src/installer'); import catalog; print(' '.join(d['id'] for d in catalog.DESKTOPS))"); do
    for lang in ru pl; do
        plan=/tmp/pkgcheck-$de.json
        python3 - "$de" "$lang" "$apps" > "$plan" <<'EOF'
import json, sys
de, lang, apps = sys.argv[1], sys.argv[2], sys.argv[3].split()
print(json.dumps({"desktop": de, "apps": apps, "ui_lang": lang, "kernel": "linux", "filesystem": "btrfs",
                  "wallpaper_video": "anim-two.mp4", "encrypt": True}))
EOF
        pk=$(cd "$SRC/src/installer" && python3 backend.py --list-packages "$plan" 2>/dev/null | tail -1)
        # the FurrOS packages themselves come from [furros], not from Arch
        pk=$(tr ' ' '\n' <<<"$pk" | grep -v '^furros-' | grep -v '^$' | tr '\n' ' ')
        out=$(pacman --config "$CONF" --dbpath "$DB" -Sp --print-format '%n' $pk 2>&1 >/dev/null)
        if [ -n "$out" ]; then echo "FAIL $de ($lang): $out" | head -5; FAILS=$((FAILS + 1))
        else echo "PASS $de ($lang): $(wc -w <<<"$pk") packages resolve"; fi
    done
done
echo "PACKAGE CHECK DONE: $FAILS failed"
