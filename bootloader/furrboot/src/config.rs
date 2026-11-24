//! Settings and boot entries.
//!
//! FurrBoot looks for `\loader\furrboot.conf` first on its own partition, then on every FAT
//! partition it can see (when it sits on Windows' small EFI partition, the kernels live on the
//! separate FurrOS /boot partition). Entries are Boot Loader Specification files in
//! `\loader\entries\*.conf` on the same partition, written by `furrboot-update`:
//!
//! ```text
//! title    FurrOS
//! linux    /vmlinuz-linux-furros
//! initrd   /initramfs-linux-furros.img
//! options  root=UUID=... rw quiet splash
//! sort-key 10
//! furrboot-kind      main            # main | kernel | safe | snapshot
//! furrboot-subtitle  ядро FurrOS · KDE Plasma
//! furrboot-when      для игр и рабочего стола
//! furrboot-date      2026-11-10 21:40   # snapshots, local time
//! furrboot-tag       update             # update | install | important
//! furrboot-kernel    linux-furros
//! furrboot-type      автоматический (snap-pac)
//! ```

use crate::i18n::Lang;
use alloc::string::{String, ToString};
use alloc::vec::Vec;
use uefi::fs::FileSystem;
use uefi::proto::media::fs::SimpleFileSystem;
use uefi::{boot, CString16, Handle};

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Kind { Main, Kernel, Safe, Snapshot }

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug, Default)]
pub struct Stamp { pub y: u16, pub mo: u8, pub d: u8, pub h: u8, pub mi: u8 }

#[derive(Clone, Debug)]
pub struct Entry {
    pub id: String,
    pub title: String,
    pub kind: Kind,
    pub linux: String,
    pub initrd: Vec<String>,
    pub options: String,
    pub sort: String,
    pub subtitle: String,
    pub when: String,
    pub date: Option<Stamp>,
    pub tag: String,
    pub kernel: String,
    pub typ: String,
    /// file name in \loader\entries (with the boot counter, if any)
    pub file: String,
    /// boot counting (https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/): `name+LEFT-DONE.conf`
    pub tries_left: Option<u32>,
    pub tries_done: u32,
    /// `furrboot-volume <GPT partition GUID>`: the kernel and initrd are on that partition (FurrOS Btrfs, read
    /// through the efifs driver) instead of the one holding the entries
    pub part: String,
    pub volume: Option<Handle>,
}

impl Entry {
    /// Ran out of tries: it failed to boot several times in a row.
    pub fn bad(&self) -> bool { self.tries_left == Some(0) }
}

/// `furros+2-1` -> ("furros", Some(2), 1); `furros` -> ("furros", None, 0). Same rules as systemd-bless-boot:
/// "+LEFT", optionally "-DONE", at the end of the name.
pub fn split_counter(stem: &str) -> (&str, Option<u32>, u32) {
    if let Some(p) = stem.rfind('+') {
        let tail = &stem[p + 1..];
        let (l, d) = tail.split_once('-').unwrap_or((tail, "0"));
        let digits = |s: &str| !s.is_empty() && s.bytes().all(|b| b.is_ascii_digit());
        if digits(l) && digits(d) {
            if let (Ok(l), Ok(d)) = (l.parse(), d.parse()) { return (&stem[..p], Some(l), d); }
        }
    }
    (stem, None, 0)
}

pub struct Config {
    pub timeout: u32,
    pub default: String,
    pub lang: Lang,
    pub theme: String,
    pub tz_offset: i32, // minutes to add to the firmware clock to get local time
    /// boot the default entry without showing the menu (LoaderConfigTimeout 0 / menu-hidden)
    pub instant: bool,
    /// `resolution 1366x768` in furrboot.conf: use exactly this screen mode if the firmware has it
    pub resolution: Option<(usize, usize)>,
    /// `season auto|on|off`: the New Year look (snow, a garland), by default 15 December .. 15 January
    pub season: u8,
    /// the OS asked for Windows this time (LoaderEntryOneShot=auto-windows)
    pub boot_windows: bool,
    pub entries: Vec<Entry>,
    /// partition holding furrboot.conf and the kernels
    pub volume: Option<Handle>,
    /// partition holding \EFI\Microsoft\Boot\bootmgfw.efi
    pub windows: Option<Handle>,
    /// things worth showing on the F12 screen
    pub notes: Vec<String>,
    /// entries left out because their partition could not be read (the fs driver did not start)
    pub unreadable: usize,
}

fn path(s: &str) -> Option<CString16> { CString16::try_from(s.replace('/', "\\").as_str()).ok() }

