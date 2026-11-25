//! The menu itself (design v2, "comic page"): a big splash panel for the selected item with the
//! character breaking out of its frame, a column of small panels to pick from, a sound-effect burst
//! for the countdown. Keyboard and mouse, animations, the snapshot and kernel screens, help, editor.

use crate::comic::{self, Panel};
use crate::config::{Config, Entry, Kind, Stamp};
use crate::draw;
use crate::gfx::{Canvas, Image, Rgba};
use crate::i18n::{Lang, Strings};
use crate::text::{Align, Face, Fonts};
use crate::theme::Theme;
use alloc::format;
use alloc::string::{String, ToString};
use alloc::vec::Vec;
use libm::sinf;

pub struct Art {
    pub logo: Image,
    pub pixie: Image,
    pub danyok: Image,
    pub pixie_lying: Image,
    pub danyok_sketch: Image,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Screen { Main, Snapshots, Kernels }

/// Things in the right-hand column.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Item { Main, Snapshots, Windows, Safe, Kernels }

/// Small buttons bottom-right.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Btn { Uefi, Reboot, Power }

/// What the menu asks main() to do.
#[derive(Clone, Debug)]
pub enum Action {
    Linux { entry: usize, options: String },
    Windows,
    FirmwareUi,
    Reboot,
    PowerOff,
}

enum Modal {
    None,
    Help,
    Edit { entry: usize, text: Vec<char>, cur: usize },
}

#[derive(Clone, Copy, PartialEq)]
pub enum Input {
    Left, Right, Up, Down, Enter, Esc, Help, Debug, PageUp, PageDown, Home, End, Backspace, Delete,
    Char(char),
    /// mouse: position in design units, pressed
    Mouse(f32, f32, bool),
}

pub struct Clock { pub y: u16, pub mo: u8, pub d: u8, pub h: u8, pub mi: u8 }

pub struct App {
    pub cv: Canvas,
    pub fonts: Fonts,
    pub th: Theme,
    pub st: &'static Strings,
    pub lang: Lang,
    pub art: Art,
    bg: Vec<u32>,
    pub cfg: Config,
    screen: Screen,
    items: Vec<Item>,
    btns: Vec<Btn>,
    /// focus: 0 = the column of items, 1 = the small buttons
    row: usize,
    sel: usize,
    prev_sel: usize,
    sel_t: f32,
    btn_sel: usize,
    list_sel: usize,
    list_top: usize,
    modal: Modal,
    countdown_ms: Option<f32>,
    auto: Item,
    last_second: i32,
    tick_t: f32,
    intro_t: f32,
    screen_t: f32,
    launching: Option<(Action, f32, String)>,
    toast: Option<(String, f32, bool)>, // text, since, is an error
    mouse: Option<(f32, f32)>,
    mouse_down: bool,
    pub clock: Clock,
    pub diag: Vec<String>,
    pub render_ms: f32,
    pub present_ms: f32,
    /// share of the screen sent per frame (dirty rectangles), for the F12 screen
    pub sent_share: f32,
    /// how frames reach the screen (Blt or direct) and what each took on the first frame
    pub out_info: String,
    pub diag_live: Vec<String>,
    show_diag: bool,
    /// New Year season: snow and a garland (furrboot.conf `season`, by default 15.12 .. 15.01)
    festive: bool,
}

// layout, design units (1920×1080)
const SPLASH: Panel = Panel { x: 70.0, y: 290.0, w: 1090.0, h: 560.0, skew: 56.0 };
const COL_X: f32 = 1220.0;
const COL_Y: f32 = 290.0;
const COL_W: f32 = 630.0;
const ROW_H: f32 = 100.0;
const ROW_GAP: f32 = 15.0;
const ROW_SKEW: f32 = 18.0;
const LIST: Panel = Panel { x: 90.0, y: 300.0, w: 1010.0, h: 640.0, skew: 40.0 };
const LROW_H: f32 = 72.0;
const LIST_ROWS: usize = 8;
const DETAIL: Panel = Panel { x: 1170.0, y: 330.0, w: 660.0, h: 610.0, skew: 40.0 };

fn ease(t: f32) -> f32 { let t = t.clamp(0.0, 1.0); 1.0 - (1.0 - t) * (1.0 - t) * (1.0 - t) }
/// ease-out with a little overshoot (things "land")
fn back(t: f32) -> f32 {
    let t = t.clamp(0.0, 1.0);
    let c = 1.70158;
    1.0 + (c + 1.0) * (t - 1.0) * (t - 1.0) * (t - 1.0) + c * (t - 1.0) * (t - 1.0)
}

impl App {
    pub fn new(cv: Canvas, fonts: Fonts, th: Theme, lang: Lang, art: Art, cfg: Config, firmware_ui: bool, clock: Clock) -> Self {
        let bg = draw::background(cv.w, cv.h, cv.s, &th);
        let mut items = Vec::new();
        if cfg.main_entry().is_some() { items.push(Item::Main); }
        if !cfg.of(Kind::Snapshot).is_empty() { items.push(Item::Snapshots); }
        if cfg.windows.is_some() { items.push(Item::Windows); }
        if !cfg.of(Kind::Safe).is_empty() { items.push(Item::Safe); }
        if cfg.kernels().len() > 1 { items.push(Item::Kernels); }
        let mut btns = Vec::new();
        if firmware_ui { btns.push(Btn::Uefi); }
        btns.push(Btn::Reboot);
        btns.push(Btn::Power);
        // the item the countdown starts: FurrOS, or Windows when the OS asked for it once
        let auto = if cfg.boot_windows { Item::Windows } else { Item::Main };
        let has_auto = items.contains(&auto);
        let countdown_ms = if !has_auto { None }
            else if cfg.instant { Some(1.0) }
            else if cfg.timeout > 0 { Some(cfg.timeout as f32 * 1000.0) } else { None };
        let row = if items.is_empty() { 1 } else { 0 };
        let sel0 = items.iter().position(|c| *c == auto).unwrap_or(0);
        // the default entry used up its boot tries: say why something else is about to start
        let st = crate::i18n::get(lang);
        let toast = cfg.entries.iter().find(|e| e.id == cfg.default && e.bad())
            .zip(cfg.main_entry().filter(|m| !m.bad()))
            .map(|(bad, good)| (st.fell_back.replace("{bad}", &bad.title).replace("{good}", &good.title), 0.0, true));
        // FurrOS entries hidden because their partition can't be read: say so until a key is pressed
        let toast = if cfg.unreadable > 0 { Some((st.unreadable.into(), 1.0e9, true)) } else { toast };
        let festive = match cfg.season { 2 => true, 1 => false, _ => (clock.mo == 12 && clock.d >= 15) || (clock.mo == 1 && clock.d <= 15) };
        Self {
            cv, fonts, th, st: crate::i18n::get(lang), lang, art, bg, cfg, screen: Screen::Main, items, btns,
            row, sel: sel0, prev_sel: sel0, auto, sel_t: -10000.0, btn_sel: 0, list_sel: 0, list_top: 0, modal: Modal::None,
            countdown_ms, last_second: -1, tick_t: -10000.0, intro_t: 0.0, screen_t: -10000.0, launching: None,
            toast, mouse: None, mouse_down: false, clock, diag: Vec::new(), render_ms: 0.0, present_ms: 0.0, sent_share: 1.0, out_info: String::new(),
            diag_live: Vec::new(), show_diag: false,
            festive,
        }
    }

