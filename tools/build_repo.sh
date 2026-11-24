#!/usr/bin/env bash
# Builds the signed [furros] pacman repository from the staged airootfs (called by build.sh).
#   usage: build_repo.sh <airootfs> <out-dir>
# Packages: furros-keyring, furros-mirrorlist, furros-branding, furros-wallpapers, furros-academy,
# furros-drivers, plus the prebuilt AUR packages FurrOS ships (usr/share/furros/pkgs) and the online-only
# extras in /root/repo-extra.
# The repository is put on the ISO (usr/share/furros/repo, the installer installs from it) and into
# <out-dir> for the GitHub release (tools/publish_repo.sh).
set -euo pipefail
AIR=$1
OUT=$2
KEY=6D7CF8FE1B59637ACAA90BF66FA5E284DD02E46E
export GNUPGHOME=/root/furros-gpg
VER=1.0.r$(date -u +%Y%m%d%H%M)
B=/var/tmp/furros/pkgbuild
REPO_URL='https://github.com/Vitlikxbox/furros-repo/releases/download/$arch'
rm -rf "$B" "$OUT"
mkdir -p "$B" "$OUT"

# ---------------------------------------------------------------- what goes where
# every path the installer used to copy (build.sh writes usr/share/furros/files.list)
mapfile -t ALL < <(sed 's|^/||' "$AIR/usr/share/furros/files.list")
DRIVERS=(usr/lib/furros/drivers usr/local/bin/furros-drivers)
# names of the Pack (Boosty supporters) for «About FurrOS»: tiny, so it can be rebuilt on its own
STAYA=(usr/share/furros-staya)
ACADEMY=(usr/lib/furros/academy usr/local/bin/furros-academy usr/share/applications/furros-academy.desktop
         usr/local/bin/furros-welcome usr/share/applications/furros-welcome.desktop
         usr/local/bin/furros-about usr/local/bin/furros-lapa usr/share/applications/furros-about.desktop
         etc/xdg/autostart/furros-lapa.desktop)
# the «FurrOS Wallpapers» picker ships with the wallpapers it shows
WALLS=(usr/share/backgrounds/furros usr/lib/furros/wallpapers usr/local/bin/furros-set-wallpaper usr/local/bin/furros-wallpapers-app
       usr/share/applications/furros-wallpapers.desktop)
BRANDING=()
for p in "${ALL[@]}"; do
    case "$p" in
        usr/lib/furros/drivers*|usr/local/bin/furros-drivers|usr/lib/furros/academy*|usr/local/bin/furros-academy|\
        usr/local/bin/furros-welcome|usr/share/applications/furros-academy.desktop|usr/share/applications/furros-welcome.desktop|usr/share/backgrounds/furros*|\
        usr/local/bin/furros-about|usr/local/bin/furros-lapa|usr/share/applications/furros-about.desktop|etc/xdg/autostart/furros-lapa.desktop|usr/share/furros-staya*|\
        usr/lib/furros/wallpapers*|usr/local/bin/furros-set-wallpaper|usr/local/bin/furros-wallpapers-app|usr/share/applications/furros-wallpapers.desktop) ;;
        usr/share/wallpapers/FurrOS*) WALLS+=("$p") ;;
        *) BRANDING+=("$p") ;;
    esac
done

# ---------------------------------------------------------------- keyring + mirrorlist files
KR=$B/keyring-files
mkdir -p "$KR"
gpg --export "$KEY" > "$KR/furros.gpg"
echo "$KEY:4:" > "$KR/furros-trusted"
: > "$KR/furros-revoked"
echo "Server = $REPO_URL" > "$B/mirrorlist.txt"

