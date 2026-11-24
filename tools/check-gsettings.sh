#!/usr/bin/env bash
# Every gsettings key furros-firstrun writes, checked against the schemas of today's Arch packages (downloaded,
# not installed): the key must exist and the value must be in its range (enums such as picture-options,
# accent-color). A key that no longer exists makes gsettings fail silently in firstrun (it runs quietly).
#   bash /root/furros-src/tools/check-gsettings.sh   (in the builder, as root)
set -uo pipefail
CONF=/tmp/pkgcheck-pacman.conf; DB=/tmp/pkgcheck-db
[ -f $CONF ] || { cp /etc/pacman.conf $CONF; mkdir -p $DB; }
pacman --config $CONF --dbpath $DB -Sy >/dev/null 2>&1
W=/tmp/gscheck; rm -rf $W; mkdir -p $W/cache $W/x $W/schemas
PKGS="gsettings-desktop-schemas cinnamon-desktop xapp mate-desktop marco mate-settings-daemon mate-control-center libmatekbd deepin-daemon dde-api"
for p in $PKGS; do
    pacman --config $CONF --dbpath $DB -Sw --noconfirm --nodeps --nodeps --cachedir $W/cache "$p" >/dev/null 2>&1 || echo "WARN: $p did not download"
done
for f in $W/cache/*.pkg.tar.zst; do bsdtar -xf "$f" -C $W/x 'usr/share/glib-2.0/schemas/*' 2>/dev/null; done
cp $W/x/usr/share/glib-2.0/schemas/* $W/schemas/ 2>/dev/null
glib-compile-schemas $W/schemas 2>&1 | tail -3
G="gsettings --schemadir $W/schemas"
FAILS=0
chk() { # schema key value
    if ! $G list-keys "$1" 2>/dev/null | grep -qx "$2"; then echo "FAIL $1 $2: no such key"; FAILS=$((FAILS+1)); return; fi
    local r; r=$($G range "$1" "$2" 2>/dev/null)
    if [[ $r == enum* ]] && ! grep -qx "'$3'" <<<"$(tail -n +2 <<<"$r")"; then
        echo "FAIL $1 $2: '$3' not in: $(tail -n +2 <<<"$r" | tr '\n' ' ')"; FAILS=$((FAILS+1)); return
    fi
    echo "PASS $1 $2 = $3"
}
for s in org.gnome.desktop.background org.cinnamon.desktop.background; do
    chk $s picture-uri x; chk $s picture-options zoom
done
chk org.gnome.desktop.background picture-uri-dark x
for s in org.gnome.desktop.interface org.cinnamon.desktop.interface; do
    chk $s gtk-theme x; chk $s icon-theme x; chk $s font-name x; chk $s cursor-theme x
done
chk org.gnome.desktop.interface color-scheme prefer-dark
chk org.gnome.desktop.interface accent-color pink
chk org.gnome.desktop.screensaver picture-uri x
chk org.gnome.desktop.sound theme-name x
chk org.cinnamon.desktop.sound theme-name x
chk org.x.apps.portal color-scheme prefer-dark
chk org.mate.background picture-filename x
chk org.mate.background picture-options zoom
chk org.mate.interface gtk-theme x
chk org.mate.interface icon-theme x
chk org.mate.Marco.general theme x
chk org.mate.peripherals-mouse cursor-theme x
chk org.mate.sound theme-name x
# Deepin 25 is set over D-Bus (org.deepin.dde.Appearance1), not gsettings
echo "GSETTINGS CHECK DONE: $FAILS failed"