    /// Something moving on screen: draw at full frame rate.
    pub fn animating(&self, now: f32) -> bool {
        (self.festive && matches!(self.modal, Modal::None))
            || now - self.intro_t < 1200.0 || now - self.screen_t < 600.0 || now - self.sel_t < 600.0 || now - self.tick_t < 400.0
            || self.launching.is_some() || self.toast.is_some() || (self.screen == Screen::Main && self.countdown_ms.is_some())
    }

    fn entry_idx(&self, e: &Entry) -> usize { self.cfg.entries.iter().position(|x| x.id == e.id).unwrap_or(0) }
    fn stop_countdown(&mut self) { self.countdown_ms = None; }

    /// T: next colour theme, applied at once and remembered in an EFI variable.
    fn next_theme(&mut self, now: f32) {
        let i = crate::theme::NAMES.iter().position(|n| *n == self.cfg.theme).unwrap_or(0);
        let j = (i + 1) % crate::theme::NAMES.len();
        let name = crate::theme::NAMES[j];
        self.cfg.theme = name.into();
        self.th = crate::theme::by_name(name);
        self.bg = draw::background(self.cv.w, self.cv.h, self.cv.s, &self.th);
        crate::prefs::set_theme(name);
        self.toast = Some((self.st.theme_toast.replace("{name}", self.st.theme_names[j]), now, false));
    }

    fn start(&mut self, a: Action, now: f32) {
        let name = match &a {
            Action::Linux { entry, .. } => self.cfg.entries[*entry].title.clone(),
            Action::Windows => "Windows".into(),
            Action::FirmwareUi => self.st.uefi.into(),
            Action::Reboot => self.st.reboot.into(),
            Action::PowerOff => self.st.poweroff.into(),
        };
        self.stop_countdown();
        self.launching = Some((a, now, name));
    }

    pub fn fail(&mut self, msg: String, now: f32) {
        self.launching = None;
        self.toast = Some((self.st.failed.replace("{err}", &msg), now, true));
    }

    fn go(&mut self, s: Screen, now: f32) {
        self.screen = s;
        self.screen_t = now;
        self.list_sel = 0;
        self.list_top = 0;
        self.stop_countdown();
        if s == Screen::Main { self.sel_t = now; }
    }

    fn select(&mut self, i: usize, now: f32) {
        if i == self.sel && self.row == 0 { return; }
        self.prev_sel = self.sel;
        self.sel = i;
        self.row = 0;
        self.sel_t = now;
    }

    fn list(&self) -> Vec<&Entry> {
        match self.screen {
            Screen::Snapshots => self.cfg.of(Kind::Snapshot),
            Screen::Kernels => self.cfg.kernels(),
            Screen::Main => Vec::new(),
        }
    }

    fn boot_entry(&mut self, e: &Entry, now: f32) {
        let i = self.entry_idx(e);
        let o = e.options.clone();
        self.start(Action::Linux { entry: i, options: o }, now);
    }

    fn activate_item(&mut self, now: f32) {
        let Some(&it) = self.items.get(self.sel) else { return };
        match it {
            Item::Main => if let Some(e) = self.cfg.main_entry().cloned() { self.boot_entry(&e, now) },
            Item::Snapshots => self.go(Screen::Snapshots, now),
            Item::Windows => self.start(Action::Windows, now),
            Item::Safe => if let Some(e) = self.cfg.of(Kind::Safe).first().map(|e| (*e).clone()) { self.boot_entry(&e, now) },
            Item::Kernels => self.go(Screen::Kernels, now),
        }
    }

    fn activate_btn(&mut self, now: f32) {
        match self.btns.get(self.btn_sel) {
            Some(Btn::Uefi) => self.start(Action::FirmwareUi, now),
            Some(Btn::Reboot) => self.start(Action::Reboot, now),
            Some(Btn::Power) => self.start(Action::PowerOff, now),
            None => {}
        }
    }

    fn activate_list(&mut self, now: f32) {
        if let Some(e) = self.list().get(self.list_sel).map(|e| (*e).clone()) { self.boot_entry(&e, now); }
    }

    /// Entry the E key would edit on the current screen.
    fn edit_target(&self) -> Option<usize> {
        match self.screen {
            Screen::Main => match (self.row, self.items.get(self.sel)) {
                (0, Some(Item::Main)) => self.cfg.main_entry().map(|e| self.entry_idx(e)),
                (0, Some(Item::Safe)) => self.cfg.of(Kind::Safe).first().map(|e| self.entry_idx(e)),
                _ => None,
            },
            _ => self.list().get(self.list_sel).map(|e| self.entry_idx(e)),
        }
    }

    pub fn input(&mut self, k: Input, now: f32) {
        if self.launching.is_some() { return; }
        if !matches!(k, Input::Mouse(_, _, false)) { self.stop_countdown(); self.toast = None; }
        match &mut self.modal {
            Modal::Help => {
                if !matches!(k, Input::Mouse(_, _, false)) { self.modal = Modal::None; }
                return;
            }
            Modal::Edit { entry, text, cur } => {
                match k {
                    Input::Esc => self.modal = Modal::None,
                    Input::Enter => {
                        let (e, o) = (*entry, text.iter().collect::<String>());
                        self.modal = Modal::None;
                        self.start(Action::Linux { entry: e, options: o }, now);
                    }
                    Input::Left => *cur = cur.saturating_sub(1),
                    Input::Right => *cur = (*cur + 1).min(text.len()),
                    Input::Home => *cur = 0,
                    Input::End => *cur = text.len(),
                    Input::Backspace => if *cur > 0 { text.remove(*cur - 1); *cur -= 1; },
                    Input::Delete => if *cur < text.len() { text.remove(*cur); },
                    Input::Char(c) => { text.insert(*cur, c); *cur += 1; }
                    _ => {}
                }
                return;
            }
            Modal::None => {}
        }
        match k {
            Input::Debug => { self.show_diag = !self.show_diag; return; }
            Input::Help => { self.modal = Modal::Help; return; }
            Input::Char('e' | 'E' | 'у' | 'У') => {
                if let Some(i) = self.edit_target() {
                    let text: Vec<char> = self.cfg.entries[i].options.chars().collect();
                    let cur = text.len();
                    self.modal = Modal::Edit { entry: i, text, cur };
                }
                return;
            }
            Input::Mouse(x, y, down) => { self.mouse_input(x, y, down, now); return; }
            Input::Char('t' | 'T' | 'е' | 'Е') => { self.next_theme(now); return; }
            _ => {}
        }
        match self.screen {
            Screen::Main => {
                let n = self.items.len();
                match k {
                    Input::Up | Input::Left if self.row == 0 => if self.sel > 0 { self.select(self.sel - 1, now) },
                    Input::Down | Input::Right if self.row == 0 => {
                        if self.sel + 1 < n { self.select(self.sel + 1, now) } else if k == Input::Down { self.row = 1; }
                    }
                    Input::Left => self.btn_sel = self.btn_sel.saturating_sub(1),
                    Input::Right => self.btn_sel = (self.btn_sel + 1).min(self.btns.len() - 1),
                    Input::Up => if n > 0 { self.row = 0; self.sel_t = now; },
                    Input::Enter => if self.row == 0 && n > 0 { self.activate_item(now) } else { self.activate_btn(now) },
                    Input::Char(c @ '1'..='9') => {
                        let i = c as usize - '1' as usize;
                        if i < n { self.select(i, now); }
                    }
                    _ => {}
                }
            }
            _ => {
                let n = self.list().len();
                match k {
                    Input::Up => self.list_sel = self.list_sel.saturating_sub(1),
                    Input::Down => self.list_sel = (self.list_sel + 1).min(n.saturating_sub(1)),
                    Input::PageUp => self.list_sel = self.list_sel.saturating_sub(LIST_ROWS),
                    Input::PageDown => self.list_sel = (self.list_sel + LIST_ROWS).min(n.saturating_sub(1)),
                    Input::Home => self.list_sel = 0,
                    Input::End => self.list_sel = n.saturating_sub(1),
                    Input::Enter => self.activate_list(now),
                    Input::Esc | Input::Backspace | Input::Left => self.go(Screen::Main, now),
                    _ => {}
                }
                if self.list_sel < self.list_top { self.list_top = self.list_sel; }
                if self.list_sel >= self.list_top + LIST_ROWS { self.list_top = self.list_sel + 1 - LIST_ROWS; }
            }
        }
    }