# ---------------------------------------------------------------- PKGBUILDs
# copy <paths...> from the airootfs into $pkgdir, keeping directories, links and modes
mkpkg() {  # name desc depends... -- paths...
    local name=$1 desc=$2; shift 2
    local deps=() paths=()
    while [[ $# -gt 0 && $1 != -- ]]; do deps+=("'$1'"); shift; done
    [[ ${1:-} == -- ]] && shift
    paths=("$@")
    local d=$B/$name
    mkdir -p "$d"
    printf '%s\n' "${paths[@]}" > "$d/paths"
    cat > "$d/PKGBUILD" <<EOF
pkgname=$name
pkgver=$VER
pkgrel=1
pkgdesc="$desc"
arch=(any)
url="https://furros.xyz"
license=(GPL-3.0-or-later)
depends=(${deps[*]})
options=(!strip !debug)
package() {
    while read -r p; do
        [[ -z \$p ]] && continue
        mkdir -p "\$pkgdir/\$(dirname "\$p")"
        cp -a "$AIR/\$p" "\$pkgdir/\$p"
    done < "$d/paths"
    # executables (Windows checkouts lose the x bit)
    find "\$pkgdir" -path '*/usr/local/bin/*' -type f -exec chmod 755 {} +
    find "\$pkgdir" -name '*.py' -type f -exec sh -c 'head -c2 "\$1" | grep -q "#!" && chmod 755 "\$1"' _ {} \;
    find "\$pkgdir" -name __pycache__ -prune -exec rm -rf {} +
    rm -f "\$pkgdir/usr/share/backgrounds/furros/current.png"   # the installer points it at the chosen wallpaper
    rm -rf "\$pkgdir/usr/share/furros/pkgs" "\$pkgdir/usr/share/furros/repo" "\$pkgdir/usr/share/furros/files.list"
}
EOF
}

# keyring (its own PKGBUILD: files come from $KR, populated after install)
mkdir -p "$B/furros-keyring"
cat > "$B/furros-keyring/furros-keyring.install" <<'EOF'
post_install() {
    if usr/bin/pacman-key -l >/dev/null 2>&1; then
        usr/bin/pacman-key --populate furros
    fi
}
post_upgrade() { post_install; }
EOF
cat > "$B/furros-keyring/PKGBUILD" <<EOF
pkgname=furros-keyring
pkgver=$VER
pkgrel=1
pkgdesc="FurrOS package signing key"
arch=(any)
url="https://furros.xyz"
license=(GPL-3.0-or-later)
install=furros-keyring.install
package() {
    install -Dm644 "$KR/furros.gpg" "\$pkgdir/usr/share/pacman/keyrings/furros.gpg"
    install -Dm644 "$KR/furros-trusted" "\$pkgdir/usr/share/pacman/keyrings/furros-trusted"
    install -Dm644 "$KR/furros-revoked" "\$pkgdir/usr/share/pacman/keyrings/furros-revoked"
}
EOF
mkdir -p "$B/furros-mirrorlist"
cat > "$B/furros-mirrorlist/PKGBUILD" <<EOF
pkgname=furros-mirrorlist
pkgver=$VER
pkgrel=1
pkgdesc="Where pacman downloads FurrOS packages from"
arch=(any)
url="https://furros.xyz"
license=(GPL-3.0-or-later)
backup=(etc/pacman.d/furros-mirrorlist)
package() {
    install -Dm644 "$B/mirrorlist.txt" "\$pkgdir/etc/pacman.d/furros-mirrorlist"
}
EOF
mkpkg furros-drivers "FurrOS: detect and install graphics drivers (furros-drivers)" python pciutils -- "${DRIVERS[@]}"
mkpkg furros-staya "The FurrOS Pack: names of the supporters shown in About FurrOS" --  "${STAYA[@]}"
mkpkg furros-academy "Lapa's School: the FurrOS built-in Linux textbook" python pyside6 qt6-webengine furros-staya -- "${ACADEMY[@]}"
mkpkg furros-wallpapers "FurrOS wallpapers, static and animated, and the FurrOS Wallpapers picker" python pyside6 polkit -- "${WALLS[@]}"
# noto-fonts-cjk: existing installs get Japanese/Chinese/Korean fonts with the next update (tester report 22.11)
mkpkg furros-branding "FurrOS look: themes, boot splash, login screen, fonts, settings" bash noto-fonts-cjk -- "${BRANDING[@]}"

# ---------------------------------------------------------------- build, sign, index
chown -R builder: "$B"
for d in "$B"/furros-*/; do
    [[ -f $d/PKGBUILD ]] || continue
    (cd "$d" && sudo -u builder makepkg -f --nodeps --noconfirm >/dev/null)
    cp "$d"/*.pkg.tar.zst "$OUT/"
done
# FurrBoot (bootloader/furros: PKGBUILD + the prebuilt furrboot.efi, Rust's UEFI target isn't in Arch)
FB_SRC=$(dirname "$0")/../bootloader/furros
if [[ -f $FB_SRC/PKGBUILD && -f $FB_SRC/furrboot.efi ]]; then
    rm -rf "$B/furrboot" && cp -r "$FB_SRC" "$B/furrboot" && sed -i 's/\r$//' "$B/furrboot"/furrboot-* "$B/furrboot"/*.hook "$B/furrboot"/PKGBUILD
    chown -R builder: "$B/furrboot"
    (cd "$B/furrboot" && sudo -u builder makepkg -f --nodeps --noconfirm >/dev/null)
    cp "$B"/furrboot/furrboot-*.pkg.tar.zst "$OUT/"
else
    echo "build_repo: no bootloader/furros (FurrBoot): the ISO installs GRUB only" >&2
fi
cp "$AIR"/usr/share/furros/pkgs/*.pkg.tar.zst "$OUT/" 2>/dev/null || true
# big prebuilt extras (legacy NVIDIA driver): online repository only, build.sh keeps them off the ISO
cp /root/repo-extra/*.pkg.tar.zst "$OUT/" 2>/dev/null || true
cd "$OUT"
for f in *.pkg.tar.zst; do
    gpg --batch --yes --detach-sign --no-armor -u "$KEY" "$f"
done
repo-add -q --sign --key "$KEY" furros.db.tar.zst *.pkg.tar.zst
# GitHub release assets can't be symlinks: real copies under the names pacman asks for
for n in furros.db furros.files; do
    for ext in "" .sig; do
        [[ -L $n$ext ]] && cp --remove-destination "$(readlink -f "$n$ext")" "$n$ext"
    done
done
ls -la "$OUT"