fn open_fs(h: Handle) -> Option<FileSystem> {
    boot::open_protocol_exclusive::<SimpleFileSystem>(h).ok().map(FileSystem::new)
}

fn read_text(fs: &mut FileSystem, p: &str) -> Option<String> {
    let p = path(p)?;
    fs.read_to_string(p.as_ref()).ok()
}

fn exists(h: Handle, p: &str) -> bool {
    let (Some(mut fs), Some(p)) = (open_fs(h), path(p)) else { return false };
    fs.try_exists(p.as_ref()).unwrap_or(false)
}

fn parse_stamp(s: &str) -> Option<Stamp> {
    // "2026-11-10 21:40"
    let (d, t) = s.trim().split_once(' ').unwrap_or((s.trim(), "00:00"));
    let mut dp = d.split('-');
    let mut tp = t.split(':');
    Some(Stamp {
        y: dp.next()?.parse().ok()?,
        mo: dp.next()?.parse().ok()?,
        d: dp.next()?.parse().ok()?,
        h: tp.next().unwrap_or("0").parse().ok()?,
        mi: tp.next().unwrap_or("0").parse().ok()?,
    })
}

fn kv(line: &str) -> Option<(&str, &str)> {
    let line = line.trim();
    if line.is_empty() || line.starts_with('#') { return None; }
    match line.find(|c: char| c.is_whitespace()) {
        Some(i) => Some((&line[..i], line[i..].trim())),
        None => Some((line, "")),
    }
}

fn parse_entry(file: &str, text: &str) -> Option<Entry> {
    let (id, tries_left, tries_done) = split_counter(file.trim_end_matches(".conf"));
    let mut e = Entry {
        file: file.into(), tries_left, tries_done, part: String::new(), volume: None,
        id: id.into(), title: String::new(), kind: Kind::Kernel, linux: String::new(), initrd: Vec::new(), options: String::new(),
        sort: String::new(), subtitle: String::new(), when: String::new(), date: None, tag: String::new(), kernel: String::new(), typ: String::new(),
    };
    for line in text.lines() {
        let Some((k, v)) = kv(line) else { continue };
        match k {
            "title" => e.title = v.into(),
            "linux" => e.linux = v.into(),
            "initrd" => e.initrd.push(v.into()),
            "options" => { if !e.options.is_empty() { e.options.push(' '); } e.options.push_str(v); }
            "sort-key" => e.sort = v.into(),
            "furrboot-kind" => e.kind = match v { "main" => Kind::Main, "safe" => Kind::Safe, "snapshot" => Kind::Snapshot, _ => Kind::Kernel },
            "furrboot-subtitle" => e.subtitle = v.into(),
            "furrboot-when" => e.when = v.into(),
            "furrboot-date" => e.date = parse_stamp(v),
            "furrboot-tag" => e.tag = v.into(),
            "furrboot-kernel" => e.kernel = v.into(),
            "furrboot-type" => e.typ = v.into(),
            "furrboot-volume" => e.part = v.to_ascii_lowercase(),
            _ => {}
        }
    }
    if e.linux.is_empty() { return None; }
    if e.title.is_empty() { e.title = id.into(); }
    Some(e)
}