    fn row_panel(i: usize) -> Panel {
        Panel { x: COL_X, y: COL_Y + i as f32 * (ROW_H + ROW_GAP), w: COL_W, h: ROW_H, skew: ROW_SKEW }
    }

    fn btn_rects(&mut self) -> Vec<(f32, f32, f32, f32)> {
        let labels: Vec<&str> = self.btns.iter().map(|b| self.btn_label(*b)).collect();
        let widths: Vec<f32> = labels.iter().map(|l| self.fonts.width(&self.cv, Face::N900, 20.0, l) + 96.0).collect();
        let total: f32 = widths.iter().sum::<f32>() + 14.0 * (widths.len() as f32 - 1.0);
        let mut x = 1850.0 - total;
        widths.iter().map(|w| { let r = (x, 1000.0, *w, 52.0); x += w + 14.0; r }).collect()
    }

    fn btn_label(&self, b: Btn) -> &'static str {
        match b { Btn::Uefi => self.st.uefi, Btn::Reboot => self.st.reboot, Btn::Power => self.st.poweroff }
    }

    fn mouse_input(&mut self, x: f32, y: f32, down: bool, now: f32) {
        let moved = self.mouse.is_none_or(|(mx, my)| (mx - x).abs() > 0.5 || (my - y).abs() > 0.5);
        self.mouse = Some((x, y));
        let click = down && !self.mouse_down;
        self.mouse_down = down;
        if moved || click { self.stop_countdown(); }
        let inside = |rx: f32, ry: f32, rw: f32, rh: f32| x >= rx && x <= rx + rw && y >= ry && y <= ry + rh;
        match self.screen {
            Screen::Main => {
                for i in 0..self.items.len() {
                    if Self::row_panel(i).contains(x, y) {
                        if moved { self.select(i, now); }
                        if click { self.select(i, now); self.activate_item(now); }
                        return;
                    }
                }
                if click && SPLASH.contains(x, y) && self.row == 0 { self.activate_item(now); return; }
                let rects = self.btn_rects();
                for (i, r) in rects.iter().enumerate() {
                    if inside(r.0, r.1, r.2, r.3) {
                        if moved { self.row = 1; self.btn_sel = i; }
                        if click { self.row = 1; self.btn_sel = i; self.activate_btn(now); }
                        return;
                    }
                }
            }
            _ => {
                let n = self.list().len();
                for vis in 0..LIST_ROWS.min(n.saturating_sub(self.list_top)) {
                    let ry = LIST.y + 26.0 + vis as f32 * LROW_H;
                    if inside(LIST.x + 20.0, ry, LIST.w, LROW_H) {
                        if moved { self.list_sel = self.list_top + vis; }
                        if click { self.list_sel = self.list_top + vis; self.activate_list(now); }
                        return;
                    }
                }
                if click && inside(DETAIL.x + 40.0, DETAIL.y + DETAIL.h - 100.0, 560.0, 70.0) { self.activate_list(now); }
                if click && inside(60.0, 30.0, 760.0, 100.0) { self.go(Screen::Main, now); }
            }
        }
    }

    /// Advance timers; returns an action to perform when the launch animation has finished.
    pub fn tick(&mut self, now: f32, dt: f32) -> Option<Action> {
        let paused = !matches!(self.modal, Modal::None);
        if let Some(ms) = self.countdown_ms.as_mut() {
            if !paused {
                *ms -= dt;
                let sec = (*ms / 1000.0) as i32;
                if sec != self.last_second { self.last_second = sec; self.tick_t = now; }
                if *ms <= 0.0 {
                    self.countdown_ms = None;
                    self.sel = self.items.iter().position(|c| *c == self.auto).unwrap_or(0);
                    self.row = 0;
                    self.activate_item(now);
                }
            }
        }
        if let Some((_, t, err)) = &self.toast { if now - *t > if *err { 7000.0 } else { 2200.0 } { self.toast = None; } }
        if let Some((a, t, _)) = &self.launching {
            if now - *t > 800.0 { return Some(a.clone()); }
        }
        None
    }

    // ================= drawing =================

    pub fn render(&mut self, now: f32) {
        self.cv.px.copy_from_slice(&self.bg);
        if self.festive { self.snow(now); }  // behind the cards, so it never covers their text
        self.top_bar();
        match self.screen {
            Screen::Main => self.main_screen(now),
            Screen::Snapshots | Screen::Kernels => self.list_screen(now),
        }
        if self.festive { self.garland(now); }
        match self.modal {
            Modal::Help => self.help(),
            Modal::Edit { .. } => self.edit(),
            Modal::None => {}
        }
        if let Some((msg, _, err)) = self.toast.clone() {
            let w = self.fonts.width(&self.cv, Face::N800, 22.0, &msg).min(1500.0) + 60.0;
            let x = (1920.0 - w) / 2.0;
            let (fill, fg) = if err { (self.th.red, self.th.paper) } else { (self.th.cyan, self.th.ink) };
            self.cv.comic_box(x, 150.0, w, 64.0, 16.0, fill, self.th.ink, 4.0, Some((self.th.ink, 6.0)));
            let fitted = self.fonts.fit(&self.cv, Face::N800, 22.0, &msg, w - 50.0);
            self.fonts.draw(&mut self.cv, Face::N800, 22.0, 960.0, 182.0, Align::Center, fg, &fitted);
        }
        if self.show_diag { self.diagnostics(); }
        if let Some((_, t, name)) = self.launching.clone() { self.launch_overlay(now - t, &name); }
        if let Some((mx, my)) = self.mouse {
            if self.launching.is_none() {
                draw::paw(&mut self.cv, mx + 2.0, my + 2.0, 15.0, self.th.ink);
                draw::paw(&mut self.cv, mx, my, 13.0, self.th.paper);
            }
        }
    }

