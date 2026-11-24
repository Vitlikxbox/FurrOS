//! Comic-style building blocks shared by the screens: background, top bar, keycaps, bubbles, icons.

use crate::gfx::{Canvas, Rgba};
use crate::text::{Align, Face, Fonts};
use crate::theme::Theme;
use alloc::vec::Vec;
use libm::{cosf, sinf, sqrtf};

pub const PI: f32 = core::f32::consts::PI;

/// The background is drawn once per screen size into its own buffer (it never changes).
pub fn background(w: usize, h: usize, s: f32, th: &Theme) -> Vec<u32> {
    let mut cv = Canvas::new(w, h);
    let (wf, hf) = (w as f32, h as f32);
    cv.fill_px(0, 0, w as i32, h as i32, th.night);
    // diagonal red slab on the right, with a paper edge (like the first screen of furros.xyz)
    let edge = 8.0 * s;
    cv.polygon_px(&[(wf * 0.64 - edge, 0.0), (wf, 0.0), (wf, hf), (wf * 0.46 - edge, hf)], th.paper);
    cv.polygon_px(&[(wf * 0.64, 0.0), (wf, 0.0), (wf, hf), (wf * 0.46, hf)], th.maroon);
    // diagonal stripes (integer test per pixel: the target has no hardware floating point)
    let period = ((52.0 * s) as i32).max(8);
    let band = ((24.0 * s) as i32).max(3);
    let stripe = th.ink.with_alpha(46);
    for y in 0..h as i32 {
        for x in 0..w as i32 {
            if (x + y) % period < band { cv.plot_a(x, y, stripe.0, stripe.a()); }
        }
    }
    // speed lines from the centre: 60 thin wedges, each a polygon
    let (cx, cy) = (wf / 2.0, hf * 0.47);
    let (r1, r2) = (380.0 * s, 1300.0 * s);
    let ray = th.paper.with_alpha(12);
    for i in 0..60 {
        let a0 = (i as f32 * 6.0) * PI / 180.0;
        let a1 = (i as f32 * 6.0 + 2.2) * PI / 180.0;
        let (c0, s0, c1, s1) = (cosf(a0), sinf(a0), cosf(a1), sinf(a1));
        cv.polygon_px(&[(cx + r1 * c0, cy + r1 * s0), (cx + r2 * c0, cy + r2 * s0), (cx + r2 * c1, cy + r2 * s1), (cx + r1 * c1, cy + r1 * s1)], ray);
    }
    // halftone dots fading out from the bottom-left corner
    let step = 16.0 * s;
    let mut yy = 0.0;
    while yy < hf {
        let mut xx = 0.0;
        while xx < wf * 0.5 {
            let k = 1.0 - sqrtf((xx / (wf * 0.45)) * (xx / (wf * 0.45)) + ((hf - yy) / (hf * 0.55)) * ((hf - yy) / (hf * 0.55)));
            if k > 0.02 {
                let r = 2.4 * k * s;
                cv.ellipse_px(xx, yy, r, r, th.pink.with_alpha((150.0 * k) as u8));
            }
            xx += step;
        }
        yy += step;
    }
    // scattered paws and stars
    let mut seed: u32 = 0x9E37_79B9;
    let mut rnd = move |n: u32| { seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5; seed % n.max(1) };
    let cols = [th.cyan, th.pink, th.paper, th.yellow];
    for i in 0..26 {
        let x = rnd(w as u32) as f32;
        let y = rnd(h as u32) as f32;
        let sz = (14 + rnd(20)) as f32 * s;
        let c = cols[rnd(4) as usize].with_alpha((18 + rnd(22)) as u8);
        if i % 5 < 3 { paw_px(&mut cv, x, y, sz, c); } else { star_px(&mut cv, x, y, sz, c, 0.0); }
    }
    cv.px
}

pub fn paw_px(cv: &mut Canvas, cx: f32, cy: f32, s: f32, c: Rgba) {
    cv.ellipse_px(cx, cy + s * 0.3, s * 0.55, s * 0.4, c);
    for (dx, dy, r) in [(-0.62, -0.42, 0.24), (-0.22, -0.78, 0.25), (0.22, -0.78, 0.25), (0.62, -0.42, 0.24)] {
        cv.ellipse_px(cx + dx * s, cy + dy * s, r * s, r * s, c);
    }
}

pub fn star_px(cv: &mut Canvas, cx: f32, cy: f32, s: f32, c: Rgba, rot: f32) {
    let mut pts = [(0.0f32, 0.0f32); 10];
    for (i, p) in pts.iter_mut().enumerate() {
        let r = if i % 2 == 0 { s } else { s * 0.45 };
        let a = PI / 5.0 * i as f32 + rot - PI / 2.0;
        *p = (cx + r * cosf(a), cy + r * sinf(a));
    }
    cv.polygon_px(&pts, c);
}

/// Paw in design units (the mouse cursor and the launch animation).
pub fn paw(cv: &mut Canvas, cx: f32, cy: f32, s: f32, c: Rgba) {
    let (x, y, s) = (cv.x(cx), cv.y(cy), cv.d(s));
    paw_px(cv, x, y, s, c);
}

