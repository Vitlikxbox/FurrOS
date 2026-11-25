#!/usr/bin/env bash
# Builds FurrOS.iso on an Arch machine (the builder VM).
#   usage: build.sh /root/furros-src
set -euo pipefail
SRC=${1:-/root/furros-src}
WORK=/var/tmp/furros
PROFILE=$WORK/profile
AIR=$PROFILE/airootfs

log() { printf '\e[38;2;127;240;240m🐾 %s\e[0m\n' "$*"; }

# a mirror that stopped syncing quietly bakes weeks-old packages (and missing security fixes) into the ISO:
# drop every mirror more than 3 days behind before building (backup in mirrorlist.furros-bak)
log "Mirror freshness"
now=$(date +%s)
cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.furros-bak
while read -r url; do
    base=${url%%\$repo*}
    # an unreachable mirror must not kill the build (set -e + pipefail): it just counts as stale;
    # an HTML error page full of digits is not a timestamp either
    stamp=$(curl -sf -m 15 "${base}lastupdate" | tr -dc 0-9) || stamp=
    [[ ${#stamp} -le 12 ]] || stamp=
    if [[ -z $stamp ]] || (( now - stamp > 3 * 86400 )); then
        log "  dropping stale mirror ${base} (lastupdate ${stamp:-?})"
        grep -vF "Server = $url" /etc/pacman.d/mirrorlist > /tmp/mirrorlist.new || true
        cat /tmp/mirrorlist.new > /etc/pacman.d/mirrorlist
    fi
done < <(sed -n 's/^Server = //p' /etc/pacman.d/mirrorlist)
grep -q '^Server' /etc/pacman.d/mirrorlist || { echo "no fresh mirror left" >&2; cp /etc/pacman.d/mirrorlist.furros-bak /etc/pacman.d/mirrorlist; exit 1; }
pacman -Syy --noconfirm >/dev/null

log "Fresh releng profile"
rm -rf "$PROFILE" "$WORK/work"
mkdir -p "$WORK/out"
cp -r /usr/share/archiso/configs/releng "$PROFILE"
# slow links: never give up on a download, fewer parallel streams
sed -i 's/^#\?ParallelDownloads.*/ParallelDownloads = 4/; /^\[options\]/a DisableDownloadTimeout' "$PROFILE/pacman.conf"

log "Overlay FurrOS files"
cp -rT "$SRC/profile/airootfs" "$AIR"
mkdir -p "$AIR/usr/lib/furros"
cp -r "$SRC/src/installer" "$AIR/usr/lib/furros/installer"
cp -r "$SRC/src/academy" "$AIR/usr/lib/furros/academy"
cp -r "$SRC/src/drivers" "$AIR/usr/lib/furros/drivers"
cp -r "$SRC/src/wallpapers" "$AIR/usr/lib/furros/wallpapers"
find "$AIR/usr/lib/furros" -name __pycache__ -prune -exec rm -rf {} +
# Windows checkouts may carry CRLF: normalize every text file
grep -rIl $'\r' "$AIR" "$PROFILE/packages.x86_64" 2>/dev/null | xargs -r sed -i 's/\r$//'
cp "$SRC/profile/packages.extra" /tmp/furros-packages.extra
sed -i 's/\r$//' /tmp/furros-packages.extra

log "Terms of use as a file"
python3 - "$AIR/usr/lib/furros/installer" "$AIR/usr/share/furros/TERMS.md" <<'EOF'
import re, sys
sys.path.insert(0, sys.argv[1])
from terms import TERMS
md = []
for lang in ("ru", "en", "pl", "es"):
    t = TERMS[lang]
    t = re.sub(r"<h3>(.*?)</h3>", r"# \1", t)
    t = re.sub(r"</?b>", "**", t)
    t = re.sub(r"</?code>", "`", t)
    t = re.sub(r"</?p>", "", t)
    md.append(t.strip())
open(sys.argv[2], "w").write("\n\n---\n\n".join(md) + "\n")
EOF

log "Animated wallpapers and prebuilt packages"
mkdir -p "$AIR/usr/share/backgrounds/furros/animated" "$AIR/usr/share/furros/pkgs"
cp /root/videos/out/anim-*.mp4 /root/videos/out/anim-*.png "$AIR/usr/share/backgrounds/furros/animated/"
cp /root/pkgs/*.pkg.tar.zst "$AIR/usr/share/furros/pkgs/"

log "FurrOS cursor theme (Breeze with FurrOS accents; rendered once, then cached)"
# index.theme is written last, so a render cut short (power loss) is redone instead of shipped half-done
if [[ ! -f /root/cursor-out/white/FurrOS/index.theme ]]; then
    rm -rf /root/cursor-out/white
    mkdir -p /root/cursor-out/white
    python3 "$SRC/tools/make_cursor.py" --build white /root/cursor-out/white
fi
mkdir -p "$AIR/usr/share/icons"
rm -rf "$AIR/usr/share/icons/FurrOS"
cp -a /root/cursor-out/white/FurrOS "$AIR/usr/share/icons/FurrOS"

log "Wallpaper link, services"
ln -sf furros-lapa-wave.png "$AIR/usr/share/backgrounds/furros/current.png"
SD=$AIR/etc/systemd/system
mkdir -p "$SD/multi-user.target.wants"
ln -sf /usr/lib/systemd/system/sddm.service "$SD/display-manager.service"
ln -sf /usr/lib/systemd/system/NetworkManager.service "$SD/multi-user.target.wants/NetworkManager.service"
ln -sf /etc/systemd/system/furros-liveuser.service "$SD/multi-user.target.wants/furros-liveuser.service"
ln -sf /usr/lib/systemd/system/vboxservice.service "$SD/multi-user.target.wants/vboxservice.service"
# Deepin (DDE) does not pull xdg-desktop-autostart.target: start firstrun with its own session target
mkdir -p "$AIR/etc/systemd/user/dde-session-core.target.wants"
ln -sf ../furros-firstrun-dde.service "$AIR/etc/systemd/user/dde-session-core.target.wants/furros-firstrun-dde.service"
# Deepin without a window manager (kwin_x11 crashing) gets a dialog instead of silently broken windows
ln -sf ../furros-dde-wm-guard.service "$AIR/etc/systemd/user/dde-session-core.target.wants/furros-dde-wm-guard.service"
# daily "updates are waiting" reminder for every user
mkdir -p "$AIR/etc/systemd/user/timers.target.wants"
ln -sf ../furros-update-check.timer "$AIR/etc/systemd/user/timers.target.wants/furros-update-check.timer"
# NetworkManager replaces releng's networkd + iwd
rm -f "$SD/multi-user.target.wants/systemd-networkd.service" "$SD/multi-user.target.wants/iwd.service" \
      "$SD/sockets.target.wants/systemd-networkd.socket" \
      "$SD/network-online.target.wants/systemd-networkd-wait-online.service" \
      "$SD/systemd-networkd-wait-online.service.d" -r 2>/dev/null || true
rm -f "$SD/multi-user.target.wants/systemd-networkd.service"
# security: releng starts sshd for remote installs, but the live user furry/furry has passwordless sudo,
# so anyone on the same network could log in as root. FurrOS installs locally: no SSH server in the live system,
# and no LLMNR (name spoofing on public Wi-Fi)
rm -f "$SD/multi-user.target.wants/sshd.service"
rm -f "$AIR/etc/ssh/sshd_config.d/10-archiso.conf"
mkdir -p "$AIR/etc/systemd/resolved.conf.d"
printf '[Resolve]\nLLMNR=no\nMulticastDNS=no\n' > "$AIR/etc/systemd/resolved.conf.d/80-furros-privacy.conf"

log "Identity"
echo furros > "$AIR/etc/hostname"
printf 'LANG=ru_RU.UTF-8\n' > "$AIR/etc/locale.conf"
printf 'KEYMAP=us\nFONT=cyr-sun16\n' > "$AIR/etc/vconsole.conf"
cat > "$AIR/etc/pacman.d/hooks/40-locale-gen.hook" <<'EOF'
[Trigger]
Operation = Install
Type = Package
Target = glibc

[Action]
Description = Generating FurrOS locales (en, ru, pl, es)...
When = PostTransaction
Depends = glibc
Depends = sh
Exec = /bin/sh -c "printf 'en_US.UTF-8 UTF-8\nru_RU.UTF-8 UTF-8\npl_PL.UTF-8 UTF-8\nes_ES.UTF-8 UTF-8\n' >> /etc/locale.gen && locale-gen"
EOF
sed -i 's/^HOOKS=(base udev /HOOKS=(base udev plymouth /' "$AIR/etc/mkinitcpio.conf.d/archiso.conf"
grep -q plymouth "$AIR/etc/mkinitcpio.conf.d/archiso.conf" || { echo "plymouth hook not added"; exit 1; }

log "Packages"
sed -i '/^virtualbox-guest-utils-nox$/d' "$PROFILE/packages.x86_64"
grep -v '^#' /tmp/furros-packages.extra | sed '/^$/d' >> "$PROFILE/packages.x86_64"
sort -u -o "$PROFILE/packages.x86_64" "$PROFILE/packages.x86_64"

log "profiledef"
P=$PROFILE/profiledef.sh
sed -i 's/^iso_name=.*/iso_name="furros"/; s/^iso_publisher=.*/iso_publisher="FurrOS <https:\/\/furros.xyz>"/;
        s/^iso_application=.*/iso_application="FurrOS Live"/; s/^iso_version=.*/iso_version="1.0"/;
        s/^iso_label=.*/iso_label="FURROS_10"/' "$P"
cat >> "$P" <<'EOF'
file_permissions+=(
  ["/usr/local/bin/furros-brand"]="0:0:755"
  ["/usr/local/bin/furros-firstrun"]="0:0:755"
  ["/usr/local/bin/furros-wallpaper"]="0:0:755"
  ["/usr/local/bin/furros-dde-wm-guard"]="0:0:755"
  ["/usr/local/bin/furros-set-wallpaper"]="0:0:755"
  ["/usr/local/bin/furros-wallpapers-app"]="0:0:755"
  ["/usr/local/bin/furros-pacman-hint"]="0:0:755"
  ["/usr/local/bin/furros-hypr-lua"]="0:0:755"
  ["/usr/lib/furros/wallpapers/furros_wallpapers.py"]="0:0:755"
  ["/usr/local/bin/furros-liveuser"]="0:0:755"
  ["/usr/local/bin/furros-installer"]="0:0:755"
  ["/usr/local/bin/furros-labwc-fix"]="0:0:755"
  ["/usr/local/bin/furros-academy"]="0:0:755"
  ["/usr/local/bin/furros-welcome"]="0:0:755"
  ["/usr/local/bin/furros-about"]="0:0:755"
  ["/usr/local/bin/furros-lapa"]="0:0:755"
  ["/usr/lib/furros/academy/furros_about.py"]="0:0:755"
  ["/usr/lib/furros/academy/furros_lapa.py"]="0:0:755"
  ["/etc/grub.d/11_furros_safe_graphics"]="0:0:755"
  ["/etc/grub.d/45_furros_power"]="0:0:755"
  ["/usr/lib/furros/academy/furros_welcome.py"]="0:0:755"
  ["/usr/local/bin/furros-drivers"]="0:0:755"
  ["/usr/local/bin/furros-update"]="0:0:755"
  ["/usr/local/bin/furros-gpu-soft"]="0:0:755"
  ["/usr/local/bin/furros-desktop"]="0:0:755"
  ["/usr/local/bin/furros-picom"]="0:0:755"
  ["/usr/lib/systemd/user-environment-generators/60-furros-vm-graphics"]="0:0:755"
  ["/usr/lib/furros/drivers/furros_hw.py"]="0:0:755"
  ["/usr/lib/furros/installer/backend.py"]="0:0:755"
  ["/usr/lib/furros/installer/furros_installer.py"]="0:0:755"
  ["/usr/lib/furros/academy/furros_academy.py"]="0:0:755"
  ["/usr/share/furros/skel/bspwm/.config/bspwm/bspwmrc"]="0:0:755"
)
EOF

log "Boot menus"
for f in $(grep -rl "Arch Linux" "$PROFILE"/efiboot "$PROFILE"/grub "$PROFILE"/syslinux 2>/dev/null); do
    sed -i 's/Arch Linux/FurrOS/g' "$f"
done
for f in $(grep -rl "archisobasedir=" "$PROFILE"/efiboot "$PROFILE"/grub "$PROFILE"/syslinux 2>/dev/null); do
    sed -i '/archisobasedir=/ { /quiet splash/! s/$/ quiet splash/ }' "$f"
done
cp "$SRC/profile/airootfs/usr/share/furros/splash.png" "$PROFILE/syslinux/splash.png" 2>/dev/null || true
# Normal graphics by default, plus a separate "safe graphics" (nomodeset) entry in every live menu (UEFI
# systemd-boot/FurrBoot, BIOS syslinux, the GRUB menus). nomodeset on every entry gave a black screen on old
# built-in graphics booted from BIOS (issue #10: Core 2 Duo laptop), while a new NVIDIA card may need it.
# English titles: firmware fonts often have no Cyrillic. The installed system writes its own command line.
python3 - "$PROFILE" <<'EOF'
import re, sys
from pathlib import Path
prof = Path(sys.argv[1])
SUFFIX = " - safe graphics"

def nomodeset(line):
    return line if " nomodeset" in line else line.rstrip("\n") + " nomodeset\n"

# systemd-boot / FurrBoot: a copy of the main entry (01-archiso-linux.conf stays the default in loader.conf)
main = prof / "efiboot/loader/entries/01-archiso-linux.conf"
if main.exists():
    out = []
    for line in main.read_text().splitlines(keepends=True):
        if line.startswith("title"):
            line = line.rstrip("\n") + SUFFIX + "\n"
        elif line.startswith("sort-key"):
            line = "sort-key 03\n"  # after the main and the speech entries
        elif line.startswith("options") and "archisobasedir=" in line:
            line = nomodeset(line)
        out.append(line)
    (prof / "efiboot/loader/entries/03-archiso-safe-graphics.conf").write_text("".join(out))

# syslinux: the first LABEL block that boots the live system (not the speech one), copied right after itself
sl = prof / "syslinux/archiso_sys-linux.cfg"
if sl.exists():
    text = sl.read_text()
    blocks = re.split(r"(?m)^(?=LABEL )", text)
    for i, b in enumerate(blocks):
        if b.startswith("LABEL ") and "archisobasedir=" in b and "speech" not in b.lower():
            # the comment at the end of the block ("# Accessibility boot option") heads the next block: keep it there
            m = re.search(r"(?:\n[ \t]*(?:#[^\n]*)?)+\Z", b)
            body, tail = (b[:m.start()], b[m.start():]) if m else (b.rstrip("\n"), "\n")
            safe = re.sub(r"(?m)^LABEL (\S+)", r"LABEL \1safe", body, count=1)
            safe = re.sub(r"(?m)^(MENU LABEL .*)$", r"\1" + SUFFIX, safe, count=1)
            safe = re.sub(r"(?m)^(\s*APPEND .*archisobasedir=.*)$", lambda m: nomodeset(m.group(1)).rstrip("\n"), safe)
            blocks[i:i + 1] = [body + "\n\n", safe + tail]
            break
    sl.write_text("".join(blocks))

# GRUB (grub.cfg for UEFI without FurrBoot, loopback.cfg for Ventoy): copy the first live menuentry
for cfg in (prof / "grub/grub.cfg", prof / "grub/loopback.cfg"):
    if not cfg.exists():
        continue
    lines = cfg.read_text().splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if l.lstrip().startswith("menuentry ")
                  and "speech" not in l.lower() and "accessib" not in l.lower()), None)
    if start is None:
        continue
    end = next((j for j in range(start + 1, len(lines)) if lines[j].strip() == "}"), None)
    block = "".join(lines[start:end + 1]) if end is not None else ""
    if "archisobasedir=" not in block:
        continue
    head = re.sub(r'^(\s*menuentry\s+)(["\'])(.*?)\2', lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{SUFFIX}{m.group(2)}",
                  lines[start], count=1)
    head = re.sub(r"--id\s+'?([\w.-]+)'?", r"--id '\1-safe-graphics'", head)
    body = [nomodeset(l) if "archisobasedir=" in l else l for l in lines[start + 1:end + 1]]
    lines[end + 1:end + 1] = ["\n", head, *body]
    cfg.write_text("".join(lines))
EOF
grep -q nomodeset "$PROFILE"/efiboot/loader/entries/03-archiso-safe-graphics.conf || { echo "safe graphics entry not added" >&2; exit 1; }

# FurrBoot instead of systemd-boot for UEFI (bootloader/furros/furrboot.efi, or FURRBOOT_EFI=/path). It reads the
# same Boot Loader Specification entries; the extra furrboot-* keys only give them names and pictures.
# BIOS (syslinux) and Ventoy (grub/loopback.cfg) stay as they are. FURRBOOT_TEST=1: the ISO gets its own name.
# FURRBOOT_EFI=none: systemd-boot as before.
[[ -z ${FURRBOOT_EFI:-} && -f $SRC/bootloader/furros/furrboot.efi ]] && FURRBOOT_EFI=$SRC/bootloader/furros/furrboot.efi
[[ ${FURRBOOT_EFI:-} == none ]] && FURRBOOT_EFI=""
if [[ -n ${FURRBOOT_EFI:-} ]]; then
    log "FurrBoot: UEFI menu of the live ISO = $FURRBOOT_EFI"
    E=$PROFILE/efiboot/loader/entries
    sed -i -E 's/^title .*/title    FurrOS Live/' "$E/01-archiso-linux.conf"
    printf '%s\n' "furrboot-kind main" "furrboot-subtitle попробовать и установить" \
        "furrboot-when обычная графика" >> "$E/01-archiso-linux.conf"
    sed -i -E 's/^title .*/title    FurrOS Live - safe graphics/' "$E/03-archiso-safe-graphics.conf"
    printf '%s\n' "furrboot-kind safe" "furrboot-when чёрный экран? запуск без драйвера видеокарты (nomodeset)" \
        >> "$E/03-archiso-safe-graphics.conf"
    if [[ -f $E/02-archiso-speech-linux.conf ]]; then
        sed -i -E 's/^title .*/title    FurrOS Live с озвучкой/' "$E/02-archiso-speech-linux.conf"
        printf '%s\n' "furrboot-kind kernel" "furrboot-when озвучка экрана для незрячих" >> "$E/02-archiso-speech-linux.conf"
    fi
    printf '%s\n' "# FurrBoot on the live medium" "timeout 10" "default 01-archiso-linux" "lang ru" "theme comic" \
        "tz-offset 0" > "$PROFILE/efiboot/loader/furrboot.conf"
    [[ ${FURRBOOT_TEST:-} == 1 ]] && sed -i 's/^iso_version=.*/iso_version="1.0-furrboot-test"/' "$PROFILE/profiledef.sh"
    # mkarchiso copies systemd-boot from the image and only loader.conf from loader/: a patched copy of it
    # also takes furrboot.conf and puts FurrBoot at \EFI\BOOT\BOOTX64.EFI (IA32 mixed mode keeps systemd-boot)
    # (mkarchiso names it BOOT${target_arch}.EFI with target_arch "x64", lowercase: the El Torito/USB EFI image
    # gets its EFI/ copied from there, so this one file is what every UEFI PC starts from the stick)
    MKARCHISO=/root/mkarchiso-furrboot
    sed -e '/"${isofs_dir}\/EFI\/BOOT\/BOOT${target_arch}.EFI"$/a\    if [[ "${target_arch,,}" == x64 ]]; then install -m 0644 -- "'"$FURRBOOT_EFI"'" "${isofs_dir}/EFI/BOOT/BOOT${target_arch}.EFI"; fi' \
        -e '/install -m 0644 -- "${profile}\/efiboot\/loader\/loader.conf" "${work_dir}\/loader"$/a\    if [[ -e "${profile}/efiboot/loader/furrboot.conf" ]]; then install -m 0644 -- "${profile}/efiboot/loader/furrboot.conf" "${work_dir}/loader"; fi' \
        /usr/bin/mkarchiso > "$MKARCHISO"
    [[ $(grep -c 'furrboot' "$MKARCHISO") -eq 2 ]] || { echo "patching mkarchiso failed" >&2; exit 1; }
    chmod +x "$MKARCHISO"
else
    MKARCHISO=mkarchiso
fi

log "List of FurrOS files the installer copies to the new system"
(
  cd "$AIR"
  for p in usr/lib/furros/academy usr/lib/furros/drivers usr/local/bin/furros-drivers usr/local/bin/furros-update usr/local/bin/furros-brand usr/local/bin/furros-firstrun usr/local/bin/furros-wallpaper usr/local/bin/furros-set-wallpaper usr/local/bin/furros-wallpapers-app usr/local/bin/furros-pacman-hint usr/lib/furros/wallpapers usr/local/bin/furros-academy usr/local/bin/furros-welcome usr/local/bin/furros-labwc-fix \
           usr/local/bin/furros-about usr/local/bin/furros-lapa usr/share/applications/furros-about.desktop etc/xdg/autostart/furros-lapa.desktop usr/share/furros-staya \
           usr/share/furros usr/share/backgrounds/furros usr/share/plymouth/themes/furros usr/share/grub/themes/furros \
           usr/share/sddm/themes/furros usr/share/color-schemes/FurrOS.colors usr/share/konsole/FurrOS.profile \
           usr/share/konsole/FurrOS.colorscheme usr/share/fonts/furros usr/share/pixmaps/furros.png \
           usr/share/applications/furros-academy.desktop usr/share/applications/furros-welcome.desktop usr/share/applications/furros-wallpapers.desktop \
           usr/share/plasma/shells/org.kde.plasma.desktop/contents/updates/furros-defaults.js \
           etc/xdg/autostart/furros-firstrun.desktop etc/xdg/autostart/furros-polkit-agent.desktop etc/grub.d/11_furros_safe_graphics etc/grub.d/45_furros_power etc/xdg/fastfetch etc/xdg/konsolerc etc/xdg/ksplashrc etc/xdg/kcminputrc \
           usr/share/icons/FurrOS usr/share/sounds/furros etc/profile.d/furros-cursor.sh etc/profile.d/furros-terminal.sh etc/profile.d/furros-vm-graphics.sh etc/profile.d/furros-desktop.sh usr/local/bin/furros-desktop usr/lib/systemd/user-environment-generators/60-furros-vm-graphics usr/local/bin/furros-gpu-soft usr/local/bin/furros-picom etc/skel/.icons usr/share/plasma/look-and-feel/org.furros.desktop etc/furros/bashrc \
           etc/pacman.d/hooks/60-furros-branding.hook etc/pacman.d/hooks/61-furros-hyprland-lua.hook usr/local/bin/furros-hypr-lua etc/skel/.config usr/share/wallpapers/FurrOS* usr/share/plasma/avatars/furros-* usr/share/pixmaps/faces/furros-* \
           etc/dconf/db/gdm.d/01-furros etc/dconf/profile/gdm \
           etc/systemd/user/furros-firstrun-dde.service etc/systemd/user/dde-session-core.target.wants \
           etc/systemd/user/furros-dde-wm-guard.service etc/systemd/user/dde-session@x11.service.d usr/local/bin/furros-dde-wm-guard \
           etc/systemd/user/furros-update-check.service etc/systemd/user/furros-update-check.timer etc/systemd/user/timers.target.wants; do
      [[ -e $p ]] && echo "/$p"
  done
  for i in usr/share/icons/hicolor/*/apps/furros.png; do echo "/$i"; done
) > "$AIR/usr/share/furros/files.list"
wc -l "$AIR/usr/share/furros/files.list"

log "Signed [furros] repository"
bash "$SRC/tools/build_repo.sh" "$AIR" /root/furros-repo-out
# REPO_ONLY=1: fixes that live only in FurrOS packages (scripts, configs) go out without an ISO build
if [[ ${REPO_ONLY:-} == 1 ]]; then log "REPO_ONLY: repository built, no ISO"; exit 0; fi
mkdir -p "$AIR/usr/share/furros/repo"
for f in /root/furros-repo-out/*; do
    n=$(basename "$f"); n=${n%.sig}
    [[ -e /root/repo-extra/$n ]] || cp "$f" "$AIR/usr/share/furros/repo/"
done
# the videos now ship in furros-wallpapers: the live session itself only needs their still frames
rm -f "$AIR"/usr/share/backgrounds/furros/animated/*.mp4

log "mkarchiso (this takes a while)"
rm -f "$WORK"/out/*.iso "$WORK"/out/*.iso.sig "$WORK"/out/*.iso.sha256
"$MKARCHISO" -v -r -w "$WORK/work" -o "$WORK/out" "$PROFILE"

log "Checksum and signature"
cd "$WORK/out"
for iso in *.iso; do
    sha256sum "$iso" > "$iso.sha256"
    GNUPGHOME=/root/furros-gpg gpg --batch --yes --detach-sign -u 6D7CF8FE1B59637ACAA90BF66FA5E284DD02E46E "$iso"
    GNUPGHOME=/root/furros-gpg gpg --verify "$iso.sig" "$iso"
done
ls -lh "$WORK/out"
log "Done"
