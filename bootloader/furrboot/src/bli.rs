//! systemd Boot Loader Interface (https://systemd.io/BOOT_LOADER_INTERFACE/).
//! Lets FurrOS talk to FurrBoot the same way it talks to systemd-boot:
//! `systemctl reboot --boot-loader-entry=auto-windows`, `bootctl set-oneshot`, `bootctl set-timeout`,
//! `systemd-analyze` (firmware/loader time), `bootctl status`.
//!
//! All variables live under vendor GUID 4a67b082-0a4c-41cf-b6c7-440b29bb8c4f and hold NUL-terminated UTF-16
//! strings. Entry identifiers are the entry file names (`furros.conf`), like in systemd-boot; Windows is
//! `auto-windows`.

use crate::config::Config;
use alloc::string::String;
use alloc::vec::Vec;
use core::sync::atomic::{AtomicU64, Ordering};
use uefi::proto::device_path::{media::HardDrive, DevicePath};
use uefi::proto::device_path::media::PartitionSignature;
use uefi::proto::loaded_image::LoadedImage;
use uefi::runtime::{self, VariableAttributes, VariableVendor};
use uefi::boot::{OpenProtocolAttributes, OpenProtocolParams};
use uefi::{boot, cstr16, guid, CStr16};

const VENDOR: VariableVendor = VariableVendor(guid!("4a67b082-0a4c-41cf-b6c7-440b29bb8c4f"));
pub const WINDOWS_ID: &str = "auto-windows";

// LoaderFeatures bits we honour: ConfigTimeout, ConfigTimeoutOneShot, EntryDefault, EntryOneShot, boot counting
const FEATURES: u64 = 1 | 2 | 4 | 8 | 16;

static START_TSC: AtomicU64 = AtomicU64::new(0);

fn tsc() -> u64 { unsafe { core::arch::x86_64::_rdtsc() } }

/// Call first thing in main: the TSC counts from CPU reset, so this is "time spent in firmware".
pub fn mark_start() { START_TSC.store(tsc(), Ordering::Relaxed); }

fn volatile() -> VariableAttributes { VariableAttributes::BOOTSERVICE_ACCESS | VariableAttributes::RUNTIME_ACCESS }

fn utf16(s: &str) -> Vec<u8> {
    let mut v = Vec::with_capacity(s.len() * 2 + 2);
    for c in s.encode_utf16().chain(core::iter::once(0)) { v.extend_from_slice(&c.to_le_bytes()); }
    v
}

fn set_str(name: &CStr16, s: &str) { let _ = runtime::set_variable(name, &VENDOR, volatile(), &utf16(s)); }

fn get_str(name: &CStr16) -> Option<String> {
    let (data, _) = runtime::get_variable_boxed(name, &VENDOR).ok()?;
    let units: Vec<u16> = data.chunks_exact(2).map(|b| u16::from_le_bytes([b[0], b[1]])).take_while(|&c| c != 0).collect();
    let s = String::from_utf16(&units).ok()?;
    let s = s.trim();
    if s.is_empty() { None } else { Some(s.into()) }
}

fn take_str(name: &CStr16) -> Option<String> {
    let v = get_str(name);
    if v.is_some() { let _ = runtime::delete_variable(name, &VENDOR); }
    v
}

fn entry_id(id: &str) -> String { alloc::format!("{id}.conf") }

/// What the OS asked for, applied on top of furrboot.conf.
pub fn apply(cfg: &mut Config) {
    // timeout: one-shot wins over the persistent one, which wins over the config file
    let one = take_str(cstr16!("LoaderConfigTimeoutOneShot"));
    let persistent = get_str(cstr16!("LoaderConfigTimeout"));
    if let Some(t) = one {
        // for the one-shot variable 0 means "show the menu and wait"
        match t.parse::<u32>() { Ok(n) => cfg.timeout = n, Err(_) => apply_timeout_word(cfg, &t) }
    } else if let Some(t) = persistent {
        match t.parse::<u32>() {
            Ok(0) => cfg.instant = true,
            Ok(n) => cfg.timeout = n,
            Err(_) => apply_timeout_word(cfg, &t),
        }
    }
    // default entry, then the one-shot one (removed after reading, as the spec says)
    if let Some(d) = get_str(cstr16!("LoaderEntryDefault")) { pick(cfg, &d, false); }
    if let Some(d) = take_str(cstr16!("LoaderEntryOneShot")) { pick(cfg, &d, true); }
}

