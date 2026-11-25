//! Write-combining for the GOP frame buffer.
//!
//! Firmware usually maps the frame buffer uncached (UC): every pixel store is its own PCIe write, so a
//! 1920×1080 frame takes ~80 ms (measured: "Blt 77 ms/frame (direct 76)"). Linux maps the same memory
//! write-combining (WC), which batches stores into full bursts and is tens of times faster.
//! The PI spec's DXE Services (GCD) let a boot application ask for that: SetMemorySpaceAttributes.
//! If the firmware has no DXE Services table, or the range doesn't support WC, nothing changes.

use core::ffi::c_void;
use uefi::Status;
use uefi::table::cfg::ConfigTableEntry;

const EFI_MEMORY_UC: u64 = 0x1;
const EFI_MEMORY_WC: u64 = 0x2;
const EFI_MEMORY_WT: u64 = 0x4;
const EFI_MEMORY_WB: u64 = 0x8;
const EFI_MEMORY_UCE: u64 = 0x10;
const CACHE_MASK: u64 = EFI_MEMORY_UC | EFI_MEMORY_WC | EFI_MEMORY_WT | EFI_MEMORY_WB | EFI_MEMORY_UCE;

#[repr(C)]
struct TableHeader { signature: u64, revision: u32, header_size: u32, crc32: u32, reserved: u32 }

#[repr(C)]
#[derive(Default)]
struct GcdMemorySpaceDescriptor {
    base_address: u64,
    length: u64,
    capabilities: u64,
    attributes: u64,
    gcd_memory_type: u32,
    image_handle: usize,
    device_handle: usize,
}

/// EFI_DXE_SERVICES (PI spec, vol. 2): only the members up to SetMemorySpaceAttributes are used.
#[repr(C)]
struct DxeServices {
    hdr: TableHeader,
    add_memory_space: usize,
    allocate_memory_space: usize,
    free_memory_space: usize,
    remove_memory_space: usize,
    get_memory_space_descriptor: unsafe extern "efiapi" fn(u64, *mut GcdMemorySpaceDescriptor) -> Status,
    set_memory_space_attributes: unsafe extern "efiapi" fn(u64, u64, u64) -> Status,
}

const DXE_SIGNATURE: u64 = u64::from_le_bytes(*b"DXE_SERV");

fn cache_name(a: u64) -> &'static str {
    match a & CACHE_MASK {
        x if x & EFI_MEMORY_WC != 0 => "WC",
        x if x & EFI_MEMORY_WB != 0 => "WB",
        x if x & EFI_MEMORY_WT != 0 => "WT",
        x if x & EFI_MEMORY_UC != 0 => "UC",
        0 => "none",
        _ => "?",
    }
}

/// Ask for write-combining on [base, base+size). Returns a line for the F12 screen.
pub fn enable(base: u64, size: usize) -> alloc::string::String {
    use alloc::format;
    if base == 0 || size == 0 { return "frame buffer WC: no linear frame buffer".into(); }
    let table = uefi::system::with_config_table(|t| {
        t.iter().find(|e| e.guid == ConfigTableEntry::DXE_SERVICES_GUID).map(|e| e.address)
    });
    let Some(addr) = table else { return "frame buffer WC: no DXE Services table".into() };
    let dxe = unsafe { &*(addr as *const c_void as *const DxeServices) };
    if dxe.hdr.signature != DXE_SIGNATURE { return "frame buffer WC: bad DXE Services signature".into(); }

    // whole 4 KiB pages
    let start = base & !0xFFF;
    let end = (base + size as u64 + 0xFFF) & !0xFFF;
    let len = end - start;

    let mut d = GcdMemorySpaceDescriptor::default();
    let st = unsafe { (dxe.get_memory_space_descriptor)(start, &mut d) };
    if st.is_error() { return format!("frame buffer WC: GetMemorySpaceDescriptor {st:?}"); }
    let before = cache_name(d.attributes);
    if d.attributes & EFI_MEMORY_WC != 0 { return format!("frame buffer WC: already WC at {start:#x}"); }
    if d.capabilities & EFI_MEMORY_WC == 0 {
        // the firmware won't do it (AMI here: caps UC|WT|WB, a 1 GiB UC MTRR over the WT one, so the
        // frame buffer is effectively UC): program the variable MTRRs ourselves, undone before any launch
        return format!("frame buffer WC: GCD no (caps {:#x}, {before}); MTRR: {}", d.capabilities, mtrr::apply(start, len));
    }
    let attrs = (d.attributes & !CACHE_MASK) | EFI_MEMORY_WC;
    let st = unsafe { (dxe.set_memory_space_attributes)(start, len, attrs) };
    if st.is_error() {
        return format!("frame buffer WC: GCD {st:?}; MTRR: {}", mtrr::apply(start, len));
    }
    format!("frame buffer WC: on ({before} -> WC, {start:#x}+{:.1} MiB)", len as f64 / 1048576.0)
}

