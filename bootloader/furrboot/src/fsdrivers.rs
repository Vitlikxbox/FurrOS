//! UEFI file-system drivers shipped next to FurrBoot in `\EFI\FurrOS\drivers\*.efi` — for FurrOS the Btrfs one
//! from efifs (https://github.com/pbatard/efifs, GPL-3.0, read-only, built from GRUB's file-system code).
//! With it the firmware reads the FurrOS Btrfs partition itself, so kernels and snapshots start straight from
//! it instead of being copied to an EFI partition that Windows made 100–200 MiB small.
//!
//! A driver started by an application only installs its Driver Binding; it has to be connected to the
//! controllers afterwards (UEFI 2.10 §7.3.12 ConnectController — what the efifs README does with `map -r`).

use alloc::format;
use alloc::string::{String, ToString};
use alloc::vec::Vec;
use uefi::boot::{self, SearchType};
use uefi::fs::FileSystem;
use uefi::proto::loaded_image::LoadedImage;
use uefi::proto::media::fs::SimpleFileSystem;
use uefi::CString16;

/// Load and start every driver found, then connect them. Returns lines for the F12 screen.
pub fn load() -> Vec<String> {
    let mut diag = Vec::new();
    let own = boot::open_protocol_exclusive::<LoadedImage>(boot::image_handle()).ok().and_then(|li| li.device());
    let Some(dev) = own else { return diag };
    // list the drivers first, then let go of the file system (loading opens it again through the firmware)
    let names: Vec<String> = {
        let Ok(sfs) = boot::open_protocol_exclusive::<SimpleFileSystem>(dev) else { return diag };
        let mut fs = FileSystem::new(sfs);
        let Ok(dir) = CString16::try_from("\\EFI\\FurrOS\\drivers") else { return diag };
        match fs.read_dir(dir.as_ref()) {
            Ok(it) => it.flatten()
                .filter(|i| !i.is_directory())
                .map(|i| i.file_name().to_string())
                .filter(|n| n.to_ascii_lowercase().ends_with("x64.efi"))
                .collect(),
            Err(_) => return diag,
        }
    };
    let mut started = 0;
    for n in &names {
        let path = format!("\\EFI\\FurrOS\\drivers\\{n}");
        match crate::launch::load_file_image(dev, &path).and_then(|img| boot::start_image(img).map(|_| img)) {
            Ok(_) => { started += 1; diag.push(format!("fs driver {n}: started")); }
            Err(e) => diag.push(format!("fs driver {n}: {:?}", e.status())),
        }
    }
    if started > 0 {
        let t0 = crate::clock::ms();
        if let Ok(buf) = boot::locate_handle_buffer(SearchType::AllHandles) {
            for h in buf.iter() { let _ = boot::connect_controller(*h, &[], None, true); }
        }
        let n = boot::find_handles::<SimpleFileSystem>().map(|v| v.len()).unwrap_or(0);
        diag.push(format!("fs drivers connected in {:.0} ms: {n} readable partitions", crate::clock::ms() - t0));
    }
    diag
}
