#!/usr/bin/env bash
# FurrOS Downloader for Linux as an AppImage. Runs in the builder VM (as root).
# Built inside an Ubuntu 22.04 chroot (/root/jammy, glibc 2.35): an AppImage only runs on systems with the same or a
# newer glibc than the one it was built on (docs.appimage.org, best practices), and the builder's Arch is too new.
# The chroot needs /root/jammy/root/venv (PySide6-Essentials + pyinstaller) and the sources unpacked in /root/jammy/root/dl.
#   bash build_downloader_appimage.sh NAME     ->  /root/dl-out/NAME-x86_64.AppImage
set -euo pipefail
NAME=${1:-FurrOS-Downloader}
J=/root/jammy
TOOL=/root/appimagetool-1.9.1-x86_64.AppImage
[ -x $TOOL ] || { curl -fsSL -o $TOOL https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage; chmod +x $TOOL; }
for m in proc sys dev; do mountpoint -q $J/$m || mount --rbind /$m $J/$m; done
# certifi: a CA bundle of its own, for systems that keep theirs where Ubuntu's Python doesn't look (issue #5)
chroot $J /bin/bash -c "set -e; cd /root/dl; rm -rf build dist
    /root/venv/bin/pip install -q certifi || echo '! certifi not installed: no CA bundle of its own' >&2
    /root/venv/bin/pyinstaller --noconfirm --onedir --windowed --hidden-import certifi --name furros-downloader \
        --add-data assets:assets furros_downloader_gui.py >/root/pyinstaller.log 2>&1 || { tail -20 /root/pyinstaller.log; exit 1; }"
A=/root/dl-appdir
rm -rf $A && mkdir -p $A/usr/lib $A/usr/share/icons/hicolor/256x256/apps
cp -r $J/root/dl/dist/furros-downloader $A/usr/lib/
python - <<'EOF'
from PIL import Image
Image.open("/root/jammy/root/dl/assets/paw.png").convert("RGBA").resize((256, 256)).save("/root/dl-appdir/furros-downloader.png")
EOF
cp $A/furros-downloader.png $A/usr/share/icons/hicolor/256x256/apps/
cat > $A/furros-downloader.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=FurrOS Downloader
Comment=Download FurrOS and write it to a USB stick
Exec=furros-downloader
Icon=furros-downloader
Categories=Utility;
Terminal=false
EOF
cat > $A/AppRun <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/furros-downloader/furros-downloader" "$@"
EOF
chmod +x $A/AppRun
mkdir -p /root/dl-out
ARCH=x86_64 $TOOL --appimage-extract-and-run $A /root/dl-out/$NAME-x86_64.AppImage >/root/appimagetool.log 2>&1 || { tail -20 /root/appimagetool.log; exit 1; }
ls -la /root/dl-out/$NAME-x86_64.AppImage
