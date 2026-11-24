#!/usr/bin/env bash
# FurrOS Downloader for Windows: one FurrOS-Downloader.exe (PyInstaller, PySide6 from D:\FurrOS\venv).
#   bash tools/build_downloader_win.sh [--testers]    --testers: the window looks in the private testers repository
# Output: build-dl/out/FurrOS-Downloader[-testers].exe
set -euo pipefail
cd "$(dirname "$0")/.."
PY=venv/Scripts/python.exe
NAME=FurrOS-Downloader
W=build-dl/win
rm -rf "$W" && mkdir -p "$W" build-dl/out
cp src/downloader/furros_downloader_gui.py src/downloader/furros_dl_core.py src/downloader/furros_dl_i18n.py "$W/"
cp -r src/downloader/assets "$W/assets"
if [[ ${1:-} == --testers ]]; then
    echo 'REPO = "Vitlikxbox/FurrOS-testers"' > "$W/furros_dl_build.py"
    NAME=$NAME-testers
fi
"$PY" -c "from PIL import Image; Image.open('$W/assets/paw.png').convert('RGBA').save('$W/paw.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
cd "$W"
HERE=$(pwd -W)  # PyInstaller resolves paths against the .spec folder: give it absolute Windows paths
../../$PY -m PyInstaller --noconfirm --onefile --windowed --name "$NAME" --icon "$HERE/paw.ico" \
    --add-data "$HERE/assets;assets" --distpath ../out --workpath work --specpath work furros_downloader_gui.py
ls -la "../out/$NAME.exe"
