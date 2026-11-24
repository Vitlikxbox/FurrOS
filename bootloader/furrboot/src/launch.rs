//! Starting things: a Linux kernel (EFI stub), Windows Boot Manager, firmware settings, reset.

use alloc::format;
use alloc::string::String;
use alloc::vec::Vec;
use core::mem::MaybeUninit;
use uefi::boot::{self, LoadImageSource, OpenProtocolAttributes, OpenProtocolParams};
use uefi::proto::BootPolicy;
use uefi::proto::device_path::build::{media::FilePath, DevicePathBuilder};
use uefi::proto::device_path::DevicePath;
use uefi::proto::loaded_image::LoadedImage;
use uefi::runtime::{self, ResetType, VariableAttributes, VariableVendor};
use uefi::{cstr16, CString16, Handle, Status};

fn efi_path(p: &str) -> String {
    let mut s = p.trim().replace('/', "\\");
    if !s.starts_with('\\') { s.insert(0, '\\'); }
    s
}

/// Load an image from a file on a partition, through the firmware (so the loaded image knows
/// its device: the kernel's EFI stub reads `initrd=` files from that same partition).
pub fn load_file_image(vol: Handle, file: &str) -> uefi::Result<Handle> {
    let vol_dp = unsafe {
        boot::open_protocol::<DevicePath>(
            OpenProtocolParams { handle: vol, agent: boot::image_handle(), controller: None },
            OpenProtocolAttributes::GetProtocol,
        )?
    };
    let name = CString16::try_from(efi_path(file).as_str()).map_err(|_| Status::INVALID_PARAMETER)?;
    let mut buf = [MaybeUninit::uninit(); 1024];
    let file_dp = DevicePathBuilder::with_buf(&mut buf)
        .push(&FilePath { path_name: &name }).map_err(|_| Status::BUFFER_TOO_SMALL)?
        .finalize().map_err(|_| Status::BUFFER_TOO_SMALL)?;
    let full = vol_dp.append_path(file_dp).map_err(|_| Status::OUT_OF_RESOURCES)?;
    boot::load_image(boot::image_handle(), LoadImageSource::FromDevicePath { device_path: &full, boot_policy: BootPolicy::ExactMatch })
}

/// Start a Linux kernel. Returns only if it failed.
pub fn linux(vol: Handle, kernel: &str, initrds: &[String], options: &str) -> uefi::Result {
    let img = load_file_image(vol, kernel)?;
    let mut cmd = String::new();
    for i in initrds {
        cmd.push_str("initrd=");
        cmd.push_str(&efi_path(i));
        cmd.push(' ');
    }
    cmd.push_str(options.trim());
    let cmd16 = CString16::try_from(cmd.as_str()).map_err(|_| Status::INVALID_PARAMETER)?;
    {
        let mut li = boot::open_protocol_exclusive::<LoadedImage>(img)?;
        // size in bytes including the terminating NUL; cmd16 lives until start_image returns
        let bytes = cmd16.num_bytes() as u32;
        unsafe { li.set_load_options(cmd16.as_ptr().cast(), bytes) };
    }
    let r = boot::start_image(img);
    let _ = boot::unload_image(img);
    drop(cmd16);
    r
}

/// Chain-load Windows Boot Manager.
pub fn windows(vol: Handle) -> uefi::Result {
    let img = load_file_image(vol, "\\EFI\\Microsoft\\Boot\\bootmgfw.efi")?;
    let r = boot::start_image(img);
    let _ = boot::unload_image(img);
    r
}

const BOOT_TO_FW_UI: u64 = 1;

pub fn firmware_ui_supported() -> bool {
    runtime::get_variable_boxed(cstr16!("OsIndicationsSupported"), &VariableVendor::GLOBAL_VARIABLE)
        .ok()
        .and_then(|(v, _)| v.get(..8).map(|b| u64::from_le_bytes(b.try_into().unwrap_or([0; 8]))))
        .is_some_and(|v| v & BOOT_TO_FW_UI != 0)
}

/// Ask the firmware to open its setup screen on the next start, then restart.
pub fn firmware_ui() -> uefi::Result {
    let cur = runtime::get_variable_boxed(cstr16!("OsIndications"), &VariableVendor::GLOBAL_VARIABLE)
        .ok()
        .and_then(|(v, _)| v.get(..8).map(|b| u64::from_le_bytes(b.try_into().unwrap_or([0; 8]))))
        .unwrap_or(0);
    let val = (cur | BOOT_TO_FW_UI).to_le_bytes();
    let attrs = VariableAttributes::NON_VOLATILE | VariableAttributes::BOOTSERVICE_ACCESS | VariableAttributes::RUNTIME_ACCESS;
    runtime::set_variable(cstr16!("OsIndications"), &VariableVendor::GLOBAL_VARIABLE, attrs, &val)?;
    runtime::reset(ResetType::COLD, Status::SUCCESS, None)
}

pub fn reboot() -> ! { runtime::reset(ResetType::COLD, Status::SUCCESS, None) }
pub fn poweroff() -> ! { runtime::reset(ResetType::SHUTDOWN, Status::SUCCESS, None) }

pub fn describe(e: &uefi::Error) -> String {
    let s = e.status();
    let name = match s {
        Status::NOT_FOUND => "file not found",
        Status::LOAD_ERROR => "load error",
        Status::SECURITY_VIOLATION | Status::ACCESS_DENIED => "Secure Boot blocked it",
        Status::OUT_OF_RESOURCES => "out of memory",
        Status::UNSUPPORTED => "unsupported",
        Status::INVALID_PARAMETER => "invalid parameter",
        _ => "",
    };
    if name.is_empty() { format!("{s:?}") } else { format!("{name} ({s:?})") }
}

#[allow(dead_code)]
fn _keep(_: Vec<u8>) {}