    /// Falling snow over the menu: each flake's path comes from its number, so nothing is stored.
    fn snow(&mut self, now: f32) {
        let t = now / 1000.0;
        let flake = self.th.paper.with_alpha(210);
        for i in 0..72u32 {
            // a well-mixed hash (lowbias32): plain multiplication lined the flakes up in diagonal dotted lines
            let h = |k: u32| {
                let mut x = i.wrapping_mul(0x9E37_79B1) ^ k.wrapping_mul(0x85EB_CA77);
                x ^= x >> 16; x = x.wrapping_mul(0x7FEB_352D); x ^= x >> 15; x = x.wrapping_mul(0x846C_A68B); x ^= x >> 16;
                (x & 0xffff) as f32 / 65535.0
            };
            let big = i % 9 == 0;
            let (speed, size) = (45.0 + 75.0 * h(1), if big { 8.0 + 4.0 * h(2) } else { 2.5 + 4.5 * h(2) });
            let y = (t * speed + 1200.0 * h(4)) % 1180.0 - 50.0;
            let x = 1920.0 * h(3) + 26.0 * libm::sinf(t * (0.6 + 0.5 * h(6)) + core::f32::consts::TAU * h(5));
            self.cv.ellipse(x, y, size, size, if big { self.th.paper.with_alpha(120) } else { flake });
        }
    }

    /// A garland along the top edge: four sagging spans, bulbs blinking in turn.
    fn garland(&mut self, now: f32) {
        let th = self.th;
        let cols = [th.red, th.cyan, th.yellow, th.green, th.pink];
        let wire_y = |x: f32| 2.0 + 26.0 * libm::sinf(core::f32::consts::PI * ((x % 480.0) / 480.0));
        let mut x = 0.0;
        while x < 1920.0 {
            let nx = x + 24.0;
            self.cv.line(x, wire_y(x), nx, wire_y(nx.min(1919.9)), 3.0, th.ink);
            x = nx;
        }
        let phase = (now / 450.0) as u32;
        let mut k = 0u32;
        let mut bx = 30.0;
        while bx < 1920.0 {
            let y = wire_y(bx);
            let c = cols[(k % 5) as usize];
            let lit = (k + phase) % 3 != 0;
            self.cv.rrect(bx - 4.0, y, 8.0, 7.0, 2.0, th.ink);
            if lit { self.cv.ellipse(bx, y + 15.0, 12.0, 14.0, c.with_alpha(70)); }
            self.cv.ellipse(bx, y + 15.0, 7.0, 9.0, if lit { c } else { c.with_alpha(110) });
            bx += 60.0;
            k += 1;
        }
    }

    fn diagnostics(&mut self) {
        let mut lines = self.diag.clone();
        lines.extend(self.diag_live.iter().cloned());
        lines.push(format!("frame: draw {:.1} ms + to screen {:.1} ms ({:.0}% of the screen sent) · canvas {}×{} · scale {:.3}", self.render_ms, self.present_ms, self.sent_share * 100.0, self.cv.w, self.cv.h, self.cv.s));
        if !self.out_info.is_empty() { lines.push(format!("screen output: {}", self.out_info)); }
        if let Some((x, y)) = self.mouse { lines.push(format!("mouse: {x:.0}, {y:.0} (design units)")); }
        let h = 40.0 + lines.len() as f32 * 34.0;
        self.cv.rrect(40.0, 1080.0 - h - 40.0, 1240.0, h, 14.0, self.th.ink.with_alpha(235));
        for (i, l) in lines.iter().enumerate() {
            self.fonts.draw(&mut self.cv, Face::N700, 21.0, 64.0, 1080.0 - h - 40.0 + 36.0 + i as f32 * 34.0, Align::Left, self.th.green, l);
        }
    }

    fn top_bar(&mut self) {
        let (th, st) = (self.th, self.st);
        let (lx, ly) = (self.cv.x(70.0) as i32, self.cv.y(56.0) as i32);
        self.cv.image_px(&self.art.logo, lx, ly, 1.0);
        self.fonts.draw_shadow(&mut self.cv, Face::Dela, 40.0, 150.0, 88.0, Align::Left, th.paper, th.red, 3.0, "Furr");
        let w = self.fonts.width(&self.cv, Face::Dela, 40.0, "Furr");
        self.fonts.draw_shadow(&mut self.cv, Face::Dela, 40.0, 150.0 + w, 88.0, Align::Left, th.red, th.paper, 3.0, "OS");
        let crumb = match self.screen { Screen::Snapshots => Some(st.snapshots), Screen::Kernels => Some(st.other_kernel), Screen::Main => None };
        if let Some(c) = crumb {
            let x = 150.0 + w + self.fonts.width(&self.cv, Face::Dela, 40.0, "OS") + 30.0;
            self.fonts.draw(&mut self.cv, Face::N800, 28.0, x, 90.0, Align::Left, th.dim, &format!("›  {c}"));
        }
        // list screens: the character on the detail panel takes the top-right corner
        if self.screen != Screen::Main { return; }
        let c = &self.clock;
        let time = format!("{:02}:{:02}", c.h, c.mi);
        let wd = weekday(c.y, c.mo, c.d);
        let date = match self.lang {
            Lang::En => format!("{}, {} {}", st.weekdays[wd], st.months[(c.mo as usize + 11) % 12], c.d),
            _ => format!("{}, {} {}", st.weekdays[wd], c.d, st.months[(c.mo as usize + 11) % 12]),
        };
        self.fonts.draw_shadow(&mut self.cv, Face::Dela, 44.0, 1850.0, 80.0, Align::Right, th.paper, th.ink, 3.0, &time);
        self.fonts.draw(&mut self.cv, Face::N700, 22.0, 1850.0, 122.0, Align::Right, th.dim, &date);
    }

    /// What to show in the splash for an item: title, caption, line the character says, which art.
    fn splash_content(&self, it: Item) -> (String, String, &'static str, u8) {
        let st = self.st;
        match it {
            Item::Main => {
                let e = self.cfg.main_entry();
                let title = e.map(|e| e.title.clone()).unwrap_or_else(|| "FurrOS".into());
                let cap = e.map(|e| e.subtitle.replace(" · ", ", ")).unwrap_or_default();
                (title, cap, if self.festive { st.say_newyear } else { st.say_main }, b'd')  // the mascot: Danyok (25.11.2026)
            }
            Item::Snapshots => (st.snapshots.into(), self.snap_summary(), st.say_snap, b'l'),
            Item::Windows => (st.windows.into(), st.windows_sub.into(), st.say_win, b'p'),  // b'p' = Velvet now
            Item::Safe => (st.safe.into(), st.cap_safe.into(), st.say_safe, b's'),
            Item::Kernels => {
                let names: Vec<String> = self.cfg.kernels().iter().map(|e| e.title.clone()).collect();
                (st.other_kernel.into(), names.join(", "), st.say_kern, b's')
            }
        }
    }

    fn art_for(&self, which: u8) -> &Image {
        match which { b'p' => &self.art.pixie, b'l' => &self.art.pixie_lying, b'd' => &self.art.danyok, _ => &self.art.danyok_sketch }
    }

