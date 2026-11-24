//! Pointer devices: mouse, touchpad, touch screen, a VM's tablet.
//!
//! UEFI 2.10 §3 ("Boot Manager"): a fast-booting platform may connect only some consoles, and ConIn
//! is "always a proper subset of" ConInDev — a mouse that is not a default console is often simply
//! not started. An application may ask the boot manager to connect a device class through
//! EFI_BOOT_MANAGER_POLICY_PROTOCOL (§3.1.4); if that is missing, the spec's "Connect All Handles"
//! example (§7.3.12) calls ConnectController(handle, NULL, NULL, TRUE) on every handle.
//!
//! edk2's console splitter puts a Simple Pointer and an Absolute Pointer on the virtual ConIn handle
//! even when no real mouse exists, so "a pointer handle exists" proves nothing: only handles other
//! than ConIn count as real devices. Everything is opened with GET_PROTOCOL (not exclusively), so the
//! splitter keeps working; we poll the real devices and the splitter alike.
//! GetState returns EFI_NOT_READY when nothing changed (§12.5, §12.7).

use alloc::format;
use alloc::string::String;
use alloc::vec::Vec;
use uefi::boot::{self, OpenProtocolAttributes, OpenProtocolParams, ScopedProtocol, SearchType};
use uefi::proto::console::pointer::{AbsolutePointer, Pointer};
use uefi::proto::unsafe_protocol;
use uefi::proto::ProtocolPointer;
use uefi::{guid, Guid, Handle, Status};

/// EFI_BOOT_MANAGER_POLICY_PROTOCOL (UEFI 2.10 §3.1.4)
#[repr(C)]
#[unsafe_protocol("fedf8e0c-e147-11e3-9903-b8e8562cbafa")]
pub struct BootManagerPolicy {
    revision: u64,
    connect_device_path: unsafe extern "efiapi" fn(this: *mut Self, dp: *const core::ffi::c_void, recursive: u8) -> Status,
    connect_device_class: unsafe extern "efiapi" fn(this: *mut Self, class: *const Guid) -> Status,
}

const POLICY_CONSOLE: Guid = guid!("cab0e94c-e15f-11e3-918d-b8e8562cbafa");
const POLICY_CONNECT_ALL: Guid = guid!("113b2126-fc8a-11e3-bd6c-b8e8562cbafa");

fn con_in_handle() -> Option<Handle> {
    let st = uefi::table::system_table_raw()?;
    unsafe { Handle::from_ptr(st.as_ref().stdin_handle) }
}

fn get<P: ProtocolPointer + ?Sized>(h: Handle) -> Option<ScopedProtocol<P>> {
    unsafe {
        boot::open_protocol::<P>(
            OpenProtocolParams { handle: h, agent: boot::image_handle(), controller: None },
            OpenProtocolAttributes::GetProtocol,
        )
    }
    .ok()
}

/// Real pointer devices (not the console splitter's virtual one).
fn real_devices() -> usize {
    let con = con_in_handle();
    let a = boot::find_handles::<AbsolutePointer>().unwrap_or_default();
    let r = boot::find_handles::<Pointer>().unwrap_or_default();
    a.iter().chain(r.iter()).filter(|h| Some(**h) != con).count()
}

fn connect_class(class: &Guid) -> bool {
    let Ok(h) = boot::get_handle_for_protocol::<BootManagerPolicy>() else { return false };
    let Some(mut p) = get::<BootManagerPolicy>(h) else { return false };
    let me: *mut BootManagerPolicy = &mut *p;
    // only allowed at TPL_APPLICATION (§3.1.4) — which is where a boot application runs
    unsafe { ((*me).connect_device_class)(me, class) }.is_success()
}

fn connect_all_handles() {
    if let Ok(buf) = boot::locate_handle_buffer(SearchType::AllHandles) {
        for h in buf.iter() {
            let _ = boot::connect_controller(*h, &[], None, true);
        }
    }
}

pub struct Pointers {
    abs: Vec<(ScopedProtocol<AbsolutePointer>, bool)>, // (device, is the console splitter)
    rel: Vec<(ScopedProtocol<Pointer>, bool)>,
    pub info: Info,
}

