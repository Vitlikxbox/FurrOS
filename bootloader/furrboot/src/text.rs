//! Text with the fonts baked into FurrBoot (Dela Gothic One for headings, Nunito for the rest).
//! Glyphs are rendered once per size and kept in a cache.

use crate::gfx::{Canvas, Rgba};
use alloc::collections::BTreeMap;
use alloc::vec::Vec;
use fontdue::{Font as FdFont, FontSettings, Metrics};
use libm::roundf;

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Face { Dela, N700, N800, N900 }

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Align { Left, Center, Right }

pub struct Fonts {
    faces: [FdFont; 4],
    cache: BTreeMap<(Face, char, u16), (Metrics, Vec<u8>)>,
}

impl Fonts {
    pub fn load() -> Self {
        let f = |b: &'static [u8]| FdFont::from_bytes(b, FontSettings::default()).expect("font");
        Self {
            faces: [
                f(include_bytes!("../assets/dela.ttf")),
                f(include_bytes!("../assets/nunito-700.ttf")),
                f(include_bytes!("../assets/nunito-800.ttf")),
                f(include_bytes!("../assets/nunito-900.ttf")),
            ],
            cache: BTreeMap::new(),
        }
    }

    fn face(&self, f: Face) -> &FdFont { &self.faces[f as usize] }

    fn glyph(&mut self, f: Face, c: char, px: u16) -> &(Metrics, Vec<u8>) {
        if !self.cache.contains_key(&(f, c, px)) {
            let g = self.face(f).rasterize(c, px as f32);
            // a very long session could fill memory; the menu uses a few hundred glyphs at most
            if self.cache.len() > 4000 { self.cache.clear(); }
            self.cache.insert((f, c, px), g);
        }
        &self.cache[&(f, c, px)]
    }

    /// Width in pixels of a string at a pixel size.
    pub fn width_px(&mut self, f: Face, px: u16, s: &str) -> f32 {
        let mut w = 0.0;
        let mut prev: Option<char> = None;
        for c in s.chars() {
            if let Some(p) = prev { w += self.face(f).horizontal_kern(p, c, px as f32).unwrap_or(0.0); }
            w += self.glyph(f, c, px).0.advance_width;
            prev = Some(c);
        }
        w
    }

    /// Width in design units.
    pub fn width(&mut self, cv: &Canvas, f: Face, size: f32, s: &str) -> f32 {
        let px = Self::px(cv, size);
        self.width_px(f, px, s) / cv.s
    }

    fn px(cv: &Canvas, size: f32) -> u16 { (roundf(size * cv.s) as u16).max(6) }

    /// Draw text. `y` is the vertical middle of the line (like PIL's "m" anchor), design units.
    pub fn draw(&mut self, cv: &mut Canvas, f: Face, size: f32, x: f32, y: f32, align: Align, c: Rgba, s: &str) {
        let px = Self::px(cv, size);
        let w = self.width_px(f, px, s);
        let lm = self.face(f).horizontal_line_metrics(px as f32);
        let (asc, desc) = lm.map(|m| (m.ascent, m.descent)).unwrap_or((px as f32 * 0.8, -(px as f32) * 0.2));
        let mut pen_x = cv.x(x) - match align { Align::Left => 0.0, Align::Center => w / 2.0, Align::Right => w };
        let baseline = cv.y(y) + (asc + desc) / 2.0;
        let mut prev: Option<char> = None;
        for ch in s.chars() {
            if let Some(p) = prev { pen_x += self.face(f).horizontal_kern(p, ch, px as f32).unwrap_or(0.0); }
            let (m, bmp) = {
                let g = self.glyph(f, ch, px);
                (g.0, g.1.clone())
            };
            let gx = roundf(pen_x + m.xmin as f32) as i32;
            let gy = roundf(baseline - (m.height as f32 + m.ymin as f32)) as i32;
            if m.width > 0 && m.height > 0 { cv.mask_px(&bmp, m.width, m.height, gx, gy, c); }
            pen_x += m.advance_width;
            prev = Some(ch);
        }
    }

    /// Text with a hard comic shadow under it.
    pub fn draw_shadow(&mut self, cv: &mut Canvas, f: Face, size: f32, x: f32, y: f32, align: Align, c: Rgba, shadow: Rgba, off: f32, s: &str) {
        self.draw(cv, f, size, x + off, y + off, align, shadow, s);
        self.draw(cv, f, size, x, y, align, c, s);
    }

    /// Cut a string to fit `max_w` design units, adding "…".
    pub fn fit(&mut self, cv: &Canvas, f: Face, size: f32, s: &str, max_w: f32) -> alloc::string::String {
        if self.width(cv, f, size, s) <= max_w { return s.into(); }
        let mut out: alloc::string::String = s.into();
        while !out.is_empty() {
            out.pop();
            let mut t = out.clone();
            t.push('…');
            if self.width(cv, f, size, &t) <= max_w { return t; }
        }
        "…".into()
    }
}