    fn item_label(&self, it: Item) -> (String, String) {
        let st = self.st;
        match it {
            Item::Main => {
                let e = self.cfg.main_entry();
                // standing in for a default entry that failed to boot
                let sub = match self.cfg.entries.iter().find(|x| x.id == self.cfg.default && x.bad()) {
                    Some(bad) if e.is_some_and(|e| e.id != bad.id) => st.instead_of.replace("{bad}", &bad.title),
                    _ => st.default_badge.into(),
                };
                (e.map(|e| e.title.clone()).unwrap_or_default(), sub)
            }
            Item::Snapshots => (st.snapshots.into(), self.snap_summary().replace('\n', ", ")),
            Item::Windows => (st.windows.into(), st.windows_sub.into()),
            Item::Safe => (st.safe.into(), st.cap_safe.into()),
            Item::Kernels => (st.other_kernel.into(), st.kernels_n.replace("{n}", &self.cfg.kernels().len().to_string())),
        }
    }

    fn main_screen(&mut self, now: f32) {
        let th = self.th;
        let t_in = now - self.intro_t;
        // the page "draws itself" once: panels wipe in from the left
        let wipe = ease(t_in / 450.0);
        if wipe < 1.0 { self.cv.set_clip(0.0, 0.0, 1920.0 * wipe, 1080.0); }

        // ---- splash panel ----
        let focus = self.row == 0 && !self.items.is_empty();
        comic::panel(&mut self.cv, &SPLASH, th.plum, th.paper, 5.0, Some((th.ink, 14.0)));
        comic::halftone(&mut self.cv, &SPLASH, 10.0, th.maroon.with_alpha(150), 22.0, 7.0);
        self.cv.reset_clip();

        if self.items.is_empty() {
            let lines = comic::wrap(&self.cv, &mut self.fonts, Face::N800, 28.0, self.st.nothing, 900.0);
            for (i, l) in lines.iter().enumerate() {
                self.fonts.draw(&mut self.cv, Face::N800, 28.0, SPLASH.x + 110.0, SPLASH.y + 140.0 + i as f32 * 40.0, Align::Left, th.paper, l);
            }
        } else {
            let k = ease((now - self.sel_t) / 320.0);
            let item = self.items[self.sel.min(self.items.len() - 1)];
            let prev = self.items[self.prev_sel.min(self.items.len() - 1)];
            let (title, cap, say, which) = self.splash_content(item);
            // character: the old one drops out, the new one slides in and lands; it breaks out of the top of the frame
            let floor = SPLASH.y + SPLASH.h - 6.0;
            let breath = sinf(now / 1000.0 * 2.2) * 3.0;
            let drop_in = if t_in < 900.0 { (1.0 - back((t_in - 250.0) / 600.0)) * 260.0 } else { 0.0 };
            self.cv.set_clip(0.0, 0.0, 1920.0, floor);
            if k < 1.0 && prev != item {
                let (_, _, _, pw) = self.splash_content(prev);
                self.draw_art(pw, floor + 120.0 * k, 1.0 - k, 0.0);
            }
            let slide = (1.0 - back(k)) * 140.0;
            self.draw_art(which, floor + drop_in - breath.max(0.0) * 0.0, k.max(0.25), slide);
            self.cv.reset_clip();
            let _ = breath;

            // title + caption, left part of the splash
            let tx = SPLASH.left_at(SPLASH.y + 190.0) + 60.0 - (1.0 - k) * 30.0;
            // a short name gets the big size on one line; a long one wraps onto two smaller lines
            let max_w = if which == b'l' { 480.0 } else { 540.0 };
            let (tsize, tlines) = if self.fonts.width(&self.cv, Face::Dela, 104.0, &title) <= max_w {
                (104.0, alloc::vec![title.clone()])
            } else {
                let mut size = 66.0;
                let mut lines = comic::wrap(&self.cv, &mut self.fonts, Face::Dela, size, &title, max_w);
                if lines.len() > 2 || lines.iter().any(|l| self.fonts.width(&self.cv, Face::Dela, size, l) > max_w) {
                    size = 52.0;
                    lines = comic::wrap(&self.cv, &mut self.fonts, Face::Dela, size, &title, max_w);
                }
                lines.truncate(2);
                (size, lines)
            };
            let lh = tsize * 1.14;
            let ty0 = SPLASH.y + 190.0 - (tlines.len() as f32 - 1.0) * lh * 0.5;
            for (i, l) in tlines.iter().enumerate() {
                let l = self.fonts.fit(&self.cv, Face::Dela, tsize, l, max_w + 40.0);
                self.fonts.draw_shadow(&mut self.cv, Face::Dela, tsize, tx, ty0 + i as f32 * lh, Align::Left, th.paper, th.red, 5.0, &l);
            }
            let cap_y = ty0 + (tlines.len() as f32 - 1.0) * lh + tsize * 0.62 + 34.0;
            if !cap.is_empty() {
                let lines = comic::wrap(&self.cv, &mut self.fonts, Face::N800, 25.0, &cap, max_w - 70.0); // clear of the bubble tail
                for (i, l) in lines.iter().take(2).enumerate() {
                    self.fonts.draw(&mut self.cv, Face::N800, 25.0, tx + 4.0, cap_y + i as f32 * 34.0, Align::Left, th.dim, l);
                }
            }
            // the character's line
            let bubble_k = back(((now - self.sel_t) - 120.0) / 300.0).max(0.0).min(1.05);
            let bubble_k = if t_in < 700.0 { back((t_in - 450.0) / 300.0).max(0.0) } else { bubble_k };
            let (bx, by) = (SPLASH.left_at(SPLASH.y + 440.0) + 60.0, SPLASH.y + 372.0);
            let (spx, spy) = match which { b'l' => (SPLASH.x + 660.0, SPLASH.y + 330.0), b'p' => (SPLASH.x + 650.0, SPLASH.y + 300.0), _ => (SPLASH.x + 690.0, SPLASH.y + 250.0) };
            comic::speech(&mut self.cv, &mut self.fonts, &th, bx, by, if which == b'l' { 500.0 } else { 560.0 }, say, spx, spy, if focus { bubble_k } else { 0.0 });

            // countdown burst on the top-right corner of the splash (breaks the frame too)
            if let Some(ms) = self.countdown_ms {
                let secs = (ms / 1000.0) as u32 + 1;
                let pop = 1.0 + 0.16 * (1.0 - ease((now - self.tick_t) / 260.0));
                let appear = back((t_in - 500.0) / 350.0).clamp(0.0, 1.1);
                let r = 88.0 * pop * appear;
                if r > 1.0 {
                    let (cx, cy) = (SPLASH.left_at(SPLASH.y) + 34.0, SPLASH.y + 8.0);
                    comic::burst(&mut self.cv, cx, cy, r, th.yellow, th.ink, now / 4000.0);
                    if appear > 0.8 {
                        self.fonts.draw(&mut self.cv, Face::Dela, 64.0 * pop, cx, cy - 6.0, Align::Center, th.ink, &secs.to_string());
                        self.fonts.draw(&mut self.cv, Face::N900, 20.0, cx, cy + 40.0, Align::Center, th.ink, self.st.burst_label);
                    }
                }
            } else if t_in > 400.0 {
                let note = self.fonts.fit(&self.cv, Face::N800, 19.0, self.st.autoboot_stopped, 470.0);
                self.fonts.draw(&mut self.cv, Face::N800, 19.0, SPLASH.left_at(SPLASH.y + SPLASH.h - 30.0) + 50.0, SPLASH.y + SPLASH.h - 32.0,
                    Align::Left, th.dim.with_alpha(170), &note);
            }
        }

        // ---- the column of small panels ----
        for i in 0..self.items.len() {
            let it = self.items[i];
            let appear = ease((t_in - 120.0 - i as f32 * 70.0) / 380.0);
            if appear <= 0.0 { continue; }
            let sel = self.row == 0 && i == self.sel;
            let p = Self::row_panel(i).moved((1.0 - appear) * 260.0 + if sel { -26.0 * ease((now - self.sel_t) / 200.0) } else { 0.0 }, 0.0);
            if sel {
                comic::panel(&mut self.cv, &p, th.cyan, th.ink, 4.0, Some((th.pink, 10.0)));
                // pointer notch towards the splash
                let my = p.y + p.h / 2.0;
                let lx = p.left_at(my);
                self.cv.polygon(&[(lx + 2.0, my - 18.0), (lx - 22.0, my), (lx + 2.0, my + 18.0)], th.ink);
                self.cv.polygon(&[(lx + 6.0, my - 12.0), (lx - 12.0, my), (lx + 6.0, my + 12.0)], th.cyan);
            } else {
                comic::panel(&mut self.cv, &p, th.plum, th.paper.with_alpha(120), 3.0, Some((th.ink, 7.0)));
            }
            let (fg, sc) = if sel { (th.ink, th.soft) } else { (th.paper, th.dim) };
            let ix = p.left_at(p.y + p.h / 2.0) + 50.0;
            let cy = p.y + p.h / 2.0;
            self.item_icon(it, ix, cy, if sel { th.ink } else { self.item_color(it) });
            let (name, sub) = self.item_label(it);
            let name = self.fonts.fit(&self.cv, Face::N900, 29.0, &name, COL_W - 150.0);
            let sub = self.fonts.fit(&self.cv, Face::N700, 19.0, &sub, COL_W - 150.0);
            self.fonts.draw(&mut self.cv, Face::N900, 29.0, ix + 46.0, cy - 13.0, Align::Left, fg, &name);
            self.fonts.draw(&mut self.cv, Face::N700, 19.0, ix + 46.0, cy + 20.0, Align::Left, sc, &sub);
            // number key hint
            self.fonts.draw(&mut self.cv, Face::N900, 18.0, p.left_at(cy) + COL_W - 34.0, cy, Align::Center, if sel { th.soft } else { th.dim.with_alpha(120) }, &(i + 1).to_string());
        }

        // ---- bottom: key hints left, small buttons right ----
        let mut items: Vec<(&str, &str)> = alloc::vec![("UD", self.st.key_select), ("Enter", self.st.key_boot)];
        if self.edit_target().is_some() { items.push(("E", self.st.key_edit)); }
        items.push(("F1", self.st.key_help));
        if matches!(self.modal, Modal::None) { self.hints_left(&items); }
        let rects = self.btn_rects();
        for (i, r) in rects.iter().enumerate() {
            let b = self.btns[i];
            let sel = self.row == 1 && i == self.btn_sel;
            let (fill, edge, fg) = if sel { (th.cyan, th.ink, th.ink) } else { (th.plum, th.paper.with_alpha(140), th.paper) };
            self.cv.rrect(r.0 + 5.0, r.1 + 5.0, r.2, r.3, 11.0, if sel { th.pink } else { th.ink });
            self.cv.comic_box(r.0, r.1, r.2, r.3, 11.0, fill, edge, 3.0, None);
            let kind = match b { Btn::Uefi => b'u', Btn::Reboot => b'r', Btn::Power => b'p' };
            draw::icon_small(&mut self.cv, kind, r.0 + 34.0, r.1 + 26.0, fg);
            let label = self.btn_label(b);
            self.fonts.draw(&mut self.cv, Face::N900, 20.0, r.0 + 66.0, r.1 + 26.0, Align::Left, fg, label);
        }
    }