#[derive(Default, Clone)]
pub struct Info {
    pub real: usize,
    pub abs: usize,
    pub rel: usize,
    pub connected: &'static str,
    pub connect_ms: f32,
    pub reads_ok: u32,
    pub reads_err: u32,
    pub last: String,
}

/// One pointer reading: where (pixels, absolute devices only) or how far (relative), button.
pub enum Event { Abs(f32, f32, bool), Rel(f32, f32, bool) }

impl Pointers {
    /// Start pointer drivers if needed, then open every pointer device.
    pub fn open(ms: impl Fn() -> f32, connect: bool) -> Self {
        let mut info = Info { connected: "not needed", ..Default::default() };
        if connect && real_devices() == 0 {
            let t0 = ms();
            info.connected = if connect_class(&POLICY_CONSOLE) && real_devices() > 0 {
                "boot manager policy: consoles"
            } else if connect_class(&POLICY_CONNECT_ALL) && real_devices() > 0 {
                "boot manager policy: all"
            } else {
                connect_all_handles();
                "ConnectController on all handles"
            };
            info.connect_ms = ms() - t0;
        }
        info.real = real_devices();
        let con = con_in_handle();
        let mut abs = Vec::new();
        for h in boot::find_handles::<AbsolutePointer>().unwrap_or_default() {
            if let Some(p) = get::<AbsolutePointer>(h) {
                let m = *p.mode();
                if m.absolute_max_x > m.absolute_min_x && m.absolute_max_y > m.absolute_min_y { abs.push((p, Some(h) == con)); }
            }
        }
        let mut rel = Vec::new();
        for h in boot::find_handles::<Pointer>().unwrap_or_default() {
            if let Some(p) = get::<Pointer>(h) { rel.push((p, Some(h) == con)); }
        }
        info.abs = abs.len();
        info.rel = rel.len();
        Self { abs, rel, info }
    }


    /// Read every device once; screen size in pixels for absolute devices.
    pub fn poll(&mut self, w: f32, h: f32, out: &mut Vec<Event>) {
        for (p, _) in self.abs.iter_mut() {
            match p.read_state() {
                Ok(Some(st)) => {
                    let m = *p.mode();
                    let fx = st.current_x.saturating_sub(m.absolute_min_x) as f32 / (m.absolute_max_x - m.absolute_min_x) as f32;
                    let fy = st.current_y.saturating_sub(m.absolute_min_y) as f32 / (m.absolute_max_y - m.absolute_min_y) as f32;
                    self.info.reads_ok += 1;
                    self.info.last = format!("abs {} {} btn {}", st.current_x, st.current_y, st.active_buttons);
                    out.push(Event::Abs(fx.clamp(0.0, 1.0) * w, fy.clamp(0.0, 1.0) * h, st.active_buttons & 1 != 0));
                }
                Ok(None) => {}
                Err(e) => { self.info.reads_err += 1; self.info.last = format!("abs error {:?}", e.status()); }
            }
        }
        for (p, _) in self.rel.iter_mut() {
            match p.read_state() {
                Ok(Some(st)) => {
                    let m = p.mode();
                    // movement / resolution = millimetres (§12.5); ~4 px per mm feels like a desktop pointer
                    let k = |res: u64| if res == 0 { 1.0 } else { 4.0 / res as f32 * 2.0 };
                    let (dx, dy) = (st.relative_movement_x as f32 * k(m.resolution_x), st.relative_movement_y as f32 * k(m.resolution_y));
                    self.info.reads_ok += 1;
                    self.info.last = format!("rel {} {} btn {}", st.relative_movement_x, st.relative_movement_y, bool::from(st.left_button));
                    out.push(Event::Rel(dx, dy, bool::from(st.left_button)));
                }
                Ok(None) => {}
                Err(e) => { self.info.reads_err += 1; self.info.last = format!("rel error {:?}", e.status()); }
            }
        }
    }
}

impl Info {
    pub fn lines(&self) -> Vec<String> {
        alloc::vec![
            format!("pointers: {} real · opened absolute {} / relative {} (incl. console splitter)", self.real, self.abs, self.rel),
            format!("drivers: {} ({:.0} ms)", self.connected, self.connect_ms),
            format!("reads: {} ok, {} errors · last: {}", self.reads_ok, self.reads_err, if self.last.is_empty() { "—" } else { &self.last }),
        ]
    }
}
