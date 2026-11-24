#!/usr/bin/env bash
# Deepin's window manager vs. today's KDE libraries: does every symbol deepin-kwin imports from kscreenlocker and
# kglobalacceld still exist? Catches the 18.11 breakage (Arch deepin-kwin 6.0.8-12 vs kscreenlocker 6.8:
# "symbol lookup error", DDE left without a window manager) before a user does. Runs in the builder as root,
# like check-packages.sh; downloads only the packages themselves (no dependencies) into a private pacman db.
#   bash /root/furros-src/tools/check-kwin-abi.sh            exit 1 = our shipped build is broken
# Checked:
#   * furros-deepin-kwin from /root/pkgs (what FurrOS ships)  -> must PASS
#   * Arch's deepin-kwin                                      -> informational: once it passes again, Arch has
#     rebuilt it and packages/furros-deepin-kwin can be retired
set -uo pipefail
W=/tmp/kwin-abi
DB=$W/db
rm -rf "$W/x" "$W/pkgs"
mkdir -p "$DB" "$W/pkgs"
pacman --dbpath "$DB" -Sy >/dev/null 2>&1 || { echo "FAIL pacman -Sy"; exit 1; }
pacman --dbpath "$DB" -Sw --cachedir "$W/pkgs" --noconfirm --nodeps --nodeps kscreenlocker kglobalacceld deepin-kwin >/dev/null 2>&1 \
    || { echo "FAIL download kscreenlocker/kglobalacceld/deepin-kwin"; exit 1; }
ver() { basename "$1" | sed -E 's/^(.*)-([^-]+-[^-]+)-x86_64\.pkg\.tar\.zst$/\1 \2/'; }

# what today's libraries export
mkdir -p "$W/x/libs"
for p in "$W"/pkgs/kscreenlocker-*.pkg.tar.zst "$W"/pkgs/kglobalacceld-*.pkg.tar.zst; do
    bsdtar -xf "$p" -C "$W/x/libs"
    echo "lib: $(ver "$p")"
done
nm -D --defined-only "$W"/x/libs/usr/lib/libKScreenLocker.so.*.* "$W"/x/libs/usr/lib/libKGlobalAccelD.so.*.* 2>/dev/null \
    | awk '{print $3}' | sort -u > "$W/have"

check() {  # check <label> <package file> -> 0 when every ScreenLocker/KGlobalAccelD import resolves
    local label=$1 pkg=$2 d
    d=$W/x/$label
    mkdir -p "$d"
    bsdtar -xf "$pkg" -C "$d"
    find "$d/usr/lib" "$d/usr/bin" -type f \( -name 'libkwin*.so*' -o -name kwin_x11 -o -name kwin_wayland \) 2>/dev/null \
        | xargs -r nm -D --undefined-only 2>/dev/null | awk '{print $2}' | grep -E 'ScreenLocker|KGlobalAccelD' | sort -u > "$d.need"
    local miss
    miss=$(comm -23 "$d.need" "$W/have")
    if [[ -z $miss ]]; then
        echo "PASS $label ($(ver "$pkg")): $(wc -l < "$d.need") kscreenlocker/kglobalacceld symbols resolve"
        return 0
    fi
    echo "FAIL $label ($(ver "$pkg")): missing in today's libraries:"
    echo "$miss" | c++filt | sed 's/^/       /'
    return 1
}

RC=0
ours=$(ls /root/pkgs/furros-deepin-kwin-*.pkg.tar.zst 2>/dev/null | sort -V | tail -1)
if [[ -n $ours ]]; then
    check furros-deepin-kwin "$ours" || RC=1
else
    echo "FAIL furros-deepin-kwin: no package in /root/pkgs (build packages/furros-deepin-kwin)"; RC=1
fi
if check arch-deepin-kwin "$(ls "$W"/pkgs/deepin-kwin-*.pkg.tar.zst | head -1)"; then
    echo "NOTE Arch's deepin-kwin loads with today's KDE libraries again: furros-deepin-kwin can be retired"
else
    echo "NOTE Arch's deepin-kwin is still broken: keep shipping furros-deepin-kwin"
fi
echo "KWIN ABI CHECK DONE: $([[ $RC == 0 ]] && echo ok || echo FAILED)"
exit $RC