pub fn load() -> Config {
    let mut cfg = Config {
        timeout: 10, default: String::new(), lang: Lang::Ru, theme: "comic".into(), tz_offset: 0, instant: false, boot_windows: false, resolution: None, season: 0,
        entries: Vec::new(), volume: None, windows: None, notes: Vec::new(), unreadable: 0,
    };
    let handles = boot::find_handles::<SimpleFileSystem>().unwrap_or_default();
    // our own partition first
    let own = boot::open_protocol_exclusive::<uefi::proto::loaded_image::LoadedImage>(boot::image_handle())
        .ok().and_then(|li| li.device());
    let mut order: Vec<Handle> = Vec::new();
    if let Some(h) = own { order.push(h); }
    order.extend(handles.iter().copied().filter(|h| Some(*h) != own));

    for &h in &order {
        if cfg.windows.is_none() && exists(h, "\\EFI\\Microsoft\\Boot\\bootmgfw.efi") { cfg.windows = Some(h); }
        if cfg.volume.is_some() { continue; }
        let Some(mut fs) = open_fs(h) else { continue };
        let Some(text) = read_text(&mut fs, "\\loader\\furrboot.conf") else { continue };
        cfg.volume = Some(h);
        for line in text.lines() {
            let Some((k, v)) = kv(line) else { continue };
            match k {
                "timeout" => cfg.timeout = v.parse().unwrap_or(10),
                "default" => cfg.default = v.into(),
                "lang" => cfg.lang = Lang::from_code(v),
                "theme" => cfg.theme = v.into(),
                "tz-offset" => cfg.tz_offset = v.parse().unwrap_or(0),
                "season" => cfg.season = match v { "on" => 2, "off" => 1, _ => 0 },
                "resolution" => cfg.resolution = v.split_once('x').and_then(|(w, h)| Some((w.trim().parse().ok()?, h.trim().parse().ok()?))),
                _ => {}
            }
        }
        // entries
        if let Some(p) = path("\\loader\\entries") {
            if let Ok(dir) = fs.read_dir(p.as_ref()) {
                for info in dir.flatten() {
                    let name = info.file_name().to_string();
                    if !name.ends_with(".conf") || info.is_directory() { continue; }
                    if let Some(text) = read_text(&mut fs, &alloc::format!("\\loader\\entries\\{name}")) {
                        let Some(e) = parse_entry(&name, &text) else { continue };
                        // the same entry twice (a rename cut short by a power loss): keep the one with fewer tries left
                        match cfg.entries.iter_mut().find(|x| x.id == e.id) {
                            Some(x) => if e.tries_left.unwrap_or(u32::MAX) < x.tries_left.unwrap_or(u32::MAX) { *x = e; },
                            None => cfg.entries.push(e),
                        }
                    }
                }
            }
        }
    }
    // entries on another partition: find it among the readable ones; one that can't be read is left out
    // (no file-system driver, or the partition is gone) and said so on the F12 screen
    if cfg.entries.iter().any(|e| !e.part.is_empty()) {
        let parts: Vec<(String, Handle)> = handles.iter().filter_map(|&h| part_guid(h).map(|g| (g, h))).collect();
        for e in cfg.entries.iter_mut().filter(|e| !e.part.is_empty()) {
            e.volume = parts.iter().find(|(g, _)| *g == e.part).map(|(_, h)| *h);
        }
        let missing = cfg.entries.iter().filter(|e| !e.part.is_empty() && e.volume.is_none()).count();
        if missing > 0 {
            cfg.notes.push(alloc::format!("{missing} entries skipped: their partition is not readable (fs driver?)"));
            cfg.unreadable = missing;
        }
        cfg.entries.retain(|e| e.part.is_empty() || e.volume.is_some());
    }
    // stable order: entries that failed to boot go last, then sort-key, then newest snapshots first
    cfg.entries.sort_by(|a, b| a.bad().cmp(&b.bad()).then(match (a.kind, b.kind) {
        (Kind::Snapshot, Kind::Snapshot) => b.date.cmp(&a.date),
        _ => a.sort.cmp(&b.sort).then(a.id.cmp(&b.id)),
    }));
    cfg
}

impl Config {
    /// What the countdown starts: the default entry, unless it used up its boot tries (failed several times in a
    /// row); then the next kernel that still works — the spare one, like systemd-boot does.
    pub fn main_entry(&self) -> Option<&Entry> {
        let ok = |e: &&Entry| !e.bad();
        self.entries.iter().filter(ok).find(|e| e.id == self.default)
            .or_else(|| self.entries.iter().filter(ok).find(|e| e.kind == Kind::Main))
            .or_else(|| self.entries.iter().filter(ok).find(|e| e.kind == Kind::Kernel))
            .or_else(|| self.entries.iter().find(|e| e.id == self.default))
            .or_else(|| self.entries.iter().find(|e| e.kind == Kind::Main))
            .or_else(|| self.entries.iter().find(|e| e.kind == Kind::Kernel))
    }
    pub fn of(&self, k: Kind) -> Vec<&Entry> { self.entries.iter().filter(|e| e.kind == k).collect() }
    pub fn kernels(&self) -> Vec<&Entry> { self.entries.iter().filter(|e| matches!(e.kind, Kind::Main | Kind::Kernel)).collect() }
}

/// GPT partition GUID of a partition handle (lowercase), from the HardDrive node of its device path.
fn part_guid(h: Handle) -> Option<String> {
    use uefi::boot::{OpenProtocolAttributes, OpenProtocolParams};
    use uefi::proto::device_path::{media::{HardDrive, PartitionSignature}, DevicePath};
    // GET_PROTOCOL: an exclusive open would disconnect the drivers using this device path
    let dp = unsafe {
        boot::open_protocol::<DevicePath>(
            OpenProtocolParams { handle: h, agent: boot::image_handle(), controller: None },
            OpenProtocolAttributes::GetProtocol,
        )
    }.ok()?;
    for node in dp.node_iter() {
        if let Ok(hd) = <&HardDrive>::try_from(node) {
            if let PartitionSignature::Guid(g) = hd.partition_signature() { return Some(alloc::format!("{g}").to_ascii_lowercase()); }
        }
    }
    None
}