    fn item_color(&self, it: Item) -> Rgba {
        match it { Item::Main => self.th.cyan, Item::Snapshots => self.th.pink, Item::Windows => self.th.yellow, Item::Safe => self.th.green, Item::Kernels => self.th.paper }
    }

    fn item_icon(&mut self, it: Item, cx: f32, cy: f32, c: Rgba) {
        let cv = &mut self.cv;
        match it {
            Item::Main => draw::paw(cv, cx, cy + 6.0, 22.0, c),
            Item::Snapshots => {
                cv.ring(cx, cy, 17.0, 5.0, c);
                cv.line(cx, cy, cx, cy - 10.0, 5.0, c);
                cv.line(cx, cy, cx + 7.0, cy + 4.0, 5.0, c);
            }
            Item::Windows => {
                cv.rrect_outline(cx - 19.0, cy - 15.0, 38.0, 30.0, 5.0, 5.0, c);
                cv.rrect(cx - 19.0, cy - 7.0, 38.0, 5.0, 0.0, c);
            }
            Item::Safe => {
                cv.polygon(&[(cx, cy - 20.0), (cx + 17.0, cy - 12.0), (cx + 14.0, cy + 6.0), (cx, cy + 19.0), (cx - 14.0, cy + 6.0), (cx - 17.0, cy - 12.0)], c);
            }
            Item::Kernels => draw::icon_small(cv, b'k', cx, cy, c),
        }
    }

    /// Draw the splash character standing on `floor` (its bottom edge), slid right by `dx`.
    fn draw_art(&mut self, which: u8, floor: f32, opacity: f32, dx: f32) {
        let img = self.art_for(which);
        let (w, h) = (img.w as f32 / self.cv.s, img.h as f32 / self.cv.s);
        let cx = match which { b'l' => SPLASH.x + 870.0, _ => SPLASH.x + 820.0 };
        let x = cx - w / 2.0 + dx;
        // the lying pose rests on the floor; standing characters are cut by it (they "stand" in the panel)
        let y = match which { b'l' => floor - h - 10.0, _ => floor - h + 40.0 };
        let (px, py) = (self.cv.x(x) as i32, self.cv.y(y) as i32);
        let img: *const Image = img;
        self.cv.image_px(unsafe { &*img }, px, py, opacity);
    }

    fn hints_left(&mut self, items: &[(&str, &str)]) {
        let th = self.th;
        let y = 1009.0;
        let mut x = 70.0;
        for (k, l) in items {
            let w = draw::keycap(&mut self.cv, &mut self.fonts, &th, x, y, k);
            self.fonts.draw(&mut self.cv, Face::N700, 20.0, x + w + 10.0, y + 17.0, Align::Left, th.dim, l);
            x += w + 10.0 + self.fonts.width(&self.cv, Face::N700, 20.0, l) + 30.0;
        }
    }

    fn snap_summary(&self) -> String {
        let snaps = self.cfg.of(Kind::Snapshot);
        let n = snaps.len();
        let latest = snaps.first().and_then(|e| e.date).map(|d| self.when(d).to_lowercase()).unwrap_or_default();
        if self.lang == Lang::Ru {
            let word = ru_plural(n, "снимок", "снимка", "снимков");
            return format!("{n} {word}\nпоследний {latest}");
        }
        self.st.snapshots_count.replace("{n}", &n.to_string()).replace("{t}", &latest)
    }

