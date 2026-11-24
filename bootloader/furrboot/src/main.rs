//! FurrBoot — the FurrOS boot menu. A UEFI application: draws the comic-style menu with the
//! firmware's graphics output, then starts a Linux kernel (EFI stub), Windows Boot Manager,
//! the firmware settings, or resets the machine.
#![no_std]
#![no_main]

extern crate alloc;

mod bli;
mod prefs;
mod clock;
mod comic;
mod config;
mod fsdrivers;
mod draw;
mod gfx;
mod i18n;
mod input;
mod launch;
mod qoi;
mod text;
mod theme;
mod ui;

use alloc::string::String;
use alloc::vec::Vec;
use core::time::Duration;
use gfx::Canvas;
use ui::{Action, App, Input};
use uefi::boot::{self, ScopedProtocol};
use uefi::prelude::*;
use uefi::proto::console::gop::{BltOp, BltPixel, BltRegion, GraphicsOutput, PixelFormat};
use alloc::format;
use uefi::proto::console::text::{Key, ScanCode};
use uefi::{runtime, system};

/// The biggest mode up to 1920×1200 (more pixels only makes software drawing slow) with the screen's own
/// shape. The largest mode the firmware offers is normally the panel's native one (GOP builds the list from
/// EDID), so its aspect ratio is the screen's; a mode of another shape would come out stretched.
fn pick_mode(gop: &mut GraphicsOutput, want: Option<(usize, usize)>) {
    if let Some(want) = want {
        if let Some(m) = gop.modes().find(|m| m.info().resolution() == want) {
            if gop.set_mode(&m).is_ok() { return; }
        }
    }
    let cur = gop.current_mode_info().resolution();
    let fits = |(w, h): (usize, usize)| w * h <= 1920 * 1200;
    let native = gop.modes().map(|m| m.info().resolution()).max_by_key(|&(w, h)| w * h).unwrap_or(cur);
    // same shape within ~2 % (1366×768 vs 1920×1080 still counts as 16:9)
    let same_shape = |(w, h): (usize, usize)| (w * native.1).abs_diff(h * native.0) * 50 <= h * native.0;
    let mut best: Option<(usize, uefi::proto::console::gop::Mode)> = None;
    for m in gop.modes() {
        let (w, h) = m.info().resolution();
        if !fits((w, h)) || w < 800 { continue; }
        let score = w * h + if same_shape((w, h)) { 1 << 40 } else { 0 };
        if best.as_ref().is_none_or(|(s, _)| score > *s) { best = Some((score, m)); }
    }
    let cur_score = cur.0 * cur.1 + if same_shape(cur) { 1 << 40 } else { 0 };
    if let Some((s, m)) = best {
        if m.info().resolution() != cur && (!fits(cur) || s > cur_score) {
            let _ = gop.set_mode(&m);
        }
    }
}

/// The screen, exclusively if we can; if another loader that started us still holds it, share it.
fn open_gop(h: Handle) -> Option<ScopedProtocol<GraphicsOutput>> {
    boot::open_protocol_exclusive::<GraphicsOutput>(h).ok().or_else(|| unsafe {
        boot::open_protocol::<GraphicsOutput>(
            boot::OpenProtocolParams { handle: h, agent: boot::image_handle(), controller: None },
            boot::OpenProtocolAttributes::GetProtocol,
        ).ok()
    })
}

/// Puts the canvas on the screen, sending only what changed since the last frame.
/// On real hardware the frame buffer behind the firmware's Blt is often uncached video memory: a whole
/// 1920×1080 frame there can take hundreds of milliseconds (≈3 fps measured on a real PC), while a typical
/// frame changes a small part (the countdown star, a moving panel). Changed rows are grouped into bands and
/// each band is sent as one sub-rectangle (EFI_GRAPHICS_OUTPUT_PROTOCOL.Blt, BltBufferToVideo with Delta).
///
/// Two ways to the screen, timed on the first frame and the faster one kept:
/// - Blt: the firmware copies (some GOP drivers do it pixel by pixel, converting formats);
/// - direct: our own row copies into the linear frame buffer (only for PixelBlueGreenRedReserved8BitPerColor,
///   which is byte for byte our canvas: 0x00RRGGBB little-endian = B, G, R, reserved).
struct Presenter { last: Vec<u32>, valid: bool, pub sent_px: usize, direct: Option<usize>, decided: bool, pub how: String }

