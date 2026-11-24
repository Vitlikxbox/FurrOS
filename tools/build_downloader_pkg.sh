#!/usr/bin/env bash
# FurrOS Downloader as an Arch package (window + terminal version). Runs in the builder VM (as root), sources in
# /root/dl-src (src/downloader). makepkg runs as the "builder" user, like tools/build_repo.sh.
#   bash build_downloader_pkg.sh [--testers]   ->  /root/dl-out/furros-downloader[-testers]-<ver>-1-any.pkg.tar.zst
# --testers: the window looks in the private testers repository (needs the tester's GitHub token).
set -euo pipefail
SRC=/root/dl-src
NAME=furros-downloader
[[ ${1:-} == --testers ]] && NAME=furros-downloader-testers
B=/var/tmp/dl-pkg/$NAME  # not under /root: makepkg runs as the "builder" user
rm -rf "$B" && mkdir -p "$B" /root/dl-out
cp -r "$SRC" "$B/src-files"
rm -rf "$B/src-files/__pycache__" "$B/src-files/preview.png" "$B/src-files/furros_dl_build.py"
[[ $NAME == *-testers ]] && echo 'REPO = "Vitlikxbox/FurrOS-testers"' > "$B/src-files/furros_dl_build.py"
python - "$B" <<'EOF'
import sys
from PIL import Image
Image.open(sys.argv[1] + "/src-files/assets/paw.png").convert("RGBA").resize((256, 256)).save(sys.argv[1] + "/icon.png")
EOF
cat > "$B/PKGBUILD" <<EOF
pkgname=$NAME
pkgver=1.0.r$(date +%Y%m%d%H%M)
pkgrel=1
pkgdesc="Downloads the FurrOS ISO, checks it and writes it to a USB stick"
arch=(any)
url="https://furros.xyz"
license=(GPL-3.0-or-later)
depends=(python pyside6 polkit)
provides=(furros-downloader)
conflicts=(furros-downloader furros-downloader-testers)
options=(!strip !debug)
package() {
    local lib="\$pkgdir/usr/lib/furros-downloader"
    install -d "\$lib" "\$pkgdir/usr/bin"
    cp -r "$B/src-files/assets" "\$lib/"
    install -m644 "$B"/src-files/*.py "\$lib/"
    install -m755 "$B/src-files/furros-downloader" "\$pkgdir/usr/bin/furros-downloader"
    printf '#!/bin/sh\nexec python3 /usr/lib/furros-downloader/furros_downloader_gui.py "\$@"\n' > "\$pkgdir/usr/bin/furros-downloader-gui"
    chmod 755 "\$pkgdir/usr/bin/furros-downloader-gui"
    install -Dm644 "$B/icon.png" "\$pkgdir/usr/share/icons/hicolor/256x256/apps/furros-downloader.png"
    install -Dm644 /dev/stdin "\$pkgdir/usr/share/applications/furros-downloader.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=FurrOS Downloader
Comment=Download FurrOS and write it to a USB stick
Exec=furros-downloader-gui
Icon=furros-downloader
Categories=Utility;
Terminal=false
DESKTOP
}
EOF
chown -R builder "$B"
(cd "$B" && sudo -u builder makepkg -f --nodeps --noconfirm >/var/tmp/dl-pkg.log 2>&1) || { tail -20 /var/tmp/dl-pkg.log; exit 1; }
cp "$B"/*.pkg.tar.zst /root/dl-out/
ls -la /root/dl-out/$NAME-*.pkg.tar.zst