    /// "Сегодня, 21:40" / "Вчера, 23:12" / "8 ноября, 18:30"
    fn when(&self, d: Stamp) -> String {
        let c = &self.clock;
        let today = days(c.y, c.mo, c.d);
        let that = days(d.y, d.mo, d.d);
        let day = if that == today { self.st.today.to_string() }
            else if that + 1 == today { self.st.yesterday.to_string() }
            else {
                let m = self.st.months[(d.mo as usize + 11) % 12];
                match self.lang { Lang::En => format!("{m} {}", d.d), _ => format!("{} {m}", d.d) }
            };
        format!("{day}, {:02}:{:02}", d.h, d.mi)
    }

    fn list_screen(&mut self, now: f32) {
        let (th, st) = (self.th, self.st);
        let snaps = self.screen == Screen::Snapshots;
        let k = ease((now - self.screen_t) / 380.0);
        let slide = (1.0 - k) * 80.0;
        let title = if snaps { st.snap_title } else { st.kern_title };
        self.fonts.draw_shadow(&mut self.cv, Face::Dela, 56.0, 100.0, 220.0, Align::Left, th.paper, th.red, 4.0, title);

        let entries: Vec<Entry> = self.list().into_iter().cloned().collect();
        let main_id = self.cfg.main_entry().map(|e| e.id.clone()).unwrap_or_default();
        let lp = LIST.moved(-slide, 0.0);
        comic::panel(&mut self.cv, &lp, th.plum, th.paper, 5.0, Some((th.ink, 14.0)));
        if entries.is_empty() {
            self.fonts.draw(&mut self.cv, Face::N800, 26.0, lp.left_at(lp.y + 60.0) + 50.0, lp.y + 60.0, Align::Left, th.dim, st.snap_none);
        }
        for vis in 0..LIST_ROWS.min(entries.len().saturating_sub(self.list_top)) {
            let i = self.list_top + vis;
            let e = &entries[i];
            let y = lp.y + 26.0 + vis as f32 * LROW_H;
            let sel = i == self.list_sel;
            let row = Panel { x: lp.left_at(y + LROW_H) + 22.0, y: y + 3.0, w: lp.w - 60.0, h: LROW_H - 6.0, skew: lp.skew * (LROW_H - 6.0) / lp.h };
            if sel { comic::panel(&mut self.cv, &row, th.cyan, th.ink, 3.0, Some((th.pink, 6.0))); }
            let (fg, sc) = if sel { (th.ink, th.soft) } else { (th.paper, th.dim) };
            let (main, sub) = if snaps {
                (e.date.map(|d| self.when(d)).unwrap_or_else(|| e.title.clone()), if e.subtitle.is_empty() { e.title.clone() } else { e.subtitle.clone() })
            } else {
                (e.title.clone(), if e.when.is_empty() { e.subtitle.clone() } else { e.when.clone() })
            };
            let tx = row.left_at(y + LROW_H / 2.0) + 30.0;
            let main = self.fonts.fit(&self.cv, Face::N900, 26.0, &main, lp.w - 330.0);
            let sub = self.fonts.fit(&self.cv, Face::N700, 18.0, &sub, lp.w - 330.0);
            self.fonts.draw(&mut self.cv, Face::N900, 26.0, tx, y + 25.0, Align::Left, fg, &main);
            self.fonts.draw(&mut self.cv, Face::N700, 18.0, tx, y + 51.0, Align::Left, sc, &sub);
            let tag = if snaps {
                match e.tag.as_str() {
                    "update" => Some((st.tag_update, th.yellow)),
                    "install" => Some((st.tag_install, th.pink)),
                    "important" => Some((st.tag_important, th.green)),
                    _ => None,
                }
            } else if e.bad() { Some((st.tag_bad, th.red)) } else if e.id == main_id { Some((st.tag_now, th.cyan)) } else { None };
            if let Some((label, col)) = tag {
                draw::tag(&mut self.cv, &mut self.fonts, &th, row.left_at(y + LROW_H / 2.0) + row.w - 26.0, y + LROW_H / 2.0, label, col, 16.0);
            }
        }
        if entries.len() > LIST_ROWS {
            let msg = format!("{}–{} / {}", self.list_top + 1, (self.list_top + LIST_ROWS).min(entries.len()), entries.len());
            self.fonts.draw(&mut self.cv, Face::N700, 18.0, lp.x + lp.w - 40.0, lp.y + lp.h - 22.0, Align::Right, th.dim, &msg);
        }

        // detail panel with the character breaking out of it
        if let Some(e) = entries.get(self.list_sel) {
            let dp = DETAIL.moved(slide * 0.5, 0.0);
            comic::panel(&mut self.cv, &dp, th.card, th.ink, 5.0, Some((th.pink, 14.0)));
            let lx = |yy: f32| dp.left_at(yy) + 44.0;
            let head = if snaps { e.date.map(|d| self.when(d)).unwrap_or_else(|| e.title.clone()) } else { e.title.clone() };
            let head = self.fonts.fit(&self.cv, Face::Dela, 32.0, &head, dp.w - 100.0);
            self.fonts.draw(&mut self.cv, Face::Dela, 32.0, lx(dp.y + 70.0), dp.y + 70.0, Align::Left, th.ink, &head);
            let fields: Vec<(&str, String)> = if snaps {
                alloc::vec![
                    (st.snap_what, if e.subtitle.is_empty() { e.title.clone() } else { e.subtitle.clone() }),
                    (st.snap_kernel, if e.kernel.is_empty() { "—".into() } else { e.kernel.clone() }),
                    (st.snap_type, if e.typ.is_empty() { "—".into() } else { e.typ.clone() }),
                ]
            } else {
                alloc::vec![
                    (st.kern_when, if e.when.is_empty() { e.subtitle.clone() } else { e.when.clone() }),
                    (st.kern_once, st.kern_once_value.into()),
                ]
            };
            let mut yy = dp.y + 130.0;
            for (label, v) in fields {
                self.fonts.draw(&mut self.cv, Face::N800, 18.0, lx(yy), yy, Align::Left, th.soft, label);
                let v = self.fonts.fit(&self.cv, Face::N800, 25.0, &v, dp.w - 110.0);
                self.fonts.draw(&mut self.cv, Face::N900, 25.0, lx(yy + 30.0), yy + 30.0, Align::Left, th.ink, &v);
                yy += 72.0;
            }
            let note: &[&str] = if snaps { &st.snap_note } else { &st.kern_note };
            let nh = 30.0 * note.len() as f32 + 28.0;
            let nx = lx(yy + nh);
            self.cv.comic_box(nx, yy, dp.w - 110.0, nh, 10.0, th.yellow, th.ink, 3.0, None);
            for (i, ln) in note.iter().enumerate() {
                self.fonts.draw(&mut self.cv, Face::N800, 19.0, nx + 20.0, yy + 30.0 + i as f32 * 30.0, Align::Left, th.ink, ln);
            }
            let label = if snaps { st.snap_button } else { st.kern_button };
            let bw = self.fonts.width(&self.cv, Face::N900, 25.0, label) + 60.0;
            let by = dp.y + dp.h - 96.0;
            let bx = lx(by + 64.0);
            self.cv.rrect(bx + 6.0, by + 6.0, bw, 64.0, 12.0, th.ink);
            self.cv.comic_box(bx, by, bw, 64.0, 12.0, th.cyan, th.ink, 4.0, None);
            self.fonts.draw(&mut self.cv, Face::N900, 25.0, bx + bw / 2.0, by + 32.0, Align::Center, th.ink, label);
            // the character sits on the top edge of the panel
            let which = if snaps { b'l' } else { b's' };
            let img: *const Image = self.art_for(which);
            let img = unsafe { &*img };
            let (w, h) = (img.w as f32 / self.cv.s, img.h as f32 / self.cv.s);
            let (ax, ay) = if snaps { (dp.x + dp.w - w + 40.0, dp.y - h + 46.0) } else { (dp.left_at(dp.y) + dp.w - w - 30.0, dp.y - 290.0) };
            if snaps {
                self.cv.image_px(img, self.cv.x(ax) as i32, self.cv.y(ay) as i32, 1.0);
            } else {
                // a peek over the edge, cut by the panel's top
                self.cv.set_clip(0.0, 0.0, 1920.0, dp.y + 4.0);
                self.cv.image_px(img, self.cv.x(ax) as i32, self.cv.y(ay) as i32, 1.0);
                self.cv.reset_clip();
            }
        }
        let mut items: Vec<(&str, &str)> = alloc::vec![("UD", st.key_select), ("Enter", st.key_boot), ("Esc", st.key_back)];
        if !entries.is_empty() { items.push(("E", st.key_edit)); }
        if matches!(self.modal, Modal::None) { self.hints_left(&items); }
    }