/// Put the MTRRs back the way the firmware left them (before starting Linux/Windows/firmware UI).
pub fn restore() { mtrr::restore(); }
/// Back to WC after a launch came back with an error and the menu is shown again.
pub fn reapply() { mtrr::reapply(); }

/// Variable-range MTRRs, programmed on this (the boot) processor only while the menu is up.
/// The original values are written back before anything is started, so the OS gets the firmware's setup.
mod mtrr {
    use alloc::format;
    use alloc::string::String;
    use alloc::vec::Vec;
    use core::arch::asm;
    use core::cell::UnsafeCell;

    const IA32_MTRRCAP: u32 = 0xFE;
    const IA32_MTRR_DEF_TYPE: u32 = 0x2FF;
    const IA32_MTRR_PHYSBASE0: u32 = 0x200;
    const VALID: u64 = 1 << 11;
    const T_UC: u64 = 0;
    const T_WC: u64 = 1;

    struct State { orig: Option<Vec<(u64, u64)>>, new: Option<Vec<(u64, u64)>>, active: bool }
    struct Global(UnsafeCell<State>);
    unsafe impl Sync for Global {} // UEFI boot services: one thread
    static STATE: Global = Global(UnsafeCell::new(State { orig: None, new: None, active: false }));
    fn st() -> &'static mut State { unsafe { &mut *STATE.0.get() } }

    unsafe fn rdmsr(msr: u32) -> u64 {
        let (lo, hi): (u32, u32);
        unsafe { asm!("rdmsr", in("ecx") msr, out("eax") lo, out("edx") hi, options(nomem, nostack, preserves_flags)) };
        ((hi as u64) << 32) | lo as u64
    }
    unsafe fn wrmsr(msr: u32, v: u64) {
        unsafe { asm!("wrmsr", in("ecx") msr, in("eax") v as u32, in("edx") (v >> 32) as u32, options(nostack, preserves_flags)) };
    }

    fn phys_bits() -> u32 {
        let max_ext = core::arch::x86_64::__cpuid(0x8000_0000).eax;
        if max_ext >= 0x8000_0008 { core::arch::x86_64::__cpuid(0x8000_0008).eax & 0xFF } else { 36 }
    }

    /// Intel SDM vol. 3A 11.11.7.2 / 11.11.8: caches off, flush, MTRRs off, write, flush, back on.
    unsafe fn write_all(pairs: &[(u64, u64)]) {
        unsafe {
            let flags: u64;
            asm!("pushfq; pop {}; cli", out(reg) flags);
            let cr0: u64; asm!("mov {}, cr0", out(reg) cr0);
            let cr4: u64; asm!("mov {}, cr4", out(reg) cr4);
            asm!("mov cr0, {}", in(reg) (cr0 | (1 << 30)) & !(1 << 29)); // CD=1, NW=0
            asm!("wbinvd");
            if cr4 & (1 << 7) != 0 { asm!("mov cr4, {}", in(reg) cr4 & !(1 << 7)); } // PGE off: flush global TLB
            asm!("mov {0}, cr3; mov cr3, {0}", out(reg) _);
            let def = rdmsr(IA32_MTRR_DEF_TYPE);
            wrmsr(IA32_MTRR_DEF_TYPE, def & !(1 << 11));
            for (i, &(b, m)) in pairs.iter().enumerate() {
                wrmsr(IA32_MTRR_PHYSBASE0 + 2 * i as u32 + 1, 0); // mask first: never a half-written range
                wrmsr(IA32_MTRR_PHYSBASE0 + 2 * i as u32, b);
                wrmsr(IA32_MTRR_PHYSBASE0 + 2 * i as u32 + 1, m);
            }
            asm!("wbinvd");
            asm!("mov {0}, cr3; mov cr3, {0}", out(reg) _);
            wrmsr(IA32_MTRR_DEF_TYPE, def);
            asm!("mov cr0, {}", in(reg) cr0);
            asm!("mov cr4, {}", in(reg) cr4);
            if flags & (1 << 9) != 0 { asm!("sti"); }
        }
    }