/// Arc drawn as a chain of dots (icons only), angles in degrees, clockwise from 3 o'clock.
pub fn arc(cv: &mut Canvas, cx: f32, cy: f32, r: f32, a0: f32, a1: f32, w: f32, c: Rgba) {
    let steps = ((a1 - a0).abs() / 4.0) as i32 + 2;
    for i in 0..=steps {
        let a = (a0 + (a1 - a0) * i as f32 / steps as f32) * PI / 180.0;
        cv.ellipse(cx + r * cosf(a), cy + r * sinf(a), w / 2.0, w / 2.0, c);
    }
}

pub fn tri(cv: &mut Canvas, cx: f32, cy: f32, s: f32, dir: u8, c: Rgba) {
    let p = match dir {
        b'l' => [(cx - s, cy), (cx + s * 0.7, cy - s), (cx + s * 0.7, cy + s)],
        b'r' => [(cx + s, cy), (cx - s * 0.7, cy - s), (cx - s * 0.7, cy + s)],
        b'u' => [(cx, cy - s), (cx - s, cy + s * 0.7), (cx + s, cy + s * 0.7)],
        _ => [(cx, cy + s), (cx - s, cy - s * 0.7), (cx + s, cy - s * 0.7)],
    };
    cv.polygon(&p, c);
}

/// Width of a keycap; "LR" / "UD" / "LRUD" are arrow keys drawn as triangles (the fonts have no arrows).
pub fn keycap_w(cv: &Canvas, f: &mut Fonts, key: &str) -> f32 {
    match key { "LR" | "UD" => 56.0, "LRUD" => 100.0, _ => f.width(cv, Face::N900, 20.0, key) + 22.0 }
}

pub fn keycap(cv: &mut Canvas, f: &mut Fonts, th: &Theme, x: f32, y: f32, key: &str) -> f32 {
    let w = keycap_w(cv, f, key);
    cv.rrect(x, y + 3.0, w, 36.0, 7.0, th.ink);
    cv.rrect(x, y, w, 34.0, 7.0, th.ink);
    cv.rrect(x + 2.0, y + 2.0, w - 4.0, 30.0, 6.0, th.paper);
    let my = y + 17.0;
    match key {
        "LR" => { tri(cv, x + w / 2.0 - 11.0, my, 7.0, b'l', th.ink); tri(cv, x + w / 2.0 + 11.0, my, 7.0, b'r', th.ink); }
        "UD" => { tri(cv, x + w / 2.0 - 11.0, my, 7.0, b'u', th.ink); tri(cv, x + w / 2.0 + 11.0, my, 7.0, b'd', th.ink); }
        "LRUD" => {
            for (i, d) in [b'l', b'r', b'u', b'd'].iter().enumerate() { tri(cv, x + 20.0 + i as f32 * 20.0, my, 7.0, *d, th.ink); }
        }
        _ => f.draw(cv, Face::N900, 20.0, x + w / 2.0, my, Align::Center, th.ink, key),
    }
    w
}

/// Small coloured label ("ОБНОВЛЕНИЕ", "ПО УМОЛЧАНИЮ").
pub fn tag(cv: &mut Canvas, f: &mut Fonts, th: &Theme, x_right: f32, cy: f32, s: &str, col: Rgba, size: f32) -> f32 {
    let up = s;
    let w = f.width(cv, Face::N900, size, up) + 22.0;
    let h = size + 15.0;
    let x = x_right - w;
    cv.rrect(x, cy - h / 2.0, w, h, 7.0, th.ink);
    cv.rrect(x + 2.5, cy - h / 2.0 + 2.5, w - 5.0, h - 5.0, 5.5, col);
    f.draw(cv, Face::N900, size, x + w / 2.0, cy, Align::Center, th.ink, up);
    w
}

pub fn icon_small(cv: &mut Canvas, kind: u8, cx: f32, cy: f32, c: Rgba) {
    match kind {
        b'k' => {
            cv.rrect_outline(cx - 13.0, cy - 13.0, 26.0, 26.0, 4.0, 4.0, c);
            for i in [-6.0f32, 6.0] {
                cv.line(cx + i, cy - 13.0, cx + i, cy - 20.0, 4.0, c);
                cv.line(cx + i, cy + 13.0, cx + i, cy + 20.0, 4.0, c);
                cv.line(cx - 13.0, cy + i, cx - 20.0, cy + i, 4.0, c);
                cv.line(cx + 13.0, cy + i, cx + 20.0, cy + i, 4.0, c);
            }
        }
        b'u' => {
            cv.ring(cx, cy, 12.0, 4.0, c);
            for k in 0..8 {
                let a = PI / 4.0 * k as f32;
                cv.line(cx + 14.0 * cosf(a), cy + 14.0 * sinf(a), cx + 20.0 * cosf(a), cy + 20.0 * sinf(a), 5.0, c);
            }
        }
        b'r' => {
            arc(cv, cx, cy, 15.0, 40.0, 330.0, 5.0, c);
            cv.polygon(&[(cx + 6.0, cy - 23.0), (cx + 21.0, cy - 12.0), (cx + 4.0, cy - 5.0)], c);
        }
        _ => {
            arc(cv, cx, cy + 2.0, 15.0, -60.0, 240.0, 5.0, c);
            cv.line(cx, cy - 20.0, cx, cy - 2.0, 5.0, c);
        }
    }
}
