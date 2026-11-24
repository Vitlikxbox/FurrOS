//! v2 comic-page pieces: slanted panels, the sound-effect burst, speech bubbles with wrapping.

use crate::gfx::{Canvas, Rgba};
use crate::text::{Align, Face, Fonts};
use crate::theme::Theme;
use alloc::string::String;
use alloc::vec::Vec;
use libm::{cosf, sinf, sqrtf};

/// A panel: parallelogram whose top edge is shifted right by `skew` (the slant of the page cuts on furros.xyz).
#[derive(Clone, Copy)]
pub struct Panel { pub x: f32, pub y: f32, pub w: f32, pub h: f32, pub skew: f32 }

impl Panel {
    pub fn pts(&self, inset: f32) -> [(f32, f32); 4] {
        let Panel { x, y, w, h, skew: k } = *self;
        // horizontal inset of a slanted side so the border is `inset` thick measured across it
        let d = inset * sqrtf(1.0 + (k / h) * (k / h));
        let (yt, yb) = (y + inset, y + h - inset);
        let lx = |yy: f32| x + k * (y + h - yy) / h;
        [(lx(yt) + d, yt), (lx(yt) + w - d, yt), (lx(yb) + w - d, yb), (lx(yb) + d, yb)]
    }
    /// x of the left edge at height `yy`
    pub fn left_at(&self, yy: f32) -> f32 { self.x + self.skew * (self.y + self.h - yy) / self.h }
    pub fn contains(&self, px: f32, py: f32) -> bool {
        py >= self.y && py <= self.y + self.h && px >= self.left_at(py) && px <= self.left_at(py) + self.w
    }
    pub fn moved(&self, dx: f32, dy: f32) -> Panel { Panel { x: self.x + dx, y: self.y + dy, ..*self } }
}

/// Hard shadow, ink edge, fill.
pub fn panel(cv: &mut Canvas, p: &Panel, fill: Rgba, edge: Rgba, bw: f32, shadow: Option<(Rgba, f32)>) {
    if let Some((c, off)) = shadow { cv.polygon(&p.moved(off, off).pts(0.0), c); }
    cv.polygon(&p.pts(0.0), edge);
    cv.polygon(&p.pts(bw), fill);
}

/// Halftone dots inside a panel, growing towards one corner (shading, like printed comics).
pub fn halftone(cv: &mut Canvas, p: &Panel, inset: f32, col: Rgba, step: f32, max_r: f32) {
    let inner = Panel { x: p.x + inset, y: p.y + inset, w: p.w - 2.0 * inset, h: p.h - 2.0 * inset, skew: p.skew };
    let mut yy = inner.y + step / 2.0;
    while yy < inner.y + inner.h {
        let mut xx = inner.left_at(yy) + step / 2.0;
        let right = inner.left_at(yy) + inner.w;
        while xx < right {
            // bigger dots towards the bottom-right
            let fx = (xx - inner.x) / inner.w;
            let fy = (yy - inner.y) / inner.h;
            let k = ((fx + fy) * 0.5 - 0.35).max(0.0) / 0.65;
            if k > 0.05 { cv.ellipse(xx, yy, max_r * k, max_r * k, col); }
            xx += step;
        }
        yy += step;
    }
}

/// The sound-effect burst ("БАХ!" star) used for the countdown.
pub fn burst(cv: &mut Canvas, cx: f32, cy: f32, r: f32, fill: Rgba, ink: Rgba, rot: f32) {
    let n = 14;
    let mut out: Vec<(f32, f32)> = Vec::with_capacity(n * 2);
    let mut inner: Vec<(f32, f32)> = Vec::with_capacity(n * 2);
    for i in 0..n * 2 {
        let a = core::f32::consts::PI * i as f32 / n as f32 + rot;
        // alternate long and short spikes so it looks hand-drawn, not like a gear
        let rr = if i % 2 == 0 { r * if i % 4 == 0 { 1.0 } else { 0.86 } } else { r * 0.66 };
        out.push((cx + (rr + 8.0) * cosf(a), cy + (rr + 8.0) * sinf(a)));
        inner.push((cx + rr * cosf(a), cy + rr * sinf(a)));
    }
    let shadow: Vec<(f32, f32)> = out.iter().map(|&(x, y)| (x + 8.0, y + 8.0)).collect();
    cv.polygon(&shadow, ink);
    cv.polygon(&out, ink);
    cv.polygon(&inner, fill);
}

