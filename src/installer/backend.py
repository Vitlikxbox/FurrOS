#!/usr/bin/env python3
"""FurrOS installer backend. Runs as root, reads a JSON plan, installs the system.

Protocol on stdout (one per line):
    @@P <percent> <text>     progress
    @@S <step-id>            a named step started (for the checklist in the GUI)
    @@E <text>               fatal error (process exits non-zero)
    anything else            log output
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "drivers"))
import catalog  # noqa: E402
import furros_hw  # noqa: E402
from i18n import STRINGS  # noqa: E402

MNT = Path("/mnt/furros")
SHARE = Path("/usr/share/furros")
DRY = False
LANG = "ru"


_out_lock = threading.Lock()


def out(line):
    with _out_lock:  # the slow-mirror watchdog in install_packages() prints from its own thread
        print(line, flush=True)


def T(key, *args):
    """Translate a backend message into the UI language chosen in the installer."""
    text = key if LANG == "ru" else STRINGS.get(key, {}).get(LANG, key)
    return text.format(*args) if args else text


def progress(pct, key, *args):
    out(f"@@P {pct:.1f} {T(key, *args)}")


def step(sid):
    out(f"@@S {sid}")


class InstallError(Exception):
    pass


def run(cmd, *, input=None, check=True, chroot=False, stream=None, env=None):
    """Run a command, echoing its output to the log. `stream` gets each line."""
    if isinstance(cmd, str):
        cmd = ["bash", "-c", cmd]
    if chroot:
        cmd = ["arch-chroot", str(MNT)] + cmd
    shown = " ".join(shlex.quote(c) for c in cmd)
    out(f"$ {shown}")
    if DRY:
        time.sleep(0.15)
        return ""
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                         env={**os.environ, **(env or {})})
    if input is not None:
        p.stdin.write(input)
        p.stdin.close()
    buf = []
    for line in p.stdout:
        line = line.rstrip("\n")
        buf.append(line)
        out(line)
        if stream:
            stream(line)
    p.wait()
    if check and p.returncode != 0:
        raise InstallError(T("Команда завершилась с ошибкой ({0}): {1}", p.returncode, shown))
    return "\n".join(buf)


def write(path, text, mode=None):
    path = Path(str(MNT) + str(path)) if str(path).startswith("/") else Path(path)
    out(f"# write {path}")
    if DRY:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if mode is not None:
        path.chmod(mode)


def part(disk, n):
    return f"{disk}p{n}" if re.search(r"\d$", disk) else f"{disk}{n}"


def is_uefi():
    return Path("/sys/firmware/efi").exists()


# ------------------------------------------------------------------ steps
def prepare(plan):
    step("prepare")
    progress(1, "Проверяю интернет и часы")
    run("timedatectl set-ntp true", check=False)
    run("ping -c1 -W5 archlinux.org >/dev/null", check=True)
    progress(2, "Ищу самые быстрые зеркала")
    run("timeout 90 reflector --latest 20 --protocol https --sort rate --save /etc/pacman.d/mirrorlist", check=False)
    run("sed -i 's/^#\\?ParallelDownloads.*/ParallelDownloads = 5/' /etc/pacman.conf")
    # pacman's own timeout drops stalled mirrors (the live ISO disables it): install_packages() retries
    run("sed -i '/^DisableDownloadTimeout/d' /etc/pacman.conf")
    run("pacman -Sy --noconfirm archlinux-keyring", check=False)
    # leftovers from a previous (failed) attempt: pacstrap's gpg-agent keeps the target busy
    run(f"fuser -km {MNT} 2>/dev/null; umount -R {MNT} 2>/dev/null || umount -Rl {MNT} 2>/dev/null; "
        "cryptsetup close cryptroot 2>/dev/null; swapoff -a; true", check=False)


def largest_free(disk):
    """(first sector, last sector, sector size) of the biggest unallocated region, aligned to 1 MiB."""
    ss = int(subprocess.run(["blockdev", "--getss", disk], capture_output=True, text=True).stdout.strip() or 512)
    best = (0, -1)
    lines = subprocess.run(["parted", "-sm", disk, "unit", "s", "print", "free"], capture_output=True,
                           text=True).stdout.splitlines()
    for line in lines:
        f = line.rstrip(";").split(":")
        if len(f) >= 5 and f[4] == "free":
            a, b = int(f[1].rstrip("s")), int(f[2].rstrip("s"))
            if b - a > best[1] - best[0]:
                best = (a, b)
    align = 1024 * 1024 // ss
    first = -(-best[0] // align) * align
    last = (best[1] + 1) // align * align - 1
    return first, last, ss


def boot_in_root(plan):
    """/boot (kernel + initramfs) inside the Btrfs root, so every snapshot carries the kernel its modules belong to.
    On a separate /boot grub-btrfs boots every snapshot with today's kernel: after a kernel update an older
    snapshot then has no matching /usr/lib/modules (no graphics, no network). Encrypted roots keep a plain /boot:
    GRUB can't open LUKS2 with argon2."""
    return plan.get("filesystem") == "btrfs" and not plan.get("encrypt")


def check_windows_shut_down(disk):
    """Refuse to go next to a Windows that is hibernated or has Fast Startup on: it is not really off, and writing
    to the shared EFI partition (or Windows waking up over our changes) can damage it. Nothing is touched yet."""
    if DRY:
        return
    if not shutil.which("ntfs-3g.probe"):
        out("! ntfs-3g.probe is missing: can't check that Windows is fully shut down")
        return
    out_ = subprocess.run(["lsblk", "-lnpo", "PATH,FSTYPE", disk], capture_output=True, text=True).stdout
    for line in out_.splitlines():
        f = line.split()
        if len(f) == 2 and f[1] == "ntfs":
            # ntfs-3g.probe exit codes: 14 = hibernated (Fast Startup or hibernation), 15 = not cleanly unmounted
            rc = subprocess.run(["ntfs-3g.probe", "--readwrite", f[0]], capture_output=True).returncode
            out(f"ntfs-3g.probe {f[0]}: {rc}")
            if rc in (14, 15):
                raise InstallError(T("Windows не выключена до конца (включён «Быстрый запуск» или гибернация). "
                                     "Загрузи Windows, выполни в командной строке от администратора powercfg /h off, "
                                     "выключи компьютер через «Завершение работы» и запусти установку снова. "
                                     "Диск не тронут"))
        elif len(f) == 2 and f[1] == "BitLocker":
            # an encrypted volume can't be probed: the window's help text asks for powercfg /h off instead
            out(f"{f[0]}: BitLocker, Fast Startup can't be checked from here")


ESP_GUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
MSR_GUID = "e3c9e316-0b5c-4db8-817d-f92df00215ae"  # Microsoft reserved: Windows Setup makes one on every GPT disk


def windows_on_any_disk():
    """An installed Windows on any disk: its reserved partition, or a BitLocker volume. A plain NTFS partition alone
    doesn't count, that may just be a USB stick or a data disk."""
    if DRY:
        return False
    lines = subprocess.run(["lsblk", "-lnpo", "PARTTYPE,FSTYPE"], capture_output=True, text=True).stdout.splitlines()
    return any(MSR_GUID in line.lower() or "BitLocker" in line for line in lines)
ESP_MIN_FREE = 4 * 1024 ** 2  # GRUB's grubx64.efi is ~200 KiB; Windows Setup makes the ESP only 100 MiB