impl Presenter {
    fn new() -> Self { Self { last: Vec::new(), valid: false, sent_px: 0, direct: None, decided: false, how: String::new() } }
    /// The screen was drawn by someone else (a loader that came back): next frame goes out whole.
    fn invalidate(&mut self) { self.valid = false; }

    /// Copy one rectangle of the canvas to the screen.
    fn put(&self, gop: &mut GraphicsOutput, cv: &Canvas, x0: usize, y0: usize, bw: usize, bh: usize) {
        let w = cv.w;
        match self.direct {
            Some(stride) => {
                let mut fb = gop.frame_buffer();
                let base = fb.as_mut_ptr().cast::<u32>();
                for y in y0..y0 + bh {
                    // SAFETY: the rectangle lies inside the mode (checked by the callers' canvas size = mode size)
                    // and the frame buffer holds stride × height pixels (checked when direct mode was chosen)
                    unsafe { core::ptr::copy_nonoverlapping(cv.px.as_ptr().add(y * w + x0), base.add(y * stride + x0), bw) };
                }
            }
            None => {
                let buf: &[BltPixel] = unsafe { core::slice::from_raw_parts(cv.px.as_ptr().cast(), cv.px.len()) };
                let _ = gop.blt(BltOp::BufferToVideo {
                    buffer: buf, src: BltRegion::SubRectangle { coords: (x0, y0), px_stride: w }, dest: (x0, y0), dims: (bw, bh),
                });
            }
        }
    }

    /// First frame: time a whole frame both ways (same picture, so nothing visible happens) and keep the faster.
    fn decide(&mut self, gop: &mut GraphicsOutput, cv: &Canvas) {
        self.decided = true;
        let (w, h) = (cv.w, cv.h);
        let info = gop.current_mode_info();
        let t0 = clock::ms();
        self.put(gop, cv, 0, 0, w, h);
        let blt = clock::ms() - t0;
        let fits = info.stride() >= w && gop.frame_buffer().size() >= info.stride() * h * 4;
        if info.pixel_format() != PixelFormat::Bgr || !fits {
            self.how = format!("Blt {blt:.0} ms/frame (direct: format {:?})", info.pixel_format());
            return;
        }
        self.direct = Some(info.stride());
        let t1 = clock::ms();
        self.put(gop, cv, 0, 0, w, h);
        let direct = clock::ms() - t1;
        if direct < blt * 0.8 {
            self.how = format!("direct {direct:.0} ms/frame (Blt {blt:.0})");
        } else {
            self.direct = None;
            self.how = format!("Blt {blt:.0} ms/frame (direct {direct:.0})");
        }
    }

