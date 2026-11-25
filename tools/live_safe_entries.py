"""Live ISO boot menus: the normal entry boots with full graphics (the kernel driver for the card), and a second
"safe graphics" entry adds nomodeset. Until 25.11 every live entry had nomodeset: integrated GPUs on old BIOS
laptops then had no picture at all (tester reports 25.11: Acer Aspire 5315 / Core 2 Duo, AMD A6-7310).
Covers UEFI (systemd-boot / FurrBoot entries), BIOS (syslinux) and the GRUB menus (Ventoy uses loopback.cfg).
    python3 live_safe_entries.py <archiso profile dir>"""
import pathlib
import re
import sys

P = pathlib.Path(sys.argv[1])
SAFE = " nomodeset"

# UEFI: 01-archiso-linux.conf -> 03-archiso-linux-safe.conf
e = P / "efiboot/loader/entries/01-archiso-linux.conf"
if e.exists():
    s = e.read_text()
    s = re.sub(r"^(title\s+.*)$", r"\1 - safe graphics", s, count=1, flags=re.M)
    s = re.sub(r"^sort-key\s+.*$", "sort-key 03", s, flags=re.M)
    s = re.sub(r"^(options\s+.*)$", lambda m: m.group(1) + SAFE, s, count=1, flags=re.M)
    (P / "efiboot/loader/entries/03-archiso-linux-safe.conf").write_text(s)
    print("uefi: safe entry")

# BIOS: the first LABEL block of archiso_sys-linux.cfg, copied as LABEL archsafe
f = P / "syslinux/archiso_sys-linux.cfg"
if f.exists():
    s = f.read_text()
    m = re.search(r"^LABEL .*?(?=^LABEL |^# |\Z)", s, flags=re.M | re.S)
    if m:
        b = m.group(0).rstrip("\n") + "\n"
        b = re.sub(r"^LABEL \S+", "LABEL archsafe", b, count=1, flags=re.M)
        b = re.sub(r"^(MENU LABEL .*)$", r"\1 - safe graphics", b, count=1, flags=re.M)
        b = re.sub(r"^(APPEND .*)$", lambda x: x.group(1) + SAFE, b, count=1, flags=re.M)
        s = s[:m.end()].rstrip("\n") + "\n\n" + b + "\n" + s[m.end():]
        f.write_text(s)
        print("bios: safe entry")

# GRUB: the menuentry with --id 'archlinux', copied as 'archlinux-safe'
for g in (P / "grub/grub.cfg", P / "grub/loopback.cfg"):
    if not g.exists():
        continue
    s = g.read_text()
    m = re.search(r"^menuentry [^\n]*--id 'archlinux' \{\n.*?^\}\n", s, flags=re.M | re.S)
    if not m:
        continue
    b = m.group(0)
    b = b.replace("--id 'archlinux'", "--id 'archlinux-safe'", 1)
    b = re.sub(r'^menuentry "([^"]*)"', r'menuentry "\1 - safe graphics"', b, count=1, flags=re.M)
    b = re.sub(r"^(\s*linux .*)$", lambda x: x.group(1) + SAFE, b, count=1, flags=re.M)
    s = s[:m.end()] + "\n" + b + s[m.end():]
    g.write_text(s)
    print(f"grub: safe entry in {g.name}")
