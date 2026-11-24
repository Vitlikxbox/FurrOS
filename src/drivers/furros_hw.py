#!/usr/bin/env python3
"""FurrOS hardware detection: which graphics drivers a machine needs.

Used by the installer (to pick packages) and installed as `furros-drivers` (to check or install
drivers later, e.g. after changing the graphics card).

NVIDIA generations are told apart by PCI device id, which is reliable even when the pci.ids
database is too old to know the card's name:
    >= 0x1e00            Turing and newer (GTX 16xx, RTX 20xx+) -> open kernel modules (nvidia-open)
    0x1340 .. 0x1dff     Maxwell / Pascal / Volta (GTX 750 .. GTX 10xx) -> no longer in the Arch repos:
                         free nouveau driver now, the legacy proprietary one (nvidia-580xx) comes from [furros] or the AUR
    older                Kepler and before -> nouveau only
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

NVIDIA, AMD, INTEL = "10de", "1002", "8086"


def _lspci():
    try:
        return subprocess.run(["lspci", "-nn"], capture_output=True, text=True, check=False).stdout
    except FileNotFoundError:
        return ""


def gpus(lspci_text=None):
    """Display controllers (PCI class 03xx) as dicts: vendor, device (hex ids), name."""
    text = _lspci() if lspci_text is None else lspci_text
    res = []
    for line in text.splitlines():
        m = re.search(r"\[03[0-9a-f]{2}\]:\s*(.*?)\s*\[([0-9a-f]{4}):([0-9a-f]{4})\]", line)
        if m:
            name = re.sub(r"\s*\(rev [0-9a-f]+\)$", "", m.group(1)).strip()
            res.append({"vendor": m.group(2), "device": m.group(3), "name": pretty(m.group(2), name)})
    return res


BROADCOM = "14e4"
# Broadcom Wi-Fi chips that only work with the proprietary "wl" driver (Arch wiki, "Broadcom wireless"):
# BCM4311/4312/4313/4321/4322/43224/43225/43227/43228/4331/4352/4360/43142. Only installed where such a chip is
# found: broadcom-wl blacklists brcmfmac and friends, which newer Broadcom chips need (that is also why the live ISO
# doesn't carry it — these laptops install over a cable or USB tethering, and get Wi-Fi after the reboot).
BROADCOM_WL = {"4311", "4312", "4727", "4328", "432b", "4353", "4357", "4358", "4359", "4331", "43b1", "43a0",
               "4365"}


def broadcom_wl_wifi(lspci_text=None):
    """Names of network controllers (PCI class 0280) that need broadcom-wl."""
    text = _lspci() if lspci_text is None else lspci_text
    res = []
    for line in text.splitlines():
        m = re.search(r"\[0280\]:\s*(.*?)\s*\[(14e4):([0-9a-f]{4})\]", line)
        if m and m.group(3) in BROADCOM_WL:
            res.append(re.sub(r"\s*\(rev [0-9a-f]+\)$", "", m.group(1)).strip())
    return res


# USB vendors of fingerprint readers that libfprint drives (Synaptics, Goodix, Validity, Upek, FPC, Egis,
# AuthenTec, Focaltech, Elan). Elan also makes USB touchscreens, so for it only its fingerprint product range 0cxx.
FINGERPRINT_VENDORS = {"06cb", "27c6", "138a", "147e", "10a5", "1c7a", "08ff", "2808"}


def fingerprint_reader(root="/sys/bus/usb/devices"):
    """Is there a USB fingerprint reader? Then fprintd goes in, and the reader works on the lock screen."""
    for d in Path(root).glob("*"):
        try:
            v = (d / "idVendor").read_text().strip().lower()
            p = (d / "idProduct").read_text().strip().lower()
        except OSError:
            continue
        if v in FINGERPRINT_VENDORS or (v == "04f3" and p.startswith("0c")):
            return True
    return False


def pretty(vendor, name):
    """'NVIDIA Corporation GA106 [GeForce RTX 3060]' -> 'NVIDIA GeForce RTX 3060'."""
    short = {NVIDIA: "NVIDIA", AMD: "AMD", INTEL: "Intel"}.get(vendor, "")
    inner = re.findall(r"\[([^\]]+)\]", name)
    model = inner[-1] if inner and inner[-1] not in ("AMD/ATI",) else re.sub(r"^.*?(Corporation|Inc\.)\s*", "", name)
    return f"{short} {model}".strip() if short and short.lower() not in model.lower() else model


def nvidia_family(device):
    d = int(device, 16)
    if d >= 0x1E00:
        return "open"
    if d >= 0x1340:
        return "legacy"
    return "nouveau"


def is_laptop():
    try:
        return Path("/sys/class/dmi/id/chassis_type").read_text().strip() in {"8", "9", "10", "14", "31", "32"}
    except OSError:
        return any(p.name.startswith("BAT") for p in Path("/sys/class/power_supply").glob("BAT*"))


def virt():
    try:
        v = subprocess.run(["systemd-detect-virt", "--vm"], capture_output=True, text=True).stdout.strip()
        return "" if v == "none" else v
    except FileNotFoundError:
        return ""


def plan(cards=None, multilib=False, laptop=None, vm=None):
    """What to install for these cards. Returns a dict:
        packages     list of repo packages
        nvidia       "open" | "legacy" | "nouveau" | None (the NVIDIA card's driver, if any)
        early_kms    kernel modules to load from the initramfs (proprietary NVIDIA)
        drop_kms     True when the initramfs `kms` hook must go (it would pull in nouveau)
        notes        list of (level, text_key, args) for the UI ("ok" / "warn")
    """
    cards = gpus() if cards is None else cards
    laptop = is_laptop() if laptop is None else laptop
    vm = virt() if vm is None else vm
    pk = ["mesa", "vulkan-icd-loader", "mesa-utils"]
    if multilib:
        pk += ["lib32-mesa", "lib32-vulkan-icd-loader"]
    res = {"packages": pk, "nvidia": None, "early_kms": [], "drop_kms": False, "notes": []}
    vendors = {c["vendor"] for c in cards}

    for c in cards:
        if c["vendor"] == NVIDIA:
            fam = nvidia_family(c["device"])
            res["nvidia"] = fam
            if fam == "open":
                pk += ["nvidia-open", "nvidia-utils", "nvidia-settings"]
                if multilib:
                    pk.append("lib32-nvidia-utils")
                res["early_kms"] = ["nvidia", "nvidia_modeset", "nvidia_uvm", "nvidia_drm"]
                res["drop_kms"] = True
                res["notes"].append(("ok", "{0}: драйвер NVIDIA (открытые модули)", [c["name"]]))
            else:
                pk.append("vulkan-nouveau")
                # Steam needs a 32-bit Vulkan driver too: without this one pacman picks lib32-nvidia-utils, whose
                # nvidia-utils blacklists nouveau while no NVIDIA kernel module is installed -> no GPU at all
                if multilib:
                    pk.append("lib32-vulkan-nouveau")
                if fam == "legacy":
                    # nouveau often finds no monitor on these cards (GP107 over HDMI: "Cannot find any crtc or sizes")
                    # and leaves a black screen. The installer adds the proprietary 580xx driver from [furros] once that
                    # repository is set up; nouveau above stays as the fallback if that fails
                    res["repo_packages"] = ["linux-headers", "nvidia-580xx-dkms", "nvidia-580xx-utils"]
                    if multilib:
                        res["repo_packages"].append("lib32-nvidia-580xx-utils")
                    res["repo_card"] = c["name"]
                    res["notes"].append(("ok", "{0}: фирменный драйвер NVIDIA 580 из репозитория FurrOS", [c["name"]]))
                else:
                    res["notes"].append(("warn", "{0}: свободный драйвер nouveau. Фирменный драйвер для этой карты "
                                                 "есть только в AUR, его можно поставить позже командой furros-drivers --nvidia-legacy",
                                         [c["name"]]))
        elif c["vendor"] == AMD:
            pk.append("vulkan-radeon")
            if multilib:
                pk.append("lib32-vulkan-radeon")
            res["notes"].append(("ok", "{0}: драйвер AMD (amdgpu)", [c["name"]]))
        elif c["vendor"] == INTEL:
            pk += ["vulkan-intel", "intel-media-driver", "libva-intel-driver"]
            if multilib:
                pk.append("lib32-vulkan-intel")
            res["notes"].append(("ok", "{0}: драйвер Intel", [c["name"]]))
        else:
            res["notes"].append(("ok", "{0}: стандартный драйвер", [c["name"]]))

    # no Vulkan driver for this card (VMs, unknown GPUs): when a desktop needs vulkan-driver (COSMIC does),
    # pacman --noconfirm would take the first provider, nvidia-utils, which also blacklists nouveau
    if res["nvidia"] != "open" and not {"vulkan-nouveau", "vulkan-radeon", "vulkan-intel"} & set(pk):
        pk.append("vulkan-swrast")
        if multilib:
            pk.append("lib32-vulkan-swrast")

    # laptops with a discrete NVIDIA card next to the built-in one: run apps on it with `prime-run`
    # (also with the legacy 580 driver; with nouveau, prime-run's variables are simply ignored)
    if res["nvidia"] in ("open", "legacy") and laptop and vendors & {AMD, INTEL}:
        pk.append("nvidia-prime")
        res["notes"].append(("ok", "Две видеокарты: игры можно запускать на NVIDIA через prime-run", []))

    if fingerprint_reader():
        pk.append("fprintd")
        res["notes"].append(("ok", "Сканер отпечатков пальцев: вход по пальцу (fprintd)", []))

    for name in broadcom_wl_wifi():
        pk.append("broadcom-wl")
        res["notes"].append(("ok", "{0}: драйвер Wi-Fi Broadcom (broadcom-wl)", [name]))

    if vm == "oracle":
        pk.append("virtualbox-guest-utils")
    elif vm in ("kvm", "qemu"):
        pk += ["qemu-guest-agent", "spice-vdagent"]
    elif vm == "vmware":
        pk.append("open-vm-tools")
    elif vm == "microsoft":
        pk.append("hyperv")
    if not cards:
        res["notes"].append(("warn", "Видеокарту определить не удалось, поставлю универсальный драйвер", []))

    seen, out = set(), []
    for p in pk:
        if p not in seen:
            seen.add(p)
            out.append(p)
    res["packages"] = out
    return res


KERNELS = ("linux", "linux-zen", "linux-lts", "linux-furros")


def for_kernels(res, kernels, dkms=False):
    """Fit a plan() to the installed kernels. Prebuilt nvidia-open is built for the stock `linux` only: with zen, lts
    or the FurrOS kernel (dkms=True: it is added later) the module comes from nvidia-open-dkms, built for every kernel,
    which needs each kernel's headers."""
    kernels = [k for k in kernels if k in KERNELS] or ["linux"]
    headers = [k + "-headers" for k in kernels]
    if "nvidia-open" in res["packages"] and (dkms or kernels != ["linux"]):
        i = res["packages"].index("nvidia-open")
        res["packages"][i:i + 1] = ["nvidia-open-dkms", *headers]
    if res.get("repo_packages"):
        res["repo_packages"] = headers + [p for p in res["repo_packages"] if p != "linux-headers"]
    # AMD GCN 1.0/1.1 cards (Radeon HD 7000, R7/R9 200, 2012-2014) get the old radeon driver, with no Vulkan
    # (no Steam/Proton), on kernels before 6.19; 6.19 moved the dedicated cards to amdgpu. linux-lts is older:
    # hand them to amdgpu there too (kernel module options si_support/cik_support; newer GCN ignores them)
    if "vulkan-radeon" in res["packages"] and "linux-lts" in kernels:
        res["modprobe"] = {"20-furros-amdgpu.conf": "options amdgpu si_support=1 cik_support=1\n"
                                                    "options radeon si_support=0 cik_support=0\n"}
    return res


# ------------------------------------------------------------------ furros-drivers (CLI)
def _installed(p):
    return subprocess.run(["pacman", "-Q", p], capture_output=True).returncode == 0


def installed_kernels():
    return [k for k in KERNELS if _installed(k)] or ["linux"]


def multilib_enabled():
    conf = Path("/etc/pacman.conf").read_text()
    return "[multilib]" in conf and "#[multilib]" not in conf


def main(argv):
    p = for_kernels(plan(multilib=multilib_enabled()), installed_kernels())
    print("🐾 FurrOS: видеокарты / graphics cards\n")
    for level, text, args in p["notes"]:
        print(("  ✓ " if level == "ok" else "  ! ") + text.format(*args))
    missing = [x for x in p["packages"] if not _installed(x)]
    print("\nНужные пакеты / packages:", " ".join(p["packages"]))
    if not missing:
        print("✓ Всё уже установлено / everything is installed")
    else:
        print("Не хватает / missing:", " ".join(missing))
    if "--install" not in argv:
        if missing:
            print("\nПоставить: sudo furros-drivers --install")
        if p["nvidia"] == "legacy":
            print("Фирменный драйвер для старой NVIDIA: furros-drivers --nvidia-legacy")
        if any(not (Path("/etc/modprobe.d") / n).exists() for n in (p.get("modprobe") or {})):
            print("Старая AMD на ядре LTS: включить драйвер amdgpu (Vulkan) — sudo furros-drivers --install")
        if p["nvidia"] in ("legacy", "nouveau") and _installed("nvidia-utils") and not _installed("nvidia-580xx-utils"):
            print("! Стоит nvidia-utils без модуля ядра NVIDIA: он отключает nouveau, видеокарта работает без драйвера.\n"
                  "  Исправить: furros-drivers --nvidia-legacy (фирменный драйвер) или (nouveau):\n"
                  "  sudo pacman -S --needed vulkan-nouveau lib32-vulkan-nouveau && sudo pacman -R nvidia-utils lib32-nvidia-utils")
        return 0
    if missing:
        r = subprocess.run(["pacman", "-S", "--needed", "--noconfirm", *missing])
        if r.returncode:
            return r.returncode
    for name, text in (p.get("modprobe") or {}).items():
        f = Path("/etc/modprobe.d") / name
        if not f.exists() or f.read_text() != text:
            f.write_text(text)
            if not p["early_kms"]:
                subprocess.run(["mkinitcpio", "-P"])
    if p["early_kms"]:
        Path("/etc/mkinitcpio.conf.d").mkdir(parents=True, exist_ok=True)
        Path("/etc/mkinitcpio.conf.d/furros-nvidia.conf").write_text(
            f"MODULES=({' '.join(p['early_kms'])})\n")
        conf = Path("/etc/mkinitcpio.conf.d/furros.conf")
        if conf.exists():
            conf.write_text(re.sub(r"\bkms ", "", conf.read_text()))
        subprocess.run(["sh", "-c", NVIDIA_SLEEP_FIX])
        subprocess.run(["mkinitcpio", "-P"])
    print("✓ Готово. Перезагрузи компьютер / Done, please reboot")
    return 0


# the classic "black screen after waking up" on NVIDIA: keep the video memory across suspend and run NVIDIA's own
# suspend/hibernate/resume helpers (the installer does the same; this covers cards added or switched later)
NVIDIA_SLEEP_FIX = ("printf 'options nvidia NVreg_PreserveVideoMemoryAllocations=1\\n' > /etc/modprobe.d/80-furros-nvidia-sleep.conf"
                    "; systemctl enable nvidia-suspend.service nvidia-hibernate.service nvidia-resume.service 2>/dev/null; true")


def legacy_nvidia(argv):
    """Proprietary driver for Maxwell/Pascal cards: prebuilt in [furros] when available, otherwise from the AUR."""
    pkgs = [k + "-headers" for k in installed_kernels()] + ["nvidia-580xx-dkms", "nvidia-580xx-utils"]
    # a fresh install may have no local copy of the [furros] database yet: without it -Si fails and we'd build
    # from the AUR for nothing. Sync first; the install below is a full -Syu, so linux-headers matches the kernel
    print("Обновляю списки пакетов…")
    if subprocess.run(["sudo", "pacman", "-Sy"]).returncode:
        return 1
    in_repo = subprocess.run(["pacman", "-Si", "furros/nvidia-580xx-dkms"], capture_output=True).returncode == 0
    if in_repo:
        if multilib_enabled():
            pkgs.append("lib32-nvidia-580xx-utils")
        print("Ставлю nvidia-580xx из репозитория FurrOS (вместе с обновлением системы).")
        print("Если спросят про конфликт с nvidia-utils / lib32-nvidia-utils — отвечай y: они заменятся на nvidia-580xx.")
        r = subprocess.run(["sudo", "pacman", "-Syu", "--needed", *pkgs]).returncode
    else:
        helper = shutil.which("yay") or shutil.which("paru")
        if not helper:
            print("Нужен помощник AUR (yay). Поставь набор «AUR» или: https://aur.archlinux.org/packages/yay-bin")
            return 1
        if multilib_enabled():
            pkgs.append("lib32-nvidia-580xx-utils")
        print("Ставлю nvidia-580xx-dkms из AUR. Это займёт несколько минут.")
        print("Если спросят про конфликт с nvidia-utils / lib32-nvidia-utils — отвечай y: они заменятся на nvidia-580xx.")
        r = subprocess.run([helper, "-Syu", "--needed", *pkgs, "nvidia-580xx-settings"]).returncode
    if r:
        return r
    # same as the open driver: load it from the initramfs and keep nouveau out of it
    conf = "/etc/mkinitcpio.conf.d/furros.conf"
    subprocess.run(["sudo", "sh", "-c",
                    "printf 'MODULES=(nvidia nvidia_modeset nvidia_uvm nvidia_drm)\\n' > /etc/mkinitcpio.conf.d/furros-nvidia.conf"
                    f" && {{ [ ! -f {conf} ] || sed -i 's/\\bkms //' {conf}; }} && {{ {NVIDIA_SLEEP_FIX}; }} && mkinitcpio -P"])
    print("✓ Готово. Перезагрузи компьютер / Done, please reboot")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--nvidia-legacy" in args:
        sys.exit(legacy_nvidia(args))
    if "--install" in args and subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip() != "0":
        sys.exit("Запусти через sudo: sudo furros-drivers --install")
    sys.exit(main(args))