fn apply_timeout_word(cfg: &mut Config, w: &str) {
    match w {
        "menu-force" => cfg.timeout = 0,
        "menu-hidden" | "menu-disabled" => cfg.instant = true,
        _ => {}
    }
}

fn pick(cfg: &mut Config, id: &str, one_shot: bool) {
    if id == WINDOWS_ID {
        if cfg.windows.is_some() { cfg.boot_windows = true; }
        return;
    }
    let id = id.trim_end_matches(".conf");
    if cfg.entries.iter().any(|e| e.id == id) {
        cfg.default = id.into();
        if one_shot { cfg.boot_windows = false; }
    }
}

/// Variables the loader publishes for the OS (volatile: they describe this boot only).
pub fn publish(cfg: &Config, per_ms: f32) {
    set_str(cstr16!("LoaderInfo"), concat!("FurrBoot ", env!("CARGO_PKG_VERSION")));
    let _ = runtime::set_variable(cstr16!("LoaderFeatures"), &VENDOR, volatile(), &FEATURES.to_le_bytes());
    let mut list = Vec::new();
    for e in &cfg.entries { list.extend_from_slice(&utf16(&entry_id(&e.id))); }
    if cfg.windows.is_some() { list.extend_from_slice(&utf16(WINDOWS_ID)); }
    let _ = runtime::set_variable(cstr16!("LoaderEntries"), &VENDOR, volatile(), &list);
    if let Some(u) = usec(START_TSC.load(Ordering::Relaxed), per_ms) { set_str(cstr16!("LoaderTimeInitUSec"), &alloc::format!("{u}")); }
    if let Some(g) = own_partition_uuid() { set_str(cstr16!("LoaderDevicePartUUID"), &g); }
}

/// Right before handing over to an OS.
pub fn before_launch(id: Option<&str>, per_ms: f32) {
    let sel = match id { Some(i) => entry_id(i), None => WINDOWS_ID.into() };
    set_str(cstr16!("LoaderEntrySelected"), &sel);
    if let Some(u) = usec(tsc(), per_ms) { set_str(cstr16!("LoaderTimeExecUSec"), &alloc::format!("{u}")); }
}

fn usec(t: u64, per_ms: f32) -> Option<u64> {
    let per_ms = per_ms as u64;
    if per_ms == 0 || t == 0 { return None; }
    Some((t as u128 * 1000 / per_ms as u128) as u64)
}

/// GPT partition GUID of the ESP we were started from, uppercase like systemd-boot writes it.
fn own_partition_uuid() -> Option<String> {
    let li = boot::open_protocol_exclusive::<LoadedImage>(boot::image_handle()).ok()?;
    let dev = li.device()?;
    // GET_PROTOCOL: an exclusive open would disconnect the disk drivers that use this device path
    let dp = unsafe {
        boot::open_protocol::<DevicePath>(
            OpenProtocolParams { handle: dev, agent: boot::image_handle(), controller: None },
            OpenProtocolAttributes::GetProtocol,
        )
    }.ok()?;
    for node in dp.node_iter() {
        if let Ok(hd) = <&HardDrive>::try_from(node) {
            if let PartitionSignature::Guid(g) = hd.partition_signature() {
                return Some(alloc::format!("{g}").to_uppercase());
            }
        }
    }
    None
}