    pub fn apply(fb: u64, fb_len: u64) -> String {
        let cap = unsafe { rdmsr(IA32_MTRRCAP) };
        let vcnt = (cap & 0xFF) as usize;
        if cap & (1 << 10) == 0 { return "CPU has no WC type".into(); }
        let def = unsafe { rdmsr(IA32_MTRR_DEF_TYPE) };
        if def & (1 << 11) == 0 { return "MTRRs are off".into(); }
        if vcnt == 0 || vcnt > 32 { return format!("{vcnt} variable MTRRs?"); }
        let pm = ((1u64 << phys_bits()) - 1) & !0xFFF; // physical address mask
        let orig: Vec<(u64, u64)> = (0..vcnt).map(|i| unsafe {
            (rdmsr(IA32_MTRR_PHYSBASE0 + 2 * i as u32), rdmsr(IA32_MTRR_PHYSBASE0 + 2 * i as u32 + 1))
        }).collect();
        // (base, size, type) of the valid ones
        let range = |&(b, m): &(u64, u64)| -> Option<(u64, u64, u64)> {
            if m & VALID == 0 { return None; }
            Some((b & pm, (!(m & pm) & pm) + 0x1000, b & 0xFF))
        };
        let covers = |(b, s): (u64, u64), x: u64, l: u64| b <= x && x + l <= b + s;
        // the block to make WC: the smallest non-UC range that holds the whole frame buffer (here the
        // firmware's WT entry for the BAR), else the power-of-two block around it
        let r = orig.iter().filter_map(range)
            .filter(|&(b, s, t)| t != T_UC && covers((b, s), fb, fb_len))
            .min_by_key(|&(_, s, _)| s)
            .map(|(b, s, _)| (b, s))
            .unwrap_or_else(|| { let s = fb_len.next_power_of_two().max(0x1000); (fb & !(s - 1), s) });
        if !covers(r, fb, fb_len) { return "frame buffer crosses a block boundary".into(); }
        let mk = |b: u64, s: u64, t: u64| (b | t, (!(s - 1) & pm) | VALID);
        let mut out: Vec<(u64, u64)> = Vec::new();
        let mut have_r = false;
        let mut split = 0;
        for (b, s, t) in orig.iter().filter_map(range) {
            if (b, s) == r { out.push(mk(b, s, T_WC)); have_r = true; continue; }
            if s > r.1 && covers((b, s), r.0, r.1) {
                // a bigger range over the block (the 1 GiB UC one): keep everything of it except the block,
                // as halves that don't contain it, down to the block's size
                let (mut cb, mut cs) = (b, s);
                while cs > r.1 {
                    cs /= 2;
                    if r.0 < cb + cs { out.push(mk(cb + cs, cs, t)); } else { out.push(mk(cb, cs, t)); cb += cs; }
                }
                split += 1;
                continue;
            }
            out.push(mk(b, s, t));
        }
        if !have_r { out.push(mk(r.0, r.1, T_WC)); }
        if out.len() > vcnt { return format!("needs {} MTRRs, has {vcnt}", out.len()); }
        out.resize(vcnt, (0, 0));
        unsafe { write_all(&out) };
        let s = st();
        s.orig = Some(orig); s.new = Some(out); s.active = true;
        format!("on, {:#x}+{} MiB WC ({} split, {} of {vcnt} used)", r.0, r.1 >> 20, split,
            s.new.as_ref().map_or(0, |v| v.iter().filter(|p| p.1 & VALID != 0).count()))
    }

    pub fn restore() {
        let s = st();
        if s.active { if let Some(o) = &s.orig { unsafe { write_all(o) }; s.active = false; } }
    }
    pub fn reapply() {
        let s = st();
        if !s.active { if let Some(n) = &s.new { unsafe { write_all(n) }; s.active = true; } }
    }
}