/// Wrap text into lines no wider than `max_w` design units.
pub fn wrap(cv: &Canvas, f: &mut Fonts, face: Face, size: f32, text: &str, max_w: f32) -> Vec<String> {
    let mut lines = Vec::new();
    for para in text.split('\n') {
        let mut cur = String::new();
        // a one-letter word (RU и/в/с/к, PL i/w/z, ES y/a/o) never ends a line: it goes down with the next word
        let mut tokens: Vec<String> = Vec::new();
        let mut glue = false;
        for w in para.split(' ') {
            if glue { if let Some(last) = tokens.last_mut() { last.push(' '); last.push_str(w); } } else { tokens.push(String::from(w)); }
            let mut ch = w.chars();
            glue = matches!((ch.next(), ch.next()), (Some(c), None) if c.is_alphabetic());
        }
        for word in tokens.iter().map(|s| s.as_str()) {
            let try_line = if cur.is_empty() { String::from(word) } else { alloc::format!("{cur} {word}") };
            if !cur.is_empty() && f.width(cv, face, size, &try_line) > max_w {
                lines.push(core::mem::take(&mut cur));
                cur = String::from(word);
            } else {
                cur = try_line;
            }
        }
        lines.push(cur);
    }
    lines
}

/// Speech bubble at (x, y) top-left, up to `max_w` wide, with a tail pointing to (tx, ty).
/// `k` 0..1 pops it open from the tail.
pub fn speech(cv: &mut Canvas, f: &mut Fonts, th: &Theme, x: f32, y: f32, max_w: f32, text: &str, tx: f32, ty: f32, k: f32) {
    if k <= 0.01 { return; }
    let size = 26.0;
    let lines = wrap(cv, f, Face::N900, size, text, max_w - 56.0);
    let tw = lines.iter().map(|l| f.width(cv, Face::N900, size, l)).fold(0.0f32, f32::max);
    let (w, h) = (tw + 56.0, lines.len() as f32 * 36.0 + 34.0);
    // scale around the tail end
    let (ox, oy) = (tx, ty);
    let sc = |v: f32, o: f32| o + (v - o) * k;
    let (bx, by, bw, bh) = (sc(x, ox), sc(y, oy), w * k, h * k);
    // tail: leaves the side of the bubble that faces the speaker
    let (ex, ey) = (sc(tx, ox), sc(ty, oy));
    let base = 38.0 * k;
    let (tail, tail_in) = if tx > x + w {
        let (ax, ay) = (bx + bw - 6.0, by + bh * 0.42);
        ([(ax, ay), (ax, ay + base), (ex, ey)], [(ax - 6.0, ay + 6.0), (ax - 6.0, ay + base - 6.0), (ex - 10.0 * k, ey)])
    } else if tx < x {
        let (ax, ay) = (bx + 6.0, by + bh * 0.42);
        ([(ax, ay), (ax, ay + base), (ex, ey)], [(ax + 6.0, ay + 6.0), (ax + 6.0, ay + base - 6.0), (ex + 10.0 * k, ey)])
    } else {
        let (ax, ay) = (bx + bw * 0.25, by + bh - 6.0);
        ([(ax, ay), (ax + base, ay), (ex, ey)], [(ax + 6.0, ay - 6.0), (ax + base - 6.0, ay - 6.0), (ex, ey - 10.0 * k)])
    };
    cv.rrect(bx + 7.0, by + 7.0, bw, bh, 28.0 * k, th.ink);
    cv.polygon(&tail, th.ink);
    cv.rrect(bx, by, bw, bh, 28.0 * k, th.ink);
    cv.rrect(bx + 4.0, by + 4.0, bw - 8.0, bh - 8.0, 24.0 * k, th.card);
    cv.polygon(&tail_in, th.card);
    if k > 0.85 {
        for (i, l) in lines.iter().enumerate() {
            f.draw(cv, Face::N900, size, bx + 28.0, by + 34.0 + i as f32 * 36.0, Align::Left, th.ink, l);
        }
    }
}