/// For the F12 screen: read back what we published, as the OS will see it.
pub fn status_lines() -> Vec<String> {
    let mut v = Vec::new();
    let info = get_str(cstr16!("LoaderInfo")).unwrap_or_else(|| "-".into());
    let n = runtime::get_variable_boxed(cstr16!("LoaderEntries"), &VENDOR)
        .map(|(d, _)| d.chunks_exact(2).filter(|b| b[0] == 0 && b[1] == 0).count()).unwrap_or(0);
    let init = get_str(cstr16!("LoaderTimeInitUSec")).and_then(|s| s.parse::<u64>().ok()).map(|u| u / 1000).unwrap_or(0);
    v.push(alloc::format!("boot loader interface: {info}, {n} entries, firmware took {init} ms"));
    v.push(alloc::format!("ESP partition: {}", get_str(cstr16!("LoaderDevicePartUUID")).unwrap_or_else(|| "-".into())));
    v
}

/// Boot counting (https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/): before an entry named `name+LEFT-DONE.conf`
/// starts, it is renamed to `name+(LEFT-1)-(DONE+1).conf`, and LoaderBootCountPath tells systemd-bless-boot
/// which file to rename to plain `name.conf` once the system came up fine (systemd-bless-boot.service(8): the
/// path is relative to the boot partition; systemd reads it as UTF-16 and turns backslashes into slashes).
/// An entry already at +0 is booted as it is (somebody picked it by hand), and still reported, so a good boot
/// makes it usable again.
pub fn count_attempt(vol: uefi::Handle, e: &mut crate::config::Entry) {
    let Some(left) = e.tries_left else { return };
    let mut name = e.file.clone();
    if left > 0 {
        let new = alloc::format!("{}+{}-{}.conf", e.id, left - 1, e.tries_done + 1);
        match rename_entry(vol, &e.file, &new) {
            Ok(()) => {
                // keep the entry in step with the disk, in case this start fails and it is picked again
                e.file = new.clone();
                e.tries_left = Some(left - 1);
                e.tries_done += 1;
                name = new;
            }
            Err(err) => log::warn!("boot counter: can't rename {}: {:?}", e.file, err.status()),
        }
    }
    set_str(cstr16!("LoaderBootCountPath"), &alloc::format!(r"\loader\entries\{name}"));
}

/// Rename a file in \loader\entries in place: EFI_FILE_PROTOCOL.SetInfo with a new FileName (UEFI 2.10 §13.5),
/// one directory-entry update on FAT — unlike uefi::fs::FileSystem::rename, which copies and then deletes.
fn rename_entry(vol: uefi::Handle, old: &str, new: &str) -> uefi::Result {
    use uefi::proto::media::file::{File, FileAttribute, FileInfo, FileMode};
    use uefi::proto::media::fs::SimpleFileSystem;
    use uefi::{CString16, Status};
    let mut sfs = boot::open_protocol_exclusive::<SimpleFileSystem>(vol)?;
    let mut root = sfs.open_volume()?;
    let path = CString16::try_from(alloc::format!(r"\loader\entries\{old}").as_str()).map_err(|_| Status::INVALID_PARAMETER)?;
    let mut f = root.open(&path, FileMode::ReadWrite, FileAttribute::empty())?
        .into_regular_file().ok_or(Status::INVALID_PARAMETER)?;
    let info = f.get_boxed_info::<FileInfo>()?;
    let name = CString16::try_from(new).map_err(|_| Status::INVALID_PARAMETER)?;
    // FileInfo is 8-byte aligned and ends with the name: build it in a u64 buffer
    let mut storage = alloc::vec![0u64; (80 + (new.len() + 1) * 2) / 8 + 2];
    let bytes = unsafe { core::slice::from_raw_parts_mut(storage.as_mut_ptr().cast::<u8>(), storage.len() * 8) };
    let new_info = FileInfo::new(bytes, info.file_size(), info.physical_size(), *info.create_time(),
        *info.last_access_time(), *info.modification_time(), info.attribute(), &name)
        .map_err(|_| Status::BUFFER_TOO_SMALL)?;
    f.set_info(new_info)?;
    f.flush()?;
    Ok(())
}
