# FurrBoot

The FurrOS boot menu. On UEFI PCs it is FurrBoot itself (`/usr/lib/furrboot/furrboot.efi`). On PCs without UEFI
(BIOS) it is Limine in FurrOS colours, with the same entries.

## What is in the menu

The menu is written by `furrboot-update` from what is installed:

- **FurrOS**: the main kernel (`linux-furros` if installed);
- **Safe graphics**: the same kernel with `nomodeset`;
- **Other kernel**: every other kernel in `/boot`;
- **System snapshots**: the 12 newest snapper snapshots that carry their own kernel. They boot read-only, and
  changes are gone after a reboot;
- **Windows** and **UEFI settings**: found by FurrBoot itself.

The pacman hook (`95-furrboot.hook`) and the snapper plugin rerun it after kernel updates and snapshots.

## Commands

| Command | What it does |
|---|---|
| `sudo furrboot-update` | rewrite the menu (after changing `/etc/kernel/cmdline`, for example) |
| `sudo furrboot-install` | put FurrBoot on the EFI partition again and make it the first boot entry |
| `sudo furrboot-install --bios /dev/sdX --esp /boot/efi` | BIOS: install Limine with the FurrOS menu |
| `furrboot-theme`, `sudo furrboot-theme neon` | show or change the menu's colour theme (in the menu: T) |

## Files

| Path | What it holds |
|---|---|
| `/etc/kernel/cmdline` | kernel parameters; the root subvolume is added from fstab |
| `/etc/kernel/tries` | boot tries for a new kernel (default 3). After that many failed starts FurrBoot boots the spare kernel; `systemd-bless-boot` confirms a good boot |
| `<ESP>/loader/furrboot.conf` | `timeout`, `default`, `theme`, `resolution` and `season` are yours; `lang` and `tz-offset` follow the system. `season auto` (the default) shows snow, a garland and a New Year greeting from 15 December to 15 January; `season off` turns it off, `season on` keeps it all year |
| `<ESP>/loader/entries/*.conf` | Boot Loader Specification entries, with extra `furrboot-*` keys for names and pictures |
| `<boot>/limine/limine.conf` | BIOS only: the Limine menu, rewritten by `furrboot-update` |

Kernels on Btrfs are read straight from the FurrOS partition through the efifs Btrfs driver
(`EFI/FurrOS/drivers/btrfs_x64.efi`, GPL-3.0, https://github.com/pbatard/efifs). Otherwise they are copied to the
FAT partition.

## If FurrBoot doesn't start

GRUB stays installed as the way back on UEFI PCs. Pick «FurrOS» in the board's boot menu (F11, F12 or F8), boot,
then run `sudo furrboot-install`.

FurrBoot speaks the systemd Boot Loader Interface, so `bootctl status` and
`systemctl reboot --boot-loader-entry=` work.