    fn present(&mut self, gop: &mut GraphicsOutput, cv: &Canvas) {
        let (w, h) = (cv.w, cv.h);
        if !self.valid || self.last.len() != cv.px.len() {
            if self.decided { self.put(gop, cv, 0, 0, w, h); } else { self.decide(gop, cv); }
            self.last.clear();
            self.last.extend_from_slice(&cv.px);
            self.valid = true;
            self.sent_px = w * h;
            return;
        }
        self.sent_px = 0;
        let mut y = 0;
        while y < h {
            // find the next band of changed rows (small unchanged gaps are merged in: fewer Blt calls)
            let row_diff = |y: usize| -> Option<(usize, usize)> {
                let (a, b) = (&cv.px[y * w..(y + 1) * w], &self.last[y * w..(y + 1) * w]);
                let l = a.iter().zip(b).position(|(p, q)| p != q)?;
                let r = w - 1 - a.iter().rev().zip(b.iter().rev()).position(|(p, q)| p != q)?;
                Some((l, r))
            };
            let Some((mut x0, mut x1)) = row_diff(y) else { y += 1; continue };
            let y0 = y;
            let mut y1 = y;
            let mut gap = 0;
            y += 1;
            while y < h && gap <= 8 {
                match row_diff(y) {
                    Some((l, r)) => { x0 = x0.min(l); x1 = x1.max(r); y1 = y; gap = 0; }
                    None => gap += 1,
                }
                y += 1;
            }
            let (bw, bh) = (x1 - x0 + 1, y1 - y0 + 1);
            self.put(gop, cv, x0, y0, bw, bh);
            for r in y0..=y1 { self.last[r * w + x0..r * w + x1 + 1].copy_from_slice(&cv.px[r * w + x0..r * w + x1 + 1]); }
            self.sent_px += bw * bh;
        }
    }
}

fn read_keys(out: &mut Vec<Input>) {
    system::with_stdin(|stdin| {
        while let Ok(Some(k)) = stdin.read_key() {
            out.push(match k {
                Key::Special(ScanCode::LEFT) => Input::Left,
                Key::Special(ScanCode::RIGHT) => Input::Right,
                Key::Special(ScanCode::UP) => Input::Up,
                Key::Special(ScanCode::DOWN) => Input::Down,
                Key::Special(ScanCode::ESCAPE) => Input::Esc,
                Key::Special(ScanCode::FUNCTION_1) => Input::Help,
                Key::Special(ScanCode::FUNCTION_12) => Input::Debug,
                Key::Special(ScanCode::PAGE_UP) => Input::PageUp,
                Key::Special(ScanCode::PAGE_DOWN) => Input::PageDown,
                Key::Special(ScanCode::HOME) => Input::Home,
                Key::Special(ScanCode::END) => Input::End,
                Key::Special(ScanCode::DELETE) => Input::Delete,
                Key::Special(_) => continue,
                Key::Printable(c) => match char::from(c) {
                    '\r' | '\n' => Input::Enter,
                    '\u{8}' => Input::Backspace,
                    '\t' => Input::Right,
                    ch => Input::Char(ch),
                },
            });
        }
    });
}