    fn help(&mut self) {
        let (th, st) = (self.th, self.st);
        self.cv.fill_px(0, 0, self.cv.w as i32, self.cv.h as i32, th.ink.with_alpha(175));
        let p = Panel { x: 440.0, y: 210.0, w: 1040.0, h: 660.0, skew: 40.0 };
        comic::panel(&mut self.cv, &p, th.card, th.ink, 5.0, Some((th.pink, 14.0)));
        self.fonts.draw(&mut self.cv, Face::Dela, 36.0, p.left_at(p.y + 80.0) + 60.0, p.y + 80.0, Align::Left, th.ink, st.help_title);
        for (i, (key, desc)) in st.help_lines.iter().enumerate() {
            let yy = p.y + 156.0 + i as f32 * 58.0;
            let x = p.left_at(yy) + 60.0;
            draw::keycap(&mut self.cv, &mut self.fonts, &th, x, yy - 17.0, key);
            self.fonts.draw(&mut self.cv, Face::N800, 24.0, x + 240.0, yy, Align::Left, th.ink, desc);
        }
    }

    fn edit(&mut self) {
        let (th, st) = (self.th, self.st);
        let Modal::Edit { entry, text, cur } = &self.modal else { return };
        let (entry, text, cur) = (*entry, text.clone(), *cur);
        self.cv.fill_px(0, 0, self.cv.w as i32, self.cv.h as i32, th.ink.with_alpha(175));
        let p = Panel { x: 190.0, y: 380.0, w: 1520.0, h: 250.0, skew: 30.0 };
        comic::panel(&mut self.cv, &p, th.card, th.ink, 5.0, Some((th.pink, 14.0)));
        let x = p.left_at(p.y + 170.0) + 50.0;
        self.fonts.draw(&mut self.cv, Face::Dela, 32.0, x, p.y + 66.0, Align::Left, th.ink, st.edit_title);
        let title = self.cfg.entries[entry].title.clone();
        self.fonts.draw(&mut self.cv, Face::N800, 22.0, x + p.w - 110.0, p.y + 68.0, Align::Right, th.soft, &title);
        let (fx, fy, fw) = (x, p.y + 114.0, p.w - 110.0);
        self.cv.comic_box(fx, fy, fw, 70.0, 12.0, th.plum, th.ink, 3.0, None);
        let size = 24.0;
        let mut start = 0usize;
        loop {
            let before: String = text[start..cur].iter().collect();
            if self.fonts.width(&self.cv, Face::N700, size, &before) < fw - 60.0 || start >= cur { break; }
            start += 1;
        }
        let mut end = cur;
        while end < text.len() {
            let s: String = text[start..end + 1].iter().collect();
            if self.fonts.width(&self.cv, Face::N700, size, &s) > fw - 40.0 { break; }
            end += 1;
        }
        let shown: String = text[start..end].iter().collect();
        self.cv.set_clip(fx + 10.0, fy, fw - 20.0, 70.0);
        self.fonts.draw(&mut self.cv, Face::N700, size, fx + 20.0, fy + 35.0, Align::Left, th.paper, &shown);
        let before: String = text[start..cur].iter().collect();
        let cx = fx + 20.0 + self.fonts.width(&self.cv, Face::N700, size, &before);
        self.cv.rrect(cx, fy + 16.0, 3.0, 38.0, 1.0, th.cyan);
        self.cv.reset_clip();
        self.hints_left(&[("Enter", st.key_boot), ("Esc", st.key_back)]);
    }

    fn launch_overlay(&mut self, t: f32, name: &str) {
        let th = self.th;
        let a = (t / 250.0).clamp(0.0, 1.0);
        self.cv.fill_px(0, 0, self.cv.w as i32, self.cv.h as i32, th.ink.with_alpha((210.0 * a) as u8));
        let msg = self.st.launching.replace("{name}", name);
        let k = back(t / 380.0);
        self.fonts.draw_shadow(&mut self.cv, Face::Dela, 54.0 * k.max(0.01), 960.0, 500.0, Align::Center, th.paper, th.red, 4.0, &msg);
        // paws walk across under the text
        let steps = 9;
        for i in 0..steps {
            let appear = i as f32 * 70.0;
            if t < appear { break; }
            let x = 960.0 - (steps as f32 - 1.0) * 45.0 + i as f32 * 90.0;
            let y = 620.0 + if i % 2 == 0 { -14.0 } else { 14.0 };
            let col = if i == steps - 1 || t - appear < 120.0 { th.cyan } else { th.paper };
            draw::paw(&mut self.cv, x, y, 24.0, col);
        }
    }
}

fn ru_plural(n: usize, one: &'static str, few: &'static str, many: &'static str) -> &'static str {
    let (m10, m100) = (n % 10, n % 100);
    if m10 == 1 && m100 != 11 { one } else if (2..=4).contains(&m10) && !(12..=14).contains(&m100) { few } else { many }
}

/// Day number (for "today"/"yesterday" comparisons).
fn days(y: u16, m: u8, d: u8) -> i64 {
    let (y, m) = if m <= 2 { (y as i64 - 1, m as i64 + 9) } else { (y as i64, m as i64 - 3) };
    365 * y + y / 4 - y / 100 + y / 400 + (m * 306 + 5) / 10 + d as i64
}

/// 0 = Sunday
pub fn weekday(y: u16, m: u8, d: u8) -> usize {
    const T: [i32; 12] = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4];
    let y = if m < 3 { y as i32 - 1 } else { y as i32 };
    ((y + y / 4 - y / 100 + y / 400 + T[(m as usize + 11) % 12] + d as i32) % 7) as usize
}