def check_shared_esp(disk, esp):
    """Before touching anything: the disk is GPT (sgdisk would silently turn an MBR disk into GPT and break a BIOS
    Windows), the ESP really is this disk's EFI partition, and it has room for GRUB's loader."""
    if DRY:
        return
    info = subprocess.run(["lsblk", "-ndo", "PTTYPE", disk], capture_output=True, text=True).stdout.strip()
    part_ = subprocess.run(["lsblk", "-ndo", "PKNAME,PARTTYPE,FSTYPE", esp], capture_output=True, text=True).stdout.split()
    out(f"disk {disk}: {info}; esp {esp}: {' '.join(part_)}")
    if info != "gpt" or len(part_) < 3 or f"/dev/{part_[0]}" != disk or part_[1].lower() != ESP_GUID or part_[2] != "vfat":
        raise InstallError(T("На этом диске нет раздела EFI (диск не GPT): поставь FurrOS на весь диск или на другой"))
    # read-only look: Windows' EFI partition is not written until grub-install
    tmp = "/run/furros-esp-check"
    run(f"mkdir -p {tmp} && mount -o ro -t vfat {esp} {tmp}")
    try:
        st = os.statvfs(tmp)
        free = st.f_bavail * st.f_frsize
    finally:
        run(f"umount {tmp}", check=False)
    out(f"esp free: {free // 1024} KiB")
    if free < ESP_MIN_FREE:
        raise InstallError(T("В разделе EFI меньше {0} МБ свободного места, загрузчик FurrOS туда не поместится. Диск не тронут",
                             ESP_MIN_FREE // 1024 ** 2))


FURROS_MIN = 20 * 1024 ** 3   # same numbers as the installer window
WIN_RESERVE = 10 * 1024 ** 3  # left free inside Windows after shrinking
MIB = 1024 ** 2


def disk_layout(disk):
    """sfdisk's view of the disk: {"sectorsize": n, "partitions": [{"node", "start", "size", "type", "uuid", ...}]}."""
    return json.loads(subprocess.run(["sfdisk", "-J", disk], capture_output=True, text=True, check=True).stdout)["partitiontable"]


def ntfs_min_bytes(text):
    """ntfsresize --info-mb-only prints "Minsize (in MB): 2105" (nothing when it can't shrink). Its MB are 10^6;
    counted here as MiB, which leaves Windows a little more room."""
    m = re.search(r"Minsize[^:]*:\s*(\d+)", text or "")
    return int(m.group(1)) * 1024 ** 2 if m else 0


def shrink_windows(disk, shrink):
    """Make room next to Windows by shrinking its NTFS partition at the end (its start never moves).
    ntfsresize(8): it never touches the partition table, so the filesystem is shrunk first and then the partition,
    never smaller than the new filesystem ("otherwise you won't be able to boot"). sfdisk -N changes only the size:
    "the unspecified fields of the partition are not modified", so the type, unique GUID (which Windows' boot
    manager uses to find its partition) and name stay. Every check that can fail runs before the first write."""
    p, give = shrink["part"], int(shrink["bytes"])
    name = os.path.basename(p)
    pk, fstype = (subprocess.run(["lsblk", "-ndo", "PKNAME,FSTYPE", p], capture_output=True, text=True).stdout.split()
                  + ["", ""])[:2]
    out(f"shrink {p} on {pk}: {fstype}, give {give // MIB} MiB")
    if f"/dev/{pk}" != disk or fstype != "ntfs":
        raise InstallError(T("Не получилось сжать раздел Windows: {0} — не раздел NTFS на этом диске. Диск не тронут", p))
    if give < FURROS_MIN:
        raise InstallError(T("На диске меньше 20 ГБ свободного места: освободи место в Windows («Сжать том»)"))
    rc = subprocess.run(["ntfs-3g.probe", "--readwrite", p], capture_output=True).returncode
    out(f"ntfs-3g.probe {p}: {rc}")
    if rc != 0:
        raise InstallError(T("Windows не выключена до конца (включён «Быстрый запуск» или гибернация). "
                             "Загрузи Windows, выполни в командной строке от администратора powercfg /h off, "
                             "выключи компьютер через «Завершение работы» и запусти установку снова. "
                             "Диск не тронут"))
    table = disk_layout(disk)
    ss = int(table.get("sectorsize", 512))
    old = next(x for x in table["partitions"] if x["node"] == p)
    num = int(Path(f"/sys/class/block/{name}/partition").read_text())
    cur = int(old["size"]) * ss
    smallest = ntfs_min_bytes(run(["ntfsresize", "--force", "--info-mb-only", p], check=False))
    if not smallest:
        raise InstallError(T("Не получилось сжать раздел Windows: ntfsresize не может его уменьшить (см. журнал). "
                             "Освободи место в Windows («Управление дисками» → «Сжать том»). Диск не тронут"))
    new = (cur - give) // MIB * MIB
    out(f"{p}: now {cur // MIB} MiB, smallest {smallest // MIB} MiB, new {new // MIB} MiB")
    if new < smallest + WIN_RESERVE:
        raise InstallError(T("Windows занимает слишком много места, столько не отдать: у Windows должно остаться "
                             "хотя бы {0} ГБ свободно. Выбери меньше. Диск не тронут", WIN_RESERVE // 1024 ** 3))
    # dry run: ntfsresize opens the volume read-only and says whether the real resize would work
    run(["ntfsresize", "--force", "--no-action", "--size", str(new), p])
    run(["sfdisk", "-N", str(num), "--no-act", disk], input=f",{new // ss}\n")
    out("partition table before:\n" + subprocess.run(["sfdisk", "-d", disk], capture_output=True, text=True).stdout)

    progress(3, "Сжимаю раздел Windows {0} (не выключай компьютер)", p)
    run(["ntfsresize", "--force", "--size", str(new), p])
    run(["sfdisk", "-N", str(num), disk], input=f",{new // ss}\n")
    run(f"partprobe {disk}; udevadm settle", check=False)
    after = next(x for x in disk_layout(disk)["partitions"] if x["node"] == p)
    out(f"after: {after}")
    same = all(after.get(k) == old.get(k) for k in ("start", "type", "uuid", "name", "attrs"))
    if not same or int(after["size"]) * ss != new:
        raise InstallError(T("Раздел Windows изменился не так, как ожидалось — установка остановлена. Ничего не "
                             "удаляй и напиши нам: журнал в /tmp/furros-install.log"))
    # read-only: fails if the filesystem doesn't fit the partition
    run(["ntfsresize", "--force", "--info", p])


def partition_alongside(plan):
    """Dual boot: FurrOS goes into the free space next to Windows. Nothing existing is touched:
    a 1 GiB /boot + the root partition are created in the biggest gap, Windows' EFI partition is shared."""
    disk = plan["disk"]
    if not is_uefi() and not DRY:
        raise InstallError(T("Установка рядом с Windows работает только в режиме UEFI"))
    check_shared_esp(disk, plan.get("esp", ""))
    check_windows_shut_down(disk)
    if plan.get("shrink") and not DRY:
        shrink_windows(disk, plan["shrink"])
    first, last, ss = (2048, 2048 + 64 * 1024 ** 3 // 512, 512) if DRY else largest_free(disk)
    gib = 1024 ** 3 // ss
    if (last - first + 1) < 20 * gib:
        raise InstallError(T("На диске меньше 20 ГБ свободного места: освободи место в Windows («Сжать том»)"))
    progress(4, "Создаю разделы FurrOS в свободном месте {0}", disk)
    if boot_in_root(plan):
        run(["sgdisk", "-n", f"0:{first}:{last}", "-t", "0:8304", "-c", "0:FurrOS", disk])
    else:
        boot_last = first + gib - 1
        run(["sgdisk", "-n", f"0:{first}:{boot_last}", "-t", "0:8300", "-c", "0:FurrOS boot",
             "-n", f"0:{boot_last + 1}:{last}", "-t", "0:8304", "-c", "0:FurrOS", disk])
    run(f"partprobe {disk}; udevadm settle", check=False)
    # find the two new partitions by where they start
    nums = {}
    for line in subprocess.run(["partx", "-g", "-o", "NR,START", disk], capture_output=True, text=True).stdout.splitlines():
        nr, start = line.split()
        nums[int(start)] = int(nr)
    if boot_in_root(plan):
        return None, part(disk, 3 if DRY else nums[first]), plan["esp"]
    if DRY:
        nums = {first: 3, boot_last + 1: 4}
    return part(disk, nums[first]), part(disk, nums[boot_last + 1]), plan["esp"]


def is_live_medium(disk):
    """The stick FurrOS runs from: holds /run/archiso/bootmnt, the ISO itself (dd) or a Ventoy boot partition."""
    src = subprocess.run(["findmnt", "-no", "SOURCE", "/run/archiso/bootmnt"], capture_output=True, text=True).stdout.strip()
    rows = subprocess.run(["lsblk", "-lnpo", "PATH,FSTYPE,LABEL", disk], capture_output=True, text=True).stdout.splitlines()
    for row in rows:
        f = row.split(None, 2) + ["", ""]
        if (src and f[0] == src) or f[2].strip() == "VTOYEFI" or (f[1] == "iso9660" and f[2].upper().startswith("FURROS")):
            return True
    return False


def partition(plan):
    step("disk")
    disk = plan["disk"]
    uefi = is_uefi()
    if plan.get("mode") == "alongside":
        boot, root, esp = partition_alongside(plan)
        return make_filesystems(plan, boot, root, esp)
    if not DRY and is_live_medium(disk):
        raise InstallError(T("Это флешка, с которой запущена FurrOS: на неё ставить нельзя. Выбери другой диск"))
    progress(4, "Размечаю {0}", disk)
    run(f"wipefs -af {disk}")
    run(f"sgdisk --zap-all {disk}", check=False)
    if uefi:
        layout = "label: gpt\nsize=1G, type=uefi, name=EFI\ntype=linux, name=FurrOS\n"
    else:
        # BIOS: Limine's stage 2 goes into the "BIOS boot" partition, its menu and the kernels onto a FAT partition
        # (Limine reads only FAT; USAGE.md "BIOS/GPT"). It gets the EFI type so the tools find it the same way
        # (bootctl, furrboot-update) and the disk would also boot in UEFI mode later.
        layout = ("label: gpt\nsize=1M, type=21686148-6449-6E6F-744E-656564454649, name=BIOS\n"
                  "size=1G, type=uefi, name=FurrOS-boot\ntype=linux, name=FurrOS\n")
    # --wipe-partitions: old file system signatures inside the new partitions go too (sfdisk(8))
    run(["sfdisk", "--wipe", "always", "--wipe-partitions", "always", disk], input=layout)
    run(f"partprobe {disk}; udevadm settle", check=False)
    if uefi:
        boot, root = part(disk, 1), part(disk, 2)
    else:
        boot, root = part(disk, 2), part(disk, 3)
        # the new "BIOS boot" partition can start right where an old file system did (an EFI partition at 1 MiB
        # is the usual layout): Limine refuses to put its stage 2 over a recognised file system, so clear it
        run(f"dd if=/dev/zero of={part(disk, 1)} bs=1M count=1 conv=fsync status=none")
    return make_filesystems(plan, boot, root, None)


def make_filesystems(plan, boot, root, esp):
    """boot: partition for /boot (whole disk: the new EFI partition itself; dual boot: a new ext4 /boot),
    esp: the existing EFI partition to share (dual boot only, never formatted)."""
    target = root
    if plan.get("encrypt"):
        progress(6, "Шифрую диск (LUKS2)")
        run(["cryptsetup", "-q", "luksFormat", "--type", "luks2", root, "-"], input=plan["encrypt_password"])
        run(["cryptsetup", "open", root, "cryptroot", "-"], input=plan["encrypt_password"])
        target = "/dev/mapper/cryptroot"

    progress(7, "Создаю файловые системы")
    fs = plan.get("filesystem", "ext4")
    if fs == "btrfs":
        run(f"mkfs.btrfs -f -L FurrOS {target} && udevadm settle")
        # the swap file gets its own top-level @swap: nested inside @ it would be missing from every snapshot,
        # so booting a snapshot or rolling back would leave a failed swap unit behind (Arch wiki, Btrfs#Swap file)
        subs = ["@", "@home", "@log", "@pkg", "@snapshots"] + (["@swap"] if plan.get("swap") == "file" else [])
        run(f"mount -t btrfs {target} /mnt && for s in {' '.join(subs)}; do btrfs subvolume create /mnt/$s; done; umount /mnt")
        opts = "noatime,compress=zstd:1,space_cache=v2"
        run(f"mkdir -p {MNT} && mount -t btrfs -o {opts},subvol=@ {target} {MNT}")
        for sub, where in [("@home", "home"), ("@log", "var/log"), ("@pkg", "var/cache/pacman/pkg"),
                           ("@snapshots", ".snapshots"), ("@swap", "swap")]:
            if sub not in subs:
                continue
            run(f"mount --mkdir -t btrfs -o {opts},subvol={sub} {target} {MNT}/{where}")
    else:
        run(f"mkfs.ext4 -F -L FurrOS {target} && udevadm settle")
        run(f"mkdir -p {MNT} && mount -t ext4 {target} {MNT}")
    if esp:
        if boot:
            run(f"mkfs.ext4 -F -L FurrOS-boot {boot} && udevadm settle")
            run(f"mount --mkdir -t ext4 {boot} {MNT}/boot")
        run(f"mount --mkdir -t vfat {esp} {MNT}/boot/efi")
    elif boot:
        # not "EFI": a volume label equal to the EFI directory name makes some firmware miss the directory (Arch wiki,
        # EFI system partition#Firmware does not see the EFI directory)
        run(f"mkfs.fat -F32 -n FURROS {boot} && udevadm settle")
        # with /boot inside the Btrfs root the EFI partition only holds GRUB's loader
        run(f"mount --mkdir -t vfat {boot} {MNT}/{'boot/efi' if boot_in_root(plan) else 'boot'}")
    plan["_root_part"] = root
    plan["_target"] = target


# choices that also get the FurrOS kernel (from [furros], next to the stock one): FurrOS itself, and Zen/LTS so
# that there are always spare kernels in the boot menu
FURROS_KERNEL_WITH = ("linux-furros", "linux-zen", "linux-lts")


def packages_for(plan):
    de = catalog.desktop(plan["desktop"])
    pk = list(catalog.BASE_PACKAGES) + list(de["packages"])
    kernel = plan.get("kernel", "linux")
    # zen / lts come next to the stock kernel, and the FurrOS kernel is added from [furros] later (furros_kernel):
    # the chosen one is the default in the boot menu (KERNEL= in settings.conf), the others are the spares
    if kernel in ("linux-zen", "linux-lts"):
        pk.insert(pk.index("linux") + 1, kernel)
    if de["x11"]:
        pk += catalog.X11_PACKAGES
    for b in catalog.APP_BUNDLES:
        if b["id"] in plan.get("apps", []):
            pk += b["packages"]
    # browser language pack follows the system language
    ff = {"ru": "firefox-i18n-ru", "pl": "firefox-i18n-pl", "es": "firefox-i18n-es-es"}.get(plan.get("ui_lang", "ru"))
    pk = [p for p in pk if not p.startswith("firefox-i18n-")]
    if ff and "firefox" in pk:
        pk.append(ff)
    pk += gpu_packages(plan)
    if "flatpak" in pk:  # the Flatpak choice, and the Games set (Bottles, Heroic, ProtonPlus come from Flathub)
        # a graphical app store for Flatpak (no PackageKit, so it can never do a partial pacman upgrade)
        pk += {"kde": ["discover"], "gnome": ["gnome-software"]}.get(de["id"], [])
    if de["id"] in catalog.VIDEO_DESKTOPS:
        # always, not only when a live wallpaper is picked in the installer: it can be picked later in the
        # wallpapers app (tester report 22.11: KDE, still wallpaper at install, live one later never moved).
        # mpvpaper / xwinwrap are AUR-only: shipped prebuilt and added in desktop_setup()
        pk += ["qt6-multimedia", "qt6-multimedia-ffmpeg"] if de["id"] == "kde" else ["mpv"]
    im = catalog.system_language(plan.get("locale", ""))[3]
    if im in catalog.INPUT_METHODS and de["id"] != "console":
        # CJK/Vietnamese: fonts for the script + the input method (configured in input_method())
        m = catalog.INPUT_METHODS[im]
        pk += m["fonts"]
        pk += ["ibus", m["ibus"][0]] if de["id"] == "gnome" else ["fcitx5", "fcitx5-configtool", "fcitx5-gtk", "fcitx5-qt", *m["fcitx5"]]
    if plan.get("encrypt"):
        pk.append("cryptsetup")
    if not is_uefi() and not DRY:
        pk.append("limine")  # the boot menu of PCs without UEFI (bootloader())
    seen, res = set(), []
    for p in pk:
        if p not in seen:
            seen.add(p)
            res.append(p)
    return res


def wants_multilib(plan):
    return any(b.get("multilib") and b["id"] in plan.get("apps", []) for b in catalog.APP_BUNDLES)


def gpu_packages(plan):
    """Graphics drivers for the cards in this machine (see src/drivers/furros_hw.py)."""
    if DRY:
        return ["mesa"]
    kernel = plan.get("kernel", "linux")
    furros = kernel in FURROS_KERNEL_WITH   # the FurrOS kernel comes later: modules are built by dkms for it too
    installed = ["linux"] + ([kernel] if kernel in ("linux-zen", "linux-lts") else [])
    hw = furros_hw.for_kernels(furros_hw.plan(multilib=wants_multilib(plan)), installed, dkms=furros)
    if furros and hw.get("repo_packages"):
        hw["repo_packages"].insert(1, "linux-furros-headers")  # the legacy driver is built for both kernels
    plan["_gpu"] = hw
    for level, text, args in hw["notes"]:
        out(("✓ " if level == "ok" else "! ") + text.format(*args))
    return hw["packages"]


def install_packages(plan):
    step("packages")
    pkgs = packages_for(plan)
    multilib = wants_multilib(plan)
    if multilib:
        run(r"sed -i '/^#\[multilib\]/,+1 s/^#//' /etc/pacman.conf")
        run("pacman -Sy --noconfirm", check=False)
    progress(10, "Скачиваю и ставлю пакеты ({0} шт.). Это самый долгий шаг", len(pkgs))
    # without a tty pacman prints plain "name downloading..." / "installing name..." lines,
    # so count them against the total from "Packages (N)"
    count = {"total": 0, "dl": 0, "inst": 0}
    # a stalled mirror keeps the same line on screen for minutes: say so, so the installer doesn't look hung
    last = {"t": time.monotonic(), "pct": 10.0, "slow": False}

    def seen(pct):
        last.update(t=time.monotonic(), pct=pct, slow=False)

    def watch():
        while not done.wait(15):
            if count["total"] and not count["inst"] and not last["slow"] and time.monotonic() - last["t"] > 90:
                last["slow"] = True
                progress(last["pct"], "Зеркало отвечает медленно, жду. Установка не зависла")

    def on_line(line):
        m = re.match(r"Packages \((\d+)\)", line)
        if m:
            count["total"] = int(m.group(1))
            return
        if not count["total"]:
            return  # still syncing databases (core/extra), not packages yet
        n = count["total"]
        m = re.match(r"\s*(\S+) downloading\.\.\.", line)
        if m:
            count["dl"] += 1
            seen(10 + 30 * min(count["dl"] / n, 1))
            progress(last["pct"], "Скачиваю {0} ({1}/{2})", m.group(1), count["dl"], n)
            return
        m = re.match(r"(?:\(\s*\d+/\d+\)\s+)?installing (\S+?)(?:\.\.\.)?\s*$", line)
        if m:
            count["inst"] += 1
            progress(40 + 28 * min(count["inst"] / n, 1), "Ставлю {0} ({1}/{2})", m.group(1), count["inst"], n)

    # English output so the progress parser understands it whatever the live session language is
    # a slow or flaky connection can drop a mirror mid-download: try again, finished files stay cached
    # an attempt that still got new packages into the cache doesn't count: on a slow line (or behind a VPN)
    # every attempt can stall once yet bring the download closer to the end; 20 rounds at most in any case
    tries, strikes = 5, 0
    cache = MNT / "var/cache/pacman/pkg"

    def cached():
        return len(list(cache.glob("*.pkg.tar.zst"))) if cache.is_dir() else 0

    done = threading.Event()
    threading.Thread(target=watch, daemon=True).start()
    try:
        for rnd in range(20):
            count.update(total=0, dl=0, inst=0)
            seen(10)
            before = cached()
            try:
                # stdbuf -oL: into a pipe pacman's stdout is block-buffered, and its non-tty " name downloading..."
                # lines are never flushed (callback.c: dload_init_event), so the log and the progress bar froze at
                # 10% for the whole download (issue #13). Line buffering hands every line over as it is printed
                run(["stdbuf", "-oL", "pacstrap", "-K", str(MNT)] + pkgs, stream=on_line, env={"LC_ALL": "C"})
                break
            except InstallError:
                strikes += 0 if cached() > before else 1
                if strikes >= tries or rnd == 19:
                    raise
                progress(10, "Связь оборвалась, пробую скачать ещё раз ({0}/{1})", strikes + 1, tries)
                run(f"rm -rf {MNT}/etc/pacman.d/gnupg", check=False)  # pacstrap -K sets the keyring up again
                # the mirror that stalled goes to the end of the list, and fewer parallel downloads stall less
                rotate_mirrors()
                run("sed -i 's/^#\\?ParallelDownloads.*/ParallelDownloads = 2/' /etc/pacman.conf", check=False)
    finally:
        done.set()
    if multilib:
        run(r"sed -i '/^#\[multilib\]/,+1 s/^#//' " + f"{MNT}/etc/pacman.conf")
    run(f"sed -i 's/^#\\?ParallelDownloads.*/ParallelDownloads = 8/; s/^#Color/Color\\nILoveCandy/' {MNT}/etc/pacman.conf")
    run(f"cp /etc/pacman.d/mirrorlist {MNT}/etc/pacman.d/mirrorlist")


def rotate_mirrors(path="/etc/pacman.d/mirrorlist"):
    """Move the first Server line to the end, so the next attempt starts from another mirror."""
    if DRY:
        return
    try:
        lines = Path(path).read_text().splitlines()
    except OSError:
        return
    servers = [i for i, l in enumerate(lines) if l.startswith("Server")]
    if len(servers) > 1:
        lines.append(lines.pop(servers[0]))
        Path(path).write_text("\n".join(lines) + "\n")


# Super+Space as a second app-menu key in the tiling configs: the app menu stays on Super+D
SUPER_SPACE_BINDS = {
    "niri/config.kdl": r"/^\s*Mod+Space {/d",
    "hypr/hyprland.lua": r'/^hl\.bind(mod \.\. " + Space"/d',
    "sway/config": r"/^bindsym \$mod+space exec/d",
    "i3/config": r"/^bindsym \$mod+space exec/d",
    "qtile/config.py": r'/Key(\[mod\], "space"/d',
    "sxhkd/sxhkdrc": r"s/^super + {d,space}$/super + d/",  # bspwm
}


def free_super_space():
    """The user switches layouts with Super+Space: the compositor would grab that key for the app menu first,
    so the layout never changes. Drop those bindings (the menu is still on Super+D); in Awesome Super+Space picks
    the next window layout, which moves to Super+Alt+Space."""
    for rel, expr in SUPER_SPACE_BINDS.items():
        conf = MNT / "etc/skel/.config" / rel
        if conf.exists():
            run(["sed", "-i", expr, str(conf)])
    rc = MNT / "etc/skel/.config/awesome/rc.lua"
    if rc.exists():
        run(["sed", "-i", r'/awful\.layout\.inc( *1)/ s/{ *modkey, *}, *"space"/{ modkey, "Mod1" }, "space"/', str(rc)])


FURROS_PACKAGES = ["furros-mirrorlist", "furros-branding", "furros-wallpapers", "furros-staya", "furros-academy",
                   "furros-drivers"]
# on the ISO only for now: installed from its copy of [furros], later upgrades come with -Syu once it is online too
FURROS_BOOT_PACKAGES = ["furrboot"]
# Arch package -> FurrOS rebuild that replaces it (packages/<name>/PKGBUILD). deepin-kwin 6.0.8-12 was built against
# kscreenlocker/kglobalacceld < 6.8 and can't load with 6.8: Deepin ends up with no window manager (report 18.11).
FURROS_REPLACEMENTS = {"deepin-kwin": "furros-deepin-kwin"}


def install_furros_repo(repo):
    """FurrOS itself comes as signed packages from the [furros] repository (a copy is on the ISO),
    so later updates arrive with a normal `pacman -Syu`."""
    tmp = MNT / "var/tmp/furros-repo"  # not /tmp: arch-chroot mounts an empty tmpfs there
    run(f"mkdir -p {tmp} && cp {repo}/*.pkg.tar.zst {repo}/*.pkg.tar.zst.sig {tmp}/ && rm -f {tmp}/furros-keyring-*.sig")
    # the keyring first, without its signature: pacman can't know our key before it is installed
    run("pacman -U --noconfirm --needed $(ls /var/tmp/furros-repo/furros-keyring-*.pkg.tar.zst)", chroot=True)
    pkgs = " ".join(f"$(ls /var/tmp/furros-repo/{p}-[0-9]*.pkg.tar.zst)" for p in FURROS_PACKAGES)
    run(f"pacman -U --noconfirm --needed --overwrite '/etc/skel/*' --overwrite '/etc/xdg/*' --overwrite '/etc/dconf/*' {pkgs}", chroot=True)
    for p in FURROS_BOOT_PACKAGES:  # the boot menu (FurrBoot on UEFI, Limine on BIOS): bootloader() sets it up
        if DRY or list(repo.glob(f"{p}-[0-9]*.pkg.tar.zst")):
            run(f"pacman -U --noconfirm --needed $(ls /var/tmp/furros-repo/{p}-[0-9]*.pkg.tar.zst)", chroot=True)
    # FurrOS rebuilds of Arch packages that Arch left broken: they replace the Arch one. Online, the -Syu below does
    # it too (`replaces=`); this also covers an install without network. --noconfirm answers "remove the conflicting
    # package?" with no (and pacman's --ask is undocumented), so: drop the Arch one without touching its dependents
    # (-Rdd), then install ours, which provides the same name — nothing runs in the chroot in between.
    for arch_pkg, ours in FURROS_REPLACEMENTS.items():
        if DRY or list(repo.glob(f"{ours}-[0-9]*.pkg.tar.zst")):
            # exact name: `pacman -Q deepin-kwin` also matches a package that only provides it (ours)
            run(f"if pacman -Qq {arch_pkg} 2>/dev/null | grep -qx {arch_pkg}; then pacman -Rdd --noconfirm {arch_pkg} && "
                f"pacman -U --noconfirm $(ls /var/tmp/furros-repo/{ours}-[0-9]*.pkg.tar.zst); fi", chroot=True)
    # only now: the [furros] section includes the mirrorlist that furros-mirrorlist has just installed
    conf = MNT / "etc/pacman.conf"
    if DRY or "[furros]" not in conf.read_text():
        # the package database is signed too: require it, so a mirror can't hand out a forged package list
        run(f"printf '\\n[furros]\\nSigLevel = Required\\nInclude = /etc/pacman.d/furros-mirrorlist\\n' >> {conf}")
    run(f"rm -rf {tmp}")
    update_furros_packages()


def update_furros_packages():
    """The ISO carries a copy of [furros] from the day it was built: pull the current FurrOS packages
    (wallpapers, Lapa's School, branding, drivers…) from the online repository right away, so a fresh install
    doesn't start out behind. Offline or a broken mirror: keep the copies from the ISO and go on."""
    progress(71, "Скачиваю свежие файлы FurrOS")
    # no package names here: pacman -S with an explicit target installs the repository's version even when it is
    # OLDER, so an ISO built after the last repository upload lost its own newer FurrOS files (seen 13.11:
    # «downgraded furros-branding»). A plain -Syu only ever moves forward.
    try:
        run(["timeout", "900", "pacman", "-Syu", "--noconfirm",
             "--overwrite", "/etc/skel/*", "--overwrite", "/etc/xdg/*", "--overwrite", "/etc/dconf/*"],
            chroot=True, env={"LC_ALL": "C"})
    except InstallError:
        out("! [furros]: could not fetch fresh packages (offline?), keeping the ones from the ISO")


def copy_furros_files(plan):
    step("branding")
    progress(70, "Переношу оформление FurrOS")
    repo = SHARE / "repo"
    if DRY or repo.exists():
        install_furros_repo(repo)
        files = []
    else:  # an ISO without the repository: copy the files like before
        files = (SHARE / "files.list").read_text().split()
    for f in files:
        src = Path(f)
        if not src.exists():
            continue
        dst = Path(str(MNT) + f)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst, follow_symlinks=False)
    bg = "/usr/share/backgrounds/furros"
    wp = plan.get("wallpaper", "furros-default.png")
    video = plan.get("wallpaper_video")
    # animated wallpapers keep their still frame next to the video; it is used for the lock screen
    # and on desktops that can't play video. A static wallpaper (or a video that isn't there) uses the plain file,
    # so the login screen never ends up pointing at a missing picture
    if video and not DRY and not (MNT / f"{bg.lstrip('/')}/animated/{video}").exists():
        video = plan["wallpaper_video"] = ""
    still = f"{bg}/animated/{wp}" if video else f"{bg}/{wp}"
    run(f"ln -sf {still} {MNT}{bg}/current.png")
    de = catalog.desktop(plan["desktop"])
    write("/etc/furros/settings.conf",
          f"DESKTOP={de['id']}\nWALLPAPER={bg}/current.png\n"
          f"WALLPAPER_VIDEO={bg + '/animated/' + video if video else ''}\n"
          f"ACADEMY_ON_FIRST_LOGIN={'1' if plan.get('academy', True) else '0'}\n"
          f"FASTFETCH={'1' if plan.get('fastfetch', True) else '0'}\nUI_LANG={plan.get('ui_lang', 'ru')}\n"
          # the kernel picked in the installer: the default entry of the boot menu (furrboot-update)
          f"KERNEL={plan.get('kernel', 'linux')}\n")
    # desktop-specific dotfiles go to /etc/skel before the user is created
    skel = SHARE / "skel" / de["id"]
    if skel.exists() and not DRY:
        shutil.copytree(skel, MNT / "etc/skel", dirs_exist_ok=True)
    localize_skel(plan.get("ui_lang", "ru"))
    run("/usr/local/bin/furros-brand", chroot=True)
    lang = plan.get("ui_lang", "ru")
    run(f"cp {MNT}/usr/share/furros/fastfetch/config.{lang}.jsonc {MNT}/etc/xdg/fastfetch/config.jsonc", check=False)


# the few words the shipped configs show on screen, in the language chosen in the installer (Russian in the files)
SKEL_TEXT = {
    ".config/hypr/hyprlock.conf": [("Привет, $USER 🐾", {"en": "Hi, $USER 🐾", "pl": "Cześć, $USER 🐾", "es": "Hola, $USER 🐾"}),
                                   ("Пароль…", {"en": "Password…", "pl": "Hasło…", "es": "Contraseña…"})],
    ".config/wofi/config": [("Найти приложение…", {"en": "Find an app…", "pl": "Znajdź aplikację…", "es": "Buscar aplicación…"})],
}


def localize_skel(lang):
    if lang == "ru" or DRY:
        return
    for rel, pairs in SKEL_TEXT.items():
        f = MNT / "etc/skel" / rel
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        for ru, tr in pairs:
            text = text.replace(ru, tr.get(lang, tr["en"]))
        f.write_text(text, encoding="utf-8")


def furros_kernel(plan):
    """The FurrOS kernel, from the online [furros] repository (too big for the ISO). Offline or failing: the stock
    kernel that is already installed simply stays the default."""
    if plan.get("kernel") not in FURROS_KERNEL_WITH:
        return
    progress(71.5, "Ставлю ядро FurrOS")
    pkgs = ["linux-furros"]
    if "nvidia-open-dkms" in ((plan.get("_gpu") or {}).get("packages") or []):
        pkgs.append("linux-furros-headers")  # the dkms hook builds the NVIDIA module for it
    try:
        run(["timeout", "1800", "pacman", "-S", "--needed", "--noconfirm", *pkgs], chroot=True, env={"LC_ALL": "C"})
        plan["_furros_kernel"] = DRY or (MNT / "boot/vmlinuz-linux-furros").exists()
    except InstallError:
        plan["_furros_kernel"] = False
    if not plan["_furros_kernel"]:
        out("! linux-furros: not installed (offline?), the standard kernel stays the default")


NVIDIA_MODULES = ["nvidia", "nvidia_modeset", "nvidia_uvm", "nvidia_drm"]


def nvidia_legacy_driver(plan):
    """GTX 750 .. 10xx: the proprietary 580xx driver from [furros] (furros_hw.plan sets repo_packages), now that the
    repository is configured. On these cards nouveau often shows no picture at all. If anything fails the install
    goes on with nouveau: the driver packages are removed again, since nvidia-580xx-utils blacklists nouveau."""
    gpu = plan.get("_gpu") or {}
    pkgs = gpu.get("repo_packages")
    if not pkgs:
        return
    progress(72, "Ставлю драйвер NVIDIA для {0}", gpu.get("repo_card", "NVIDIA"))
    # -Syu: linux-headers must match the kernel; the dkms pacman hook builds the module for it inside the chroot
    try:
        run(["pacman", "-Syu", "--noconfirm", "--needed", *pkgs], chroot=True, env={"LC_ALL": "C"})
        built = DRY or any(MNT.glob("usr/lib/modules/*/updates/dkms/nvidia.ko*"))
    except InstallError:
        built = False
    if built:
        gpu["early_kms"], gpu["drop_kms"] = NVIDIA_MODULES, True
        return
    out("! NVIDIA 580: the driver could not be installed, keeping nouveau (later: furros-drivers --nvidia-legacy)")
    installed = [p for p in pkgs if not p.endswith("-headers")
                 and subprocess.run(["arch-chroot", str(MNT), "pacman", "-Q", p], capture_output=True).returncode == 0]
    if installed:
        run(["pacman", "-Rns", "--noconfirm", *installed], chroot=True, check=False)


def kernel_dir(pkgbase):
    """/usr/lib/modules/<version> of an installed kernel package (its pkgbase file names the package)."""
    for d in MNT.glob("usr/lib/modules/*"):
        try:
            if (d / "pkgbase").read_text().strip() == pkgbase:
                return d
        except OSError:
            continue
    return None


def nvidia_furros_kernel(plan):
    """The proprietary NVIDIA module is built by dkms for the FurrOS kernel too. When that build fails, pacman still
    succeeds (hook failures don't change its exit code), and then mkinitcpio stops the install (MODULES=(nvidia ...)
    not found) or the FurrOS kernel boots with no graphics driver at all: nouveau is blacklisted by nvidia-utils,
    the picture comes from the firmware framebuffer, stretched and without acceleration (issue #8). Try the build
    once more; if it still fails, the FurrOS kernel goes and the stock one, which has the driver, is the default."""
    gpu = plan.get("_gpu") or {}
    if DRY or not plan.get("_furros_kernel") or not gpu.get("early_kms"):
        return
    kdir = kernel_dir("linux-furros")
    if kdir is None:
        return

    def has_module():
        return any(kdir.glob("**/nvidia.ko*"))

    if not has_module():
        out(f"! NVIDIA: no module for linux-furros ({kdir.name}), building it again")
        run(["dkms", "autoinstall", "-k", kdir.name], chroot=True, check=False)
    if has_module():
        return
    out("! NVIDIA: the module could not be built for linux-furros: removing that kernel, the standard one stays")
    # only the installed ones: pacman -R with a name that isn't installed removes nothing at all
    run("pacman -Rns --noconfirm $(pacman -Qq linux-furros linux-furros-headers 2>/dev/null)", chroot=True, check=False)
    plan["_furros_kernel"] = False
    if plan.get("kernel") == "linux-furros":
        run(["sed", "-i", "s/^KERNEL=.*/KERNEL=linux/", "/etc/furros/settings.conf"], chroot=True, check=False)


def configure(plan):
    step("system")
    progress(74, "Настраиваю язык, время и имя компьютера")
    run(f"genfstab -U {MNT} >> {MNT}/etc/fstab")
    if plan.get("mode") == "alongside" and not DRY:
        # Windows' EFI partition is mounted only while something reads it (os-prober, grub-install) and let go after a
        # minute: if Windows hibernates (or Fast Startup comes back after an update) the two systems don't keep it
        # mounted at the same time (Arch wiki, EFI system partition#Hibernation and multi boot systems)
        fstab = Path(f"{MNT}/etc/fstab")
        lines = []
        for line in fstab.read_text().splitlines():
            f = line.split()
            if len(f) >= 4 and not line.startswith("#") and f[1] == "/boot/efi":
                f[3] += ",noauto,x-systemd.automount,x-systemd.idle-timeout=1min"
                line = "\t".join(f)
            lines.append(line)
        fstab.write_text("\n".join(lines) + "\n")
    # file managers mount Windows disks through udisks, which prefers the ntfs3 kernel driver: it has no guard against a
    # hibernated Windows (Fast Startup), writing there can corrupt it. "ntfs" goes through mount.ntfs = ntfs-3g, which
    # refuses to write to a hibernated Windows (Arch wiki, Dual boot with Windows#Fast Startup and hibernation; udisks)
    write("/etc/udisks2/mount_options.conf", "[defaults]\nntfs_drivers=ntfs\n")
    tz = plan.get("timezone", "Europe/Moscow")
    run(["ln", "-sf", f"/usr/share/zoneinfo/{tz}", "/etc/localtime"], chroot=True)
    if plan.get("mode") == "alongside" or windows_on_any_disk():
        # Windows keeps the hardware clock in local time: do the same, or the clock jumps after every switch.
        # Also when Windows sits on another disk and FurrOS took a whole disk of its own (Arch wiki, System time)
        run(["hwclock", "--systohc", "--localtime"], chroot=True, check=False)
    else:
        run(["hwclock", "--systohc"], chroot=True, check=False)
    loc = plan.get("locale", "ru_RU.UTF-8")
    if loc not in dict(catalog.LOCALES):
        loc = "en_US.UTF-8"
    # locale.gen lines are "<name> <charset>" exactly as in glibc's SUPPORTED: "ru_RU.UTF-8 UTF-8", but "hi_IN UTF-8"
    gens = {loc, "en_US.UTF-8"}
    gen_lines = "".join(f"{g} UTF-8\n" for g in sorted(gens))
    write("/etc/locale.gen", gen_lines)
    run(["locale-gen"], chroot=True)
    write("/etc/locale.conf", f"LANG={loc}\n")
    # layouts as "layout" or "layout(variant)" (catalog.KEYBOARDS); XKB wants two parallel lists
    layouts = [l for l in plan.get("layouts", ["us", "ru"]) if l in catalog.KEYBOARD_CODES] or ["us"]
    kb, var = catalog.xkb_split(layouts)
    base = kb.split(",")
    cyr = any(l in ("ru", "ua", "by", "kz", "bg", "mk", "rs", "kg", "tj", "mn") for l in base)
    # the text console (vconsole.conf) has its own keymaps: the first non-US Latin layout, else US
    console_maps = {"latam": "la-latin1", "pl": "pl2", "de": "de-latin1", "fr": "fr-latin1", "it": "it", "pt": "pt-latin1",
                    "br": "br-abnt2", "gb": "uk", "tr": "trq", "cz": "cz", "sk": "sk-qwertz", "hu": "hu", "ro": "ro",
                    "fi": "fi", "se": "sv-latin1", "no": "no", "dk": "dk", "nl": "nl", "be": "be-latin1", "ch": "sg",
                    "ca": "cf", "hr": "croat", "si": "slovene", "ee": "et", "lt": "lt", "lv": "lv", "es": "es"}
    console_map = next((console_maps[l] for l in base if l in console_maps), "us")
    vc_font = "cyr-sun16" if cyr else "lat2-16"
    write("/etc/vconsole.conf", f"KEYMAP={console_map}\nFONT={vc_font}\n")
    toggle = plan.get("layout_toggle", "grp:alt_shift_toggle")
    has_var = any(var.split(","))
    # systemd-localed reads this file too (GNOME, Cinnamon and others take their layouts from it)
    write("/etc/X11/xorg.conf.d/00-keyboard.conf",
          'Section "InputClass"\n    Identifier "system-keyboard"\n    MatchIsKeyboard "on"\n'
          f'    Option "XkbLayout" "{kb}"\n' + (f'    Option "XkbVariant" "{var}"\n' if has_var else "") +
          f'    Option "XkbOptions" "{toggle}"\nEndSection\n')
    write("/etc/xdg/kxkbrc", f"[Layout]\nLayoutList={kb}\n" + (f"VariantList={var}\n" if has_var else "") +
          f"Options={toggle}\nResetOldOptions=true\nUse=true\n")
    write("/etc/furros/keyboard.conf", f"LAYOUTS={kb}\nVARIANTS={var}\nTOGGLE={toggle}\n")
    # wayland compositors don't read xorg.conf.d: give them the layouts directly
    # Hyprland 0.57+ only reads Lua (hyprland.lua requires this file)
    write("/etc/skel/.config/furros/keyboard-hypr.lua",
          f'hl.config({{ input = {{ kb_layout = "{kb}", kb_variant = "{var}", kb_options = "{toggle}" }} }})\n')
    write("/etc/skel/.config/furros/keyboard-sway.conf",
          f'input type:keyboard {{\n    xkb_layout "{kb}"\n' + (f'    xkb_variant "{var}"\n' if has_var else "") +
          f'    xkb_options "{toggle}"\n}}\n')
    niri = MNT / "etc/skel/.config/niri/config.kdl"
    if niri.exists():
        # GNU sed: \n in the replacement is a new line, \1 the indentation of the layout line
        variant_line = f'\\n\\1variant "{var}"' if has_var else ""
        run(["sed", "-i", f's/^\\( *\\)layout "us,ru"/\\1layout "{kb}"{variant_line}/; '
                          f's/^\\( *\\)options "grp:alt_shift_toggle"/\\1options "{toggle}"/', str(niri)])
    # Qtile's keyboard widget: "layout variant" entries, comma separated
    qtile_kbs = ",".join(f"{l} {v}".strip() for l, v in zip(base, var.split(",")))
    run(f"printf 'export FURROS_LAYOUTS=\"%s\"\nexport FURROS_KBS=\"%s\"\n' {shlex.quote(' '.join(base))} "
        f"{shlex.quote(qtile_kbs)} > {MNT}/etc/profile.d/furros-keyboard.sh")
    if plan["desktop"] == "awesome":
        rc = MNT / "etc/skel/.config/awesome/rc.lua"
        run(f"cp {MNT}/etc/xdg/awesome/rc.lua {rc}")
        run(["sed", "-i",
             's|beautiful.init(.*)|beautiful.init(os.getenv("HOME") .. "/.config/awesome/furros-theme.lua")|; '
             's|terminal = "xterm"|terminal = "alacritty"|', str(rc)])
        run(f"printf '\\nawful.spawn.once(\"furros-firstrun\")\\nawful.spawn.once(\"furros-picom\")\\n"
            f"awful.spawn.once(\"nm-applet\")\\n"
            f"awful.spawn.once(\"/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1\")\\n"
            f"awful.spawn.once(\"furros-wallpaper\")\\n"
            f"pcall(dofile, os.getenv(\"HOME\") .. \"/.config/awesome/furros-keys.lua\")\\n' >> {rc}")
    input_method(plan, catalog.system_language(loc)[3], layouts)
    if toggle == "grp:win_space_toggle":
        free_super_space()
    host = plan.get("hostname", "furros")
    write("/etc/hostname", host + "\n")
    write("/etc/hosts", f"127.0.0.1 localhost\n::1 localhost\n127.0.1.1 {host}.localdomain {host}\n")

    # everyday responsiveness (the same knobs Fedora and CachyOS ship)
    # - small dirty-page limits: copying to a slow USB stick no longer freezes the whole desktop
    write("/etc/sysctl.d/80-furros-desktop.conf",
          "vm.dirty_bytes = 268435456\nvm.dirty_background_bytes = 67108864\n")
    # - BFQ keeps a spinning disk responsive under load; SSD/NVMe keep the kernel default
    write("/etc/udev/rules.d/60-furros-ioscheduler.rules",
          'ACTION=="add|change", KERNEL=="sd[a-z]*|mmcblk[0-9]*", ATTR{queue/rotational}=="1", '
          'ATTR{queue/scheduler}="bfq"\n')
    # - hardening from the Lynis audit that costs a desktop nothing (Ubuntu/Fedora do the same):
    #   rare network protocols with a history of kernel holes are never loaded,
    #   ICMP redirects and source routing are ignored (route spoofing on foreign Wi-Fi), kernel addresses hidden
    write("/etc/modprobe.d/80-furros-hardening.conf",
          "".join(f"install {m} /bin/false\n" for m in ("dccp", "sctp", "rds", "tipc")))
    write("/etc/sysctl.d/80-furros-hardening.conf",
          "kernel.kptr_restrict = 2\n"
          "net.ipv4.conf.all.accept_redirects = 0\nnet.ipv4.conf.default.accept_redirects = 0\n"
          "net.ipv6.conf.all.accept_redirects = 0\nnet.ipv6.conf.default.accept_redirects = 0\n"
          "net.ipv4.conf.all.send_redirects = 0\nnet.ipv4.conf.default.send_redirects = 0\n"
          "net.ipv4.conf.all.accept_source_route = 0\nnet.ipv6.conf.all.accept_source_route = 0\n")
    # - the journal never eats more than 200 MB of disk
    write("/etc/systemd/journald.conf.d/80-furros.conf", "[Journal]\nSystemMaxUse=200M\n")
    # - systemd-oomd: when memory runs out, close the runaway app instead of freezing the whole system
    #   (Fedora's defaults: memory pressure in the user session, swap almost full system-wide)
    write("/etc/systemd/system/user@.service.d/80-furros-oomd.conf",
          "[Service]\nManagedOOMMemoryPressure=kill\nManagedOOMMemoryPressureLimit=50%\n")
    write("/etc/systemd/system/-.slice.d/80-furros-oomd.conf", "[Slice]\nManagedOOMSwap=kill\n")

    # swap
    swap = plan.get("swap", "zram")
    if swap == "zram":
        write("/etc/systemd/zram-generator.conf", "[zram0]\nzram-size = min(ram / 2, 8192)\ncompression-algorithm = zstd\n")
        # compressed RAM swap is cheap: use it eagerly, and read it page by page (values from the Arch wiki)
        write("/etc/sysctl.d/80-furros-zram.conf",
              "vm.swappiness = 180\nvm.watermark_boost_factor = 0\nvm.watermark_scale_factor = 125\nvm.page-cluster = 0\n")
    elif swap == "file":
        size = plan.get("swap_size_mb", 4096)
        if plan.get("filesystem") == "btrfs":
            run(f"btrfs filesystem mkswapfile --size {size}m {MNT}/swap/swapfile")  # /swap is the @swap subvolume
            run(f"echo '/swap/swapfile none swap defaults 0 0' >> {MNT}/etc/fstab")
        else:
            run(f"dd if=/dev/zero of={MNT}/swapfile bs=1M count={size} status=none && chmod 600 {MNT}/swapfile && mkswap {MNT}/swapfile")
            run(f"echo '/swapfile none swap defaults 0 0' >> {MNT}/etc/fstab")

    progress(77, "Собираю initramfs с заставкой Лапы")
    hooks = ["base", "systemd", "plymouth", "autodetect", "microcode", "modconf", "kms", "keyboard",
             "sd-vconsole", "block"]
    gpu = plan.get("_gpu") or {}
    if gpu.get("drop_kms"):
        hooks.remove("kms")  # it would put nouveau into the initramfs next to the NVIDIA driver
    for name, text in (gpu.get("modprobe") or {}).items():
        write(f"/etc/modprobe.d/{name}", text)  # before mkinitcpio: the modconf hook copies them in
    if gpu.get("early_kms"):
        # proprietary NVIDIA: load it from the initramfs so the boot splash and the login screen work
        write("/etc/mkinitcpio.conf.d/furros-nvidia.conf", f"MODULES=({' '.join(gpu['early_kms'])})\n")
        # sleep/resume: the classic "black screen after waking up" on NVIDIA. The Arch wiki fix: keep the video memory
        # across suspend and run NVIDIA's own suspend/hibernate/resume helpers (harmless if the package enabled them)
        write("/etc/modprobe.d/80-furros-nvidia-sleep.conf", "options nvidia NVreg_PreserveVideoMemoryAllocations=1\n")
        for unit in ("nvidia-suspend", "nvidia-hibernate", "nvidia-resume"):
            run(["systemctl", "enable", f"{unit}.service"], chroot=True, check=False)
    if plan.get("encrypt"):
        hooks.append("sd-encrypt")
    hooks += ["filesystems", "fsck"]
    if snapshots_on(plan):
        # snapshots are read-only: boot them with a writable overlay (see SD_VOLATILE_HOOK)
        write("/etc/initcpio/install/sd-volatile", SD_VOLATILE_HOOK, 0o644)
        hooks.append("sd-volatile")
    write("/etc/mkinitcpio.conf.d/furros.conf", f"HOOKS=({' '.join(hooks)})\n")
    run(["mkinitcpio", "-P"], chroot=True)


SD_VOLATILE_HOOK = """#!/bin/bash
# FurrOS: lets systemd.volatile=overlay work in a systemd initramfs, so a read-only Btrfs snapshot picked in the
# boot menu gets a writable tmpfs layer on top (changes are gone after a reboot). grub-btrfs-overlayfs is a
# busybox runtime hook and never runs with the systemd hook.
build() {
    add_module overlay
    add_binary /usr/lib/systemd/systemd-volatile-root
    add_systemd_unit systemd-volatile-root.service
}

help() {
    echo "Boot read-only snapshots with a writable overlay (systemd.volatile=overlay)."
}
"""


def snapshots_on(plan):
    return "snapshots" in plan.get("apps", []) and plan.get("filesystem") == "btrfs"


def users(plan):
    step("user")
    progress(80, "Создаю пользователя")
    u = plan["username"]
    run(["useradd", "-m", "-G", "wheel,audio,video,input,storage", "-s", "/bin/bash", "-c", plan.get("fullname", u), u],
        chroot=True)
    run(["chpasswd"], input=f"{u}:{plan['password']}\n", chroot=True)
    if plan.get("lock_root"):
        run(["passwd", "-l", "root"], chroot=True)
    else:
        run(["chpasswd"], input=f"root:{plan['password']}\n", chroot=True)
    # account picture: the FurrOS mascot (AccountsService for SDDM/GDM and the settings, ~/.face.icon for the rest)
    avatar = "/usr/share/furros/avatars/furros-mascot.png"
    if DRY or (MNT / avatar.lstrip("/")).exists():
        run(f"install -Dm644 {MNT}{avatar} {MNT}/var/lib/AccountsService/icons/{u}", check=False)
        write(f"/var/lib/AccountsService/users/{u}", f"[User]\nIcon=/var/lib/AccountsService/icons/{u}\n")
        run(["install", "-Dm644", "-o", u, "-g", u, avatar, f"/home/{u}/.face.icon"], chroot=True, check=False)
        # SDDM (sddm.conf(5)): FacesDir holds <user>.face.icon; ~/.face.icon is behind the 700 home directory
        run(f"install -Dm644 {MNT}{avatar} {MNT}/usr/share/sddm/faces/{u}.face.icon", check=False)
    write("/etc/sudoers.d/10-furros", "%wheel ALL=(ALL:ALL) ALL\nDefaults pwfeedback\nDefaults insults\n", 0o440)
    # temporary passwordless sudo for AUR builds during install
    write("/etc/sudoers.d/99-furros-install", f"{u} ALL=(ALL:ALL) NOPASSWD: ALL\n", 0o440)
    run(["sudo", "-u", u, "xdg-user-dirs-update"], chroot=True, check=False)



def input_method(plan, im, layouts):
    """Chinese, Japanese, Korean, Vietnamese: an input method on top of the keyboard layouts. Fcitx 5 with the
    environment fcitx-im.org recommends per session type ("Using Fcitx 5 on Wayland"): X11 sets the GTK/Qt/SDL
    modules; Wayland only XMODIFIERS (+ Qt's), KDE starts it as its virtual keyboard. GNOME uses IBus, which
    GNOME Shell has built in. The packages come from packages_for()."""
    if im not in catalog.INPUT_METHODS:
        return
    de = catalog.desktop(plan["desktop"])
    if de["id"] == "console":
        return
    if de["id"] == "gnome":
        engine = catalog.INPUT_METHODS[im]["ibus"][1]
        kb, var = catalog.xkb_split(layouts)
        src = [f"('xkb', '{l}{'+' + v if v else ''}')" for l, v in zip(kb.split(","), var.split(","))]
        src.append(f"('ibus', '{engine}')")
        if not (MNT / "etc/dconf/profile/user").exists():
            write("/etc/dconf/profile/user", "user-db:user\nsystem-db:local\n")
        write("/etc/dconf/db/local.d/20-furros-input-sources",
              f"[org/gnome/desktop/input-sources]\nsources=[{', '.join(src)}]\n")
        return   # desktop_setup() runs `dconf update` for GNOME
    env = ["XMODIFIERS=@im=fcitx"]
    if de["id"] == "kde":
        run(["kwriteconfig6", "--file", "/etc/xdg/kwinrc", "--group", "Wayland", "--key", "InputMethod",
             "/usr/share/applications/org.fcitx.Fcitx5.desktop"], chroot=True, check=False)
    elif de["x11"] and de["id"] != "budgie":       # Budgie 10.10 runs on labwc (Wayland)
        env += ["GTK_IM_MODULE=fcitx", "QT_IM_MODULE=fcitx", "SDL_IM_MODULE=fcitx"]
    else:
        env += ["QT_IM_MODULE=fcitx", "QT_IM_MODULES=wayland;fcitx"]
    run(f"printf '%s\n' {' '.join(shlex.quote(e) for e in env)} >> {MNT}/etc/environment")
    # the full desktops start it through /etc/xdg/autostart (fcitx5 ships that file); tiling ones don't read it
    start = {
        "sway": (".config/furros/keyboard-sway.conf", "exec fcitx5 -d --replace"),
        "hyprland": (".config/furros/keyboard-hypr.lua",
                     'hl.on("hyprland.start", function() hl.exec_cmd("fcitx5 -d --replace") end)'),
        "niri": (".config/niri/config.kdl", 'spawn-at-startup "fcitx5" "-d" "--replace"'),
        "i3": (".config/i3/config", "exec --no-startup-id fcitx5 -d --replace"),
        "bspwm": (".config/bspwm/bspwmrc", "fcitx5 -d --replace &"),
        "awesome": (".config/awesome/rc.lua", 'awful.spawn.once("fcitx5 -d --replace")'),
        "qtile": (".config/qtile/config.py",
                  "@hook.subscribe.startup_once\ndef furros_input_method():\n"
                  "    subprocess.Popen(\"fcitx5 -d --replace\", shell=True)"),
    }.get(de["id"])
    if start:
        f = MNT / "etc/skel" / start[0]
        if f.exists() or DRY:
            out(f"# input method autostart -> {f}")
            if not DRY:
                with f.open("a") as fh:
                    fh.write(f"\n# input method (FurrOS installer)\n{start[1]}\n" if not f.name.endswith(".lua")
                             else f"\n-- input method (FurrOS installer)\n{start[1]}\n")

def desktop_setup(plan):
    step("desktop")
    de = catalog.desktop(plan["desktop"])
    progress(83, "Настраиваю {0}", de["name"])
    services = ["NetworkManager", "fstrim.timer", "systemd-timesyncd", "paccache.timer", "systemd-oomd",
                "power-profiles-daemon", "reflector.timer"]
    if de["dm"]:
        services.append(de["dm"])
    apps = plan.get("apps", [])
    if "bluetooth" in apps:
        services.append("bluetooth")
    if "printing" in apps:
        services.append("cups.socket")
    # "--vm": a VM, not a container; it prints "none" on real hardware, which is a non-empty string
    virt = "" if DRY else subprocess.run(["systemd-detect-virt", "--vm"], capture_output=True, text=True).stdout.strip()
    virt = "" if virt == "none" else virt
    if virt == "oracle":
        services.append("vboxservice")
    elif virt in ("kvm", "qemu"):
        services.append("qemu-guest-agent")
    elif virt == "vmware":
        services.append("vmtoolsd")
    elif virt == "microsoft":
        services += ["hv_kvp_daemon", "hv_vss_daemon"]
    services.append("ufw")
    for s in services:
        run(["systemctl", "enable", s], chroot=True, check=False)
    # firewall on from the first boot: incoming blocked, outgoing allowed (ufw's defaults);
    # inactive ufw only edits its rule files, so this is safe inside the chroot
    if "kdeconnect" in de["packages"]:
        # KDE Connect only from local networks (home Wi-Fi, LAN), never straight from the internet
        for net in ("192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "fe80::/10", "fc00::/7"):
            for proto in ("tcp", "udp"):
                run(["ufw", "allow", "from", net, "to", "any", "port", "1714:1764", "proto", proto],
                    chroot=True, check=False)
    run(["sed", "-i", "s/^ENABLED=.*/ENABLED=yes/", "/etc/ufw/ufw.conf"], chroot=True, check=False)

    if de["id"] == "sway" and (plan.get("_gpu") or {}).get("nvidia") in ("open", "legacy"):
        # sway refuses to start on the proprietary NVIDIA driver unless told --unsupported-gpu (sway(1)); the login
        # screen runs plain `sway` from PATH, where /usr/local/bin comes first. Only while that driver is loaded
        write("/usr/local/bin/sway",
              "#!/bin/sh\n# FurrOS: sway on the proprietary NVIDIA driver needs --unsupported-gpu (sway(1))\n"
              "if [ -d /sys/module/nvidia ]; then exec /usr/bin/sway --unsupported-gpu \"$@\"; fi\n"
              "exec /usr/bin/sway \"$@\"\n", mode=0o755)
    if virt and de["id"] in ("hyprland", "niri", "sway"):
        # VirtualBox/VMware GPUs can't hand EGL buffers to wlroots-style compositors: render apps in software.
        # Decided at every login, not here (the live system runs with nomodeset and can't see the virtual GPU):
        # QEMU / GNOME Boxes with virgl 3D keep the GPU (usr/lib/systemd/user-environment-generators/60-furros-vm-graphics)
        write("/etc/furros/vm-software-gl", f"{virt}\n")

    if de["id"] in catalog.VIDEO_DESKTOPS:      # see packages(): the player goes in even without a live wallpaper
        # AUR-only pieces, prebuilt and shipped on the ISO: the Plasma video wallpaper plugin (GPLv2)
        # for KDE, mpvpaper (GPLv3) for Hyprland/Sway/Niri, xwinwrap for the X11 tilers (i3/bspwm/Awesome/Qtile)
        stem = ("plasma6-wallpapers-smart-video-wallpaper-reborn" if de["id"] == "kde"
                else "xwinwrap-git" if de["id"] in catalog.X11_VIDEO_DESKTOPS else "mpvpaper")
        pkgs = sorted(Path("/usr/share/furros/pkgs").glob(f"{stem}-[0-9]*.pkg.tar.zst"))
        if pkgs or DRY:
            name = pkgs[-1].name if pkgs else "plugin.pkg.tar.zst"
            # not /tmp: arch-chroot mounts an empty tmpfs there
            run(f"cp /usr/share/furros/pkgs/{name} {MNT}/var/tmp/", check=False)
            run(["pacman", "-U", "--noconfirm", "--needed", f"/var/tmp/{name}"], chroot=True, check=False)
            run(f"rm -f {MNT}/var/tmp/{name}", check=False)
        # the player must really be there: without it furros-wallpaper falls back to the still frame and the
        # chosen live wallpaper never moves (tester report 19.11: i3/bspwm/Awesome/Qtile had no xwinwrap).
        # Second chance from [furros], which carries the same packages
        if not DRY and run(f"pacman -Qq {stem} >/dev/null 2>&1 && echo ok", chroot=True, check=False).splitlines()[-1:] != ["ok"]:
            out(f"!! {stem} is not installed after pacman -U, trying the [furros] repository")
            run(["pacman", "-S", "--noconfirm", "--needed", stem], chroot=True, check=False)

    u = plan["username"]
    if de["dm"] == "sddm":
        auto = f"[Autologin]\nUser={u}\nSession={de['session']}\n\n" if plan.get("autologin") else ""
        write("/etc/sddm.conf.d/furros.conf",
              f"{auto}[Theme]\nCurrent=furros\nCursorTheme=FurrOS\nCursorSize=24\n\n[General]\nNumlock=on\n")
        # preselect the right session on the login screen: SDDM lists Wayland sessions first, so Xfce got
        # "Xfce (Wayland)" (no compositor installed -> black screen after typing the password)
        dirs = ["xsessions", "wayland-sessions"] if de.get("x11") else ["wayland-sessions", "xsessions"]
        found = [f"/usr/share/{d}/{de['session']}.desktop" for d in dirs
                 if Path(f"{MNT}/usr/share/{d}/{de['session']}.desktop").exists()]
        if found:
            write("/var/lib/sddm/state.conf", f"[Last]\nUser={u}\nSession={found[0]}\n")
            run(["chown", "-R", "sddm:sddm", "/var/lib/sddm"], chroot=True, check=False)
    elif de["dm"] == "gdm" and plan.get("autologin"):
        write("/etc/gdm/custom.conf", f"[daemon]\nAutomaticLoginEnable=True\nAutomaticLogin={u}\n")
    if de["id"] == "gnome":
        run("dconf update", chroot=True, check=False)
    if de["dm"] is None:
        run(["systemctl", "set-default", "multi-user.target"], chroot=True)


def extras(plan):
    step("extras")
    apps = plan.get("apps", [])
    u = plan["username"]
    if "aur" in apps:
        progress(86, "Собираю помощника AUR (yay)")
        run(["sudo", "-u", u, "bash", "-c",
             "cd /tmp && rm -rf yay-bin && git clone --depth 1 https://aur.archlinux.org/yay-bin.git && "
             "cd yay-bin && makepkg -si --noconfirm"], chroot=True, check=False)
    # COSMIC's store pulls flatpak in on its own: without Flathub it would open empty
    if "flatpak" in apps or os.path.exists(f"{MNT}/usr/bin/flatpak"):
        progress(88, "Подключаю Flathub")
        run(["flatpak", "remote-add", "--if-not-exists", "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"],
            chroot=True, check=False)
    if "gaming" in apps:
        progress(88, "Включаю игровой режим")
        # GameMode may raise game priority only for members of its group
        run(["usermod", "-aG", "gamemode", u], chroot=True, check=False)
        # while a game runs: higher CPU priority, best I/O priority, no screensaver
        write("/etc/gamemode.ini", "[general]\nrenice=10\nsoftrealtime=auto\nioprio=0\ninhibit_screensaver=1\n")
        # split-lock "mitigation" makes some games stutter badly; it protects nothing on a home PC
        write("/etc/sysctl.d/80-furros-gaming.conf", "kernel.split_lock_mitigate = 0\n")
        # not in the Arch repos (AUR only): Windows programs, Epic/GOG games and Proton versions from Flathub
        progress(89, "Ставлю Bottles, Heroic и ProtonPlus из Flathub")
        run(["flatpak", "install", "-y", "--noninteractive", "--system", "flathub", "com.usebottles.bottles",
             "com.heroicgameslauncher.hgl", "com.vysp3r.ProtonPlus"], chroot=True, check=False)
        # MangoHud overlay in FurrOS colours, right Shift+F12 shows/hides it
        write(f"/home/{u}/.config/MangoHud/MangoHud.conf",
              "legacy_layout=false\nfps\nframetime\ncpu_stats\ncpu_temp\ngpu_stats\ngpu_temp\nram\nvram\n"
              "position=top-left\nround_corners=8\nbackground_alpha=0.6\nbackground_color=1E1418\n"
              "text_color=FFF4EC\ngpu_color=7FF0F0\ncpu_color=FF8CBE\nfps_color_change\n"
              "toggle_hud=Shift_R+F12\n")
        run(["chown", "-R", f"{u}:{u}", f"/home/{u}/.config/MangoHud"], chroot=True, check=False)
        # ntsync: Wine/Proton use the kernel's NT sync primitives when the device exists (fewer stutters)
        write("/etc/modules-load.d/furros-ntsync.conf", "ntsync\n")
        write("/etc/udev/rules.d/80-furros-ntsync.rules", 'KERNEL=="ntsync", MODE="0666"\n')
        # bigger shader caches: shaders compiled once stay compiled, so less stutter on the next launch
        write("/etc/environment.d/80-furros-gaming.conf",
              "MESA_SHADER_CACHE_MAX_SIZE=12G\n__GL_SHADER_DISK_CACHE_SIZE=12000000000\n"
              "__GL_SHADER_DISK_CACHE_SKIP_CLEANUP=1\n")
    if "snapshots" in apps and plan.get("filesystem") == "btrfs":
        progress(89, "Настраиваю снимки Snapper")
        run(f"umount {MNT}/.snapshots && rmdir {MNT}/.snapshots", check=False)
        run(["snapper", "--no-dbus", "-c", "root", "create-config", "/"], chroot=True, check=False)
        run(["btrfs", "subvolume", "delete", "/.snapshots"], chroot=True, check=False)
        run(f"mkdir -p {MNT}/.snapshots && mount -a --target-prefix {MNT} --fstab {MNT}/etc/fstab", check=False)
        # keep a sane number of snapshots so they never fill the disk; let wheel users list them
        run(["snapper", "--no-dbus", "-c", "root", "set-config", "TIMELINE_LIMIT_HOURLY=5", "TIMELINE_LIMIT_DAILY=7",
             "TIMELINE_LIMIT_WEEKLY=2", "TIMELINE_LIMIT_MONTHLY=0", "TIMELINE_LIMIT_YEARLY=0", "NUMBER_LIMIT=10",
             "NUMBER_LIMIT_IMPORTANT=5", "ALLOW_GROUPS=wheel", "SYNC_ACL=yes"], chroot=True, check=False)
        # grub-btrfsd keeps GRUB's snapshot menu current; BIOS PCs boot Limine, whose menu furrboot-update writes
        units = ["snapper-timeline.timer", "snapper-cleanup.timer"] + (["grub-btrfsd.service"] if is_uefi() or DRY else [])
        run(["systemctl", "enable", *units], chroot=True, check=False)
        # snapshots show up in the boot menu under a FurrOS submenu
        run(["sed", "-i", 's/^#\\?GRUB_BTRFS_SUBMENUNAME=.*/GRUB_BTRFS_SUBMENUNAME="FurrOS: снимки системы"/',
             "/etc/default/grub-btrfs/config"], chroot=True, check=False)
        # a snapshot booted from the menu gets a writable overlay (sd-volatile hook); the list shows only what
        # people need — when and what (the snapshot path and padding cut the description off in the theme).
        # remount-fs can't remount the overlay root and would mark every snapshot boot "degraded"
        if not DRY:
            with open(f"{MNT}/etc/default/grub-btrfs/config", "a") as f:
                f.write('\n# FurrOS\nGRUB_BTRFS_SNAPSHOT_KERNEL_PARAMETERS='
                        '"systemd.volatile=overlay systemd.mask=systemd-remount-fs.service"\n'
                        'GRUB_BTRFS_TITLE_FORMAT=("date" "type" "description")\n')
    run(f"rm -f {MNT}/etc/sudoers.d/99-furros-install")


def bootloader(plan):
    step("boot")
    progress(92, "Ставлю загрузчик GRUB с темой FurrOS")
    cmd = "loglevel=3 quiet splash"
    linux = ""
    if plan.get("encrypt"):
        uuid = "DRYRUN" if DRY else subprocess.run(["blkid", "-s", "UUID", "-o", "value", plan["_root_part"]],
                                                    capture_output=True, text=True).stdout.strip()
        linux = f"rd.luks.name={uuid}=cryptroot root=/dev/mapper/cryptroot"
    defaults = (
        'GRUB_DEFAULT=0\nGRUB_TIMEOUT=5\nGRUB_DISTRIBUTOR="FurrOS"\n'
        f'GRUB_CMDLINE_LINUX_DEFAULT="{cmd}"\nGRUB_CMDLINE_LINUX="{linux}"\n'
        'GRUB_PRELOAD_MODULES="part_gpt part_msdos"\nGRUB_TIMEOUT_STYLE=menu\nGRUB_TERMINAL_INPUT=console\n'
        'GRUB_GFXMODE=auto\nGRUB_GFXPAYLOAD_LINUX=keep\nGRUB_DISABLE_RECOVERY=true\nGRUB_DISABLE_OS_PROBER=false\n'
        # no "UiApp / VBOX HARDDISK / FurrOS (EFI BootNext)" entries: they pushed the snapshots out of sight
        'GRUB_DISABLE_BOOTNEXT=true\n'
        'GRUB_THEME="/boot/grub/themes/furros/theme.txt"\n'
    )
    chosen = plan.get("kernel", "linux")
    if chosen in ("linux-zen", "linux-lts"):
        # the chosen kernel first; the stock and FurrOS kernels stay under "Advanced options" as the spares
        defaults += f'GRUB_TOP_LEVEL="/boot/vmlinuz-{chosen}"\n'
    elif chosen == "linux-furros" and plan.get("_furros_kernel"):
        # two kernels: ours first; the standard one stays under "Advanced options" as the spare
        defaults += 'GRUB_TOP_LEVEL="/boot/vmlinuz-linux-furros"\n'
    # the theme must sit next to the kernel on the unencrypted /boot, not on the (maybe encrypted) root
    run(f"mkdir -p {MNT}/boot/grub/themes && cp -r {MNT}/usr/share/grub/themes/furros {MNT}/boot/grub/themes/")
    write("/etc/default/grub", defaults)
    if plan.get("mode") == "alongside":
        # the shared EFI partition: our own FurrOS entry only, Windows' files and fallback loader stay as they are;
        # os-prober (GRUB_DISABLE_OS_PROBER=false) puts "Windows Boot Manager" into the menu
        run(["grub-install", "--target=x86_64-efi", "--efi-directory=/boot/efi", "--bootloader-id=FurrOS"], chroot=True)
        # some boards only boot \EFI\BOOT\BOOTX64.EFI (Arch wiki, GRUB#Default/fallback boot path). Windows usually keeps
        # a copy of its own loader there, which is never overwritten; only when that path is empty does GRUB go there too
        esp_root = Path(f"{MNT}/boot/efi/EFI")
        fallback = [p for d in (esp_root.iterdir() if esp_root.is_dir() else []) if d.name.lower() == "boot"
                    for p in d.iterdir() if p.name.lower() == "bootx64.efi"]
        if not fallback and not DRY:
            run(["grub-install", "--target=x86_64-efi", "--efi-directory=/boot/efi", "--removable"], chroot=True, check=False)
    elif is_uefi() or DRY:
        efi = "/boot/efi" if boot_in_root(plan) else "/boot"
        run(["grub-install", "--target=x86_64-efi", f"--efi-directory={efi}", "--bootloader-id=FurrOS"], chroot=True)
        # also install to the fallback path so picky firmware (and VirtualBox) always finds it
        run(["grub-install", "--target=x86_64-efi", f"--efi-directory={efi}", "--removable"], chroot=True, check=False)
    # the kernel command line FurrBoot and Limine use (furrboot-update reads /etc/kernel/cmdline; the root
    # subvolume it adds itself from fstab). The same parameters GRUB gets from /etc/default/grub.
    if plan.get("encrypt"):
        kcmd = f"{linux} rw {cmd}"
    else:
        fsuuid = "DRYRUN" if DRY else subprocess.run(["blkid", "-s", "UUID", "-o", "value", plan["_target"]],
                                                      capture_output=True, text=True).stdout.strip()
        kcmd = f"root=UUID={fsuuid} rw {cmd}"
    write("/etc/kernel/cmdline", kcmd + "\n")
    bios = not is_uefi() and not DRY
    if bios:
        # PCs without UEFI: Limine in FurrOS colours (FurrBoot is a UEFI program). GRUB isn't installed there.
        progress(92, "Ставлю загрузчик Limine с темой FurrOS")
        esp = "/boot/efi" if boot_in_root(plan) else "/boot"
        run(["furrboot-install", "--bios", plan["disk"], "--esp", esp], chroot=True)
    else:
        run(f"chmod 755 {MNT}/etc/grub.d/11_furros_safe_graphics {MNT}/etc/grub.d/45_furros_power 2>/dev/null; true", check=False)
        run(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"], chroot=True)
    if snapshots_on(plan):
        # the "fresh install" snapshot comes last: with /boot inside the root it must already hold GRUB and its
        # config (a restore of it has to boot), and the temporary passwordless sudo must be gone from it.
        # ASCII on purpose: snapper stores other letters as XML entities and GRUB shows them as "&#x434;..."
        run(["snapper", "--no-dbus", "-c", "root", "create", "-c", "number", "--userdata", "important=yes",
             "-d", "FurrOS: fresh install"], chroot=True, check=False)
        if not bios:
            run(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"], chroot=True)  # list the new snapshot in the menu
    if bios:
        run(["furrboot-update"], chroot=True, check=False)  # the new snapshot into Limine's menu
    else:
        furrboot(plan)


def furrboot(plan):
    """UEFI: FurrBoot, the FurrOS boot menu, becomes the first boot entry; GRUB stays as the way back (its own
    "FurrOS" firmware entry and, on a whole disk, the fallback path \\EFI\\BOOT\\BOOTX64.EFI). Kernels are read
    from the FurrOS partition itself (Btrfs driver) or straight from a FAT /boot. Not used when /boot is a
    separate ext4 partition next to Windows (encrypted dual boot): the shared EFI partition has no room for
    kernel copies, so GRUB stays there."""
    if not DRY and not (MNT / "usr/bin/furrboot-install").exists():
        out("! furrboot: package not installed, GRUB stays the boot menu")
        return
    if plan.get("mode") == "alongside" and not boot_in_root(plan):
        out("furrboot: /boot is a separate ext4 partition next to Windows, GRUB stays the boot menu")
        return
    progress(96, "Ставлю загрузчик FurrBoot")
    esp = "/boot/efi" if (plan.get("mode") == "alongside" or boot_in_root(plan)) else "/boot"
    # first the files and the menu, without a firmware entry: only a FurrBoot that has a menu becomes the default
    try:
        run(["furrboot-install", "--esp", esp, "--no-nvram"], chroot=True)
        entries = DRY or any((MNT / esp.lstrip("/") / "loader/entries").glob("furros*.conf"))
        if not entries:
            raise InstallError("furrboot: no menu entries were written")
        run(["furrboot-install", "--esp", esp], chroot=True)
    except InstallError as e:
        out(f"! furrboot: {e}; GRUB stays the boot menu")


def finish(plan):
    step("finish")
    progress(98, "Убираю за собой")
    run(f"cp /tmp/furros-install.log {MNT}/var/log/furros-install.log", check=False)
    run("sync")
    run(f"gpgconf --homedir {MNT}/etc/pacman.d/gnupg --kill all 2>/dev/null; fuser -km {MNT} 2>/dev/null; true",
        check=False)
    run(f"umount -R {MNT} || umount -Rl {MNT}", check=False)
    if plan.get("encrypt"):
        run("cryptsetup close cryptroot", check=False)
    progress(100, "Готово! Гав!")


STEPS = [prepare, partition, install_packages, copy_furros_files, furros_kernel, nvidia_legacy_driver,
         nvidia_furros_kernel, configure, users, desktop_setup, extras,
         bootloader, finish]


def main():
    global DRY, LANG
    args = sys.argv[1:]
    if "--dry-run" in args:
        DRY = True
        args.remove("--dry-run")
    if "--list-packages" in args:
        args.remove("--list-packages")
        plan = json.loads(Path(args[0]).read_text())
        print(" ".join(packages_for(plan)))
        return 0
    plan_path = Path(args[0])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    LANG = plan.get("ui_lang", "ru")
    # what was chosen in the installer goes to the install log (no passwords), so a report can be checked later
    out("plan: " + json.dumps({k: v for k, v in plan.items() if "password" not in k}, ensure_ascii=False))
    if not DRY:
        plan_path.unlink(missing_ok=True)  # contains passwords
        if os.geteuid() != 0:
            out("@@E " + T("Установщику нужны права root"))
            return 1
    try:
        for fn in STEPS:
            fn(plan)
    except InstallError as e:
        out(f"@@E {e}")
        return 2
    except Exception as e:  # noqa: BLE001
        out("@@E " + T("Неожиданная ошибка: {0}", repr(e)))
        return 3
    finally:
        # a failed install must not leave the temporary passwordless sudo behind on the disk
        if not DRY:
            Path(f"{MNT}/etc/sudoers.d/99-furros-install").unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