fn local_clock(tz: i32) -> ui::Clock {
    let Ok(t) = runtime::get_time() else { return ui::Clock { y: 2026, mo: 1, d: 1, h: 0, mi: 0 } };
    let (mut y, mut mo, mut d) = (t.year(), t.month(), t.day());
    let mut mins = t.hour() as i32 * 60 + t.minute() as i32 + tz;
    // roll the date over when the offset crosses midnight
    let dim = |y: u16, m: u8| -> u8 { match m { 2 => if (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 { 29 } else { 28 }, 4 | 6 | 9 | 11 => 30, _ => 31 } };
    while mins < 0 { mins += 1440; if d > 1 { d -= 1 } else { mo = if mo > 1 { mo - 1 } else { y -= 1; 12 }; d = dim(y, mo); } }
    while mins >= 1440 { mins -= 1440; if d < dim(y, mo) { d += 1 } else { d = 1; mo = if mo < 12 { mo + 1 } else { y += 1; 1 }; } }
    ui::Clock { y, mo, d, h: (mins / 60) as u8, mi: (mins % 60) as u8 }
}

fn load_art(s: f32) -> ui::Art {
    let dec = |b: &[u8]| qoi::decode(b).expect("art");
    let fit = |img: gfx::Image| {
        if (s - 1.0).abs() < 0.01 { img } else {
            let (w, h) = ((img.w as f32 * s) as usize, (img.h as f32 * s) as usize);
            img.scaled(w, h)
        }
    };
    ui::Art {
        logo: fit(dec(include_bytes!("../assets/logo.qoi"))),
        pixie: fit(dec(include_bytes!("../assets/pixie.qoi"))),
        danyok: fit(dec(include_bytes!("../assets/danyok.qoi"))),
        pixie_lying: fit(dec(include_bytes!("../assets/pixie_lying.qoi"))),
        danyok_sketch: fit(dec(include_bytes!("../assets/danyok_sketch.qoi"))),
    }
}

#[entry]
fn main() -> Status {
    bli::mark_start();
    uefi::helpers::init().unwrap();
    // the firmware gives a boot application 5 minutes before it resets the machine; a menu may wait longer
    let _ = boot::set_watchdog_timer(0, 0x10000, None);

    // keys pressed before the menu appeared (or left over from a loader that started us) must not pick anything
    system::with_stdin(|stdin| { let _ = stdin.reset(false); while let Ok(Some(_)) = stdin.read_key() {} });

    // file-system drivers (Btrfs) first: entries may point at kernels on the FurrOS partition
    clock::calibrate();
    let fs_diag = fsdrivers::load();
    let mut cfg = config::load();
    bli::apply(&mut cfg);
    if let Some(t) = prefs::theme() { if theme::NAMES.contains(&t.as_str()) { cfg.theme = t; } }
    let Ok(gop_handle) = boot::get_handle_for_protocol::<GraphicsOutput>() else {
        // no graphics at all: start the default entry straight away
        return fallback_boot(&cfg);
    };
    let Some(mut gop) = open_gop(gop_handle) else { return fallback_boot(&cfg) };
    pick_mode(&mut gop, cfg.resolution);
    let (w, h) = gop.current_mode_info().resolution();

    bli::publish(&cfg, clock::per_ms());
    let cv = Canvas::new(w, h);
    let art = load_art(cv.s);
    let th = theme::by_name(&cfg.theme);
    let lang = cfg.lang;
    let fw_ui = launch::firmware_ui_supported();
    let clock = local_clock(cfg.tz_offset);
    let mut app = App::new(cv, text::Fonts::load(), th, lang, art, cfg, fw_ui, clock);
    let mut mouse = input::Pointers::open(clock::ms, true);
    app.diag = diagnostics(&gop, &app);
    app.diag.extend(fs_diag);
    app.diag.extend(app.cfg.notes.clone());
    let (mut mx, mut my) = (w as f32 / 2.0, h as f32 / 2.0);
    let mut last = clock::ms();
    let mut last_clock = last;
    let mut inputs: Vec<Input> = Vec::new();
    let mut events: Vec<input::Event> = Vec::new();
    let mut screen = Presenter::new();
    let mut dirty = true; // something to draw although nothing animates (input, clock, first frame)
    let mut was_animating = true; // one more frame when an animation ends (its last state, a toast going away)

    loop {
        let now = clock::ms();
        let dt = (now - last).clamp(0.0, 200.0);
        last = now;
        if now - last_clock > 5000.0 { app.clock = local_clock(app.cfg.tz_offset); last_clock = now; dirty = true; }

        inputs.clear();
        read_keys(&mut inputs);
        events.clear();
        mouse.poll(w as f32, h as f32, &mut events);
        for ev in events.drain(..) {
            let down = match ev {
                input::Event::Abs(x, y, d) => { mx = x; my = y; d }
                input::Event::Rel(dx, dy, d) => {
                    mx = (mx + dx).clamp(0.0, w as f32 - 1.0);
                    my = (my + dy).clamp(0.0, h as f32 - 1.0);
                    d
                }
            };
            let (dx, dy) = app.cv.to_design(mx, my);
            inputs.push(Input::Mouse(dx, dy, down));
        }
        app.diag_live = mouse.info.lines();
        if !inputs.is_empty() { dirty = true; }
        for k in inputs.drain(..) { app.input(k, now); }

        if let Some(action) = app.tick(now, dt) {
            app.render(now);
            screen.present(&mut gop, &app.cv);
            // whatever starts next (Windows, a kernel, another loader) needs the screen and the mouse
            drop(gop);
            drop(mouse);
            let err = perform(&mut app, action);
            let Some(g) = open_gop(gop_handle) else { return Status::DEVICE_ERROR };
            gop = g;
            mouse = input::Pointers::open(clock::ms, false);
            screen.invalidate(); // whatever ran drew over the screen
            dirty = true;
            if let Some(e) = err {
                let now = clock::ms();
                app.fail(e, now);
                last = now;
            }
            continue;
        }
        let animating = app.animating(now);
        if animating || dirty || was_animating {
            let t0 = clock::ms();
            app.render(now);
            let t1 = clock::ms();
            screen.present(&mut gop, &app.cv);
            let t2 = clock::ms();
            app.render_ms = app.render_ms * 0.9 + (t1 - t0) * 0.1;
            app.present_ms = app.present_ms * 0.9 + (t2 - t1) * 0.1;
            app.sent_share = app.sent_share * 0.9 + (screen.sent_px as f32 / (w * h) as f32) * 0.1;
            if app.out_info.is_empty() { app.out_info = screen.how.clone(); }
            dirty = false;
        }
        was_animating = animating;
        // idle: nothing on screen moves, wait for a key or the mouse (the firmware keeps the last frame)
        if !animating { boot::stall(Duration::from_millis(20)); }
    }
}

/// Do what the menu chose. Returns an error text if it came back.
fn perform(app: &mut App, a: Action) -> Option<String> {
    let cfg = &mut app.cfg;
    let r = match a {
        Action::Linux { entry, options } => {
            if let Some(v) = cfg.volume { bli::count_attempt(v, &mut cfg.entries[entry]); }
            let e = &cfg.entries[entry];
            bli::before_launch(Some(&e.id), clock::per_ms());
            match e.volume.or(cfg.volume) {  // the FurrOS Btrfs partition, or the one with the entries
                Some(v) => launch::linux(v, &e.linux, &e.initrd, &options),
                None => Err(Status::NOT_FOUND.into()),
            }
        }
        Action::Windows => match cfg.windows.inspect(|_| bli::before_launch(None, clock::per_ms())) { Some(v) => launch::windows(v), None => Err(Status::NOT_FOUND.into()) },
        Action::FirmwareUi => launch::firmware_ui(),
        Action::Reboot => launch::reboot(),
        Action::PowerOff => launch::poweroff(),
    };
    r.err().map(|e| launch::describe(&e))
}

fn fallback_boot(cfg: &config::Config) -> Status {
    if let Some((e, v)) = cfg.main_entry().and_then(|e| e.volume.or(cfg.volume).map(|v| (e, v))) {
        let mut e = e.clone();
        // the counter lives in the entry's file name: that is on the partition with \loader\entries
        if let Some(ev) = cfg.volume { bli::count_attempt(ev, &mut e); }
        bli::before_launch(Some(&e.id), clock::per_ms());
        let _ = launch::linux(v, &e.linux, &e.initrd, &e.options);
    }
    Status::LOAD_ERROR
}

/// The F12 screen: what the firmware gave us. Useful when something misbehaves on real hardware.
fn diagnostics(gop: &GraphicsOutput, app: &App) -> Vec<String> {
    let mut v = Vec::new();
    let fw = system::firmware_vendor();
    let rev = system::firmware_revision();
    v.push(alloc::format!("firmware: {} {}.{} (UEFI {})", fw, rev >> 16, rev & 0xFFFF, system::uefi_revision()));
    let (w, h) = gop.current_mode_info().resolution();
    v.push(alloc::format!("screen: {w}×{h}, {} modes, format {:?}", gop.modes().count(), gop.current_mode_info().pixel_format()));
    v.push(alloc::format!("entries: {} · boot volume {} · Windows {}", app.cfg.entries.len(),
        if app.cfg.volume.is_some() { "found" } else { "NOT FOUND" }, if app.cfg.windows.is_some() { "found" } else { "no" }));
    v.push(alloc::format!("firmware settings button: {}", if launch::firmware_ui_supported() { "yes" } else { "no" }));
    v.extend(bli::status_lines());
    v
}
