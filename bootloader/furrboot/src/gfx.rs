//! Software drawing into an off-screen buffer that is copied to the screen in one go (no flicker).
//! Pixels are 0x00RRGGBB, the same layout as the firmware's BltPixel. Shape functions take
//! coordinates in *design units* (a 1920×1080 layout); `Canvas` scales and centres them.
//!
//! Speed: the x86_64-unknown-uefi target has MMX/SSE off ("disabled by default, to allow for
//! compilation of core UEFI code that runs before they are set up" — rustc platform docs), so every
//! f32 operation is emulated in software. Floats are therefore used only once per shape (layout);
//! everything done per pixel is integer, in 24.8 fixed point (`FX` = one pixel).

use alloc::vec;
use alloc::vec::Vec;

const FX: i32 = 256;

#[inline]
fn fx(v: f32) -> i32 { (v * FX as f32) as i32 }

/// A colour with alpha, 0xAARRGGBB.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Rgba(pub u32);

impl Rgba {
    pub const fn with_alpha(self, a: u8) -> Self { Self(self.0 & 0x00FF_FFFF | (a as u32) << 24) }
    pub const fn a(self) -> u32 { self.0 >> 24 }
}

/// x * a / 255 for x, a in 0..=255, without a division.
#[inline]
fn mul255(x: u32, a: u32) -> u32 { let t = x * a + 128; (t + (t >> 8)) >> 8 }

#[inline]
fn blend(dst: u32, src: u32, a: u32) -> u32 {
    // a in 0..=255 already includes the colour's own alpha and the coverage
    if a >= 255 { return src & 0x00FF_FFFF; }
    if a == 0 { return dst; }
    let inv = 255 - a;
    let r = mul255((src >> 16) & 0xFF, a) + mul255((dst >> 16) & 0xFF, inv);
    let g = mul255((src >> 8) & 0xFF, a) + mul255((dst >> 8) & 0xFF, inv);
    let b = mul255(src & 0xFF, a) + mul255(dst & 0xFF, inv);
    r << 16 | g << 8 | b
}

/// colour alpha (0..=255) × coverage (0..=FX) → blend alpha
#[inline]
fn alpha(ca: u32, cov: i32) -> u32 { (ca * cov.clamp(0, FX) as u32) >> 8 }

#[inline]
fn isqrt(v: u64) -> i32 { v.isqrt() as i32 }

/// Coverage (0..=FX) of a pixel centre (fixed) by a rounded rectangle (fixed edges, corner radius).
#[inline]
fn rr_cov(pcx: i32, pcy: i32, x0: i32, y0: i32, x1: i32, y1: i32, r: i32) -> i32 {
    let vx = (pcx - x0 + FX / 2).min(x1 - pcx + FX / 2).clamp(0, FX);
    let vy = (pcy - y0 + FX / 2).min(y1 - pcy + FX / 2).clamp(0, FX);
    if vx == 0 || vy == 0 { return 0; }
    let mut cov = vx * vy >> 8;
    let qx = if pcx < x0 + r { x0 + r - pcx } else if pcx > x1 - r { pcx - (x1 - r) } else { 0 };
    let qy = if pcy < y0 + r { y0 + r - pcy } else if pcy > y1 - r { pcy - (y1 - r) } else { 0 };
    if qx > 0 && qy > 0 {
        let d = isqrt(qx as u64 * qx as u64 + qy as u64 * qy as u64);
        cov = cov * (r - d + FX / 2).clamp(0, FX) >> 8;
    }
    cov
}

/// An RGBA picture (straight alpha), e.g. a decoded sticker.
pub struct Image {
    pub w: usize,
    pub h: usize,
    pub px: Vec<u32>, // 0xAARRGGBB
}

impl Image {
    /// Bilinear resize (fixed point); used once at start-up to fit the art to the screen size.
    pub fn scaled(&self, nw: usize, nh: usize) -> Image {
        let (nw, nh) = (nw.max(1), nh.max(1));
        let mut px = vec![0u32; nw * nh];
        // source position of a destination pixel centre, in 1/256 source pixels
        let sx = ((self.w as u64) << 8) / nw as u64;
        let sy = ((self.h as u64) << 8) / nh as u64;
        for y in 0..nh {
            let fy = ((y as i64 * sy as i64 + (sy as i64 >> 1)) - 128).max(0);
            let y0 = ((fy >> 8) as usize).min(self.h - 1);
            let y1 = (y0 + 1).min(self.h - 1);
            let ty = (fy & 0xFF) as u32;
            for x in 0..nw {
                let fxp = ((x as i64 * sx as i64 + (sx as i64 >> 1)) - 128).max(0);
                let x0 = ((fxp >> 8) as usize).min(self.w - 1);
                let x1 = (x0 + 1).min(self.w - 1);
                let tx = (fxp & 0xFF) as u32;
                let p = [self.px[y0 * self.w + x0], self.px[y0 * self.w + x1], self.px[y1 * self.w + x0], self.px[y1 * self.w + x1]];
                let wts = [(256 - tx) * (256 - ty), tx * (256 - ty), (256 - tx) * ty, tx * ty]; // sum 65536
                // premultiplied mix so transparent pixels don't bleed dark edges
                let (mut a, mut r, mut g, mut b) = (0u64, 0u64, 0u64, 0u64);
                for (c, wt) in p.iter().zip(wts) {
                    let ca = ((c >> 24) & 0xFF) as u64 * wt as u64;
                    a += ca;
                    r += ((c >> 16) & 0xFF) as u64 * ca;
                    g += ((c >> 8) & 0xFF) as u64 * ca;
                    b += (c & 0xFF) as u64 * ca;
                }
                px[y * nw + x] = if a < 32768 { 0 } else {
                    ((a >> 16).min(255) as u32) << 24 | ((r / a).min(255) as u32) << 16 | ((g / a).min(255) as u32) << 8 | (b / a).min(255) as u32
                };
            }
        }
        Image { w: nw, h: nh, px }
    }
}

pub struct Canvas {
    pub w: usize,
    pub h: usize,
    pub px: Vec<u32>,
    /// design units → pixels
    pub s: f32,
    pub ox: f32,
    pub oy: f32,
    /// clip rectangle in pixels (x0, y0, x1, y1)
    clip: (i32, i32, i32, i32),
    scratch: Vec<i32>,
}

impl Canvas {
    pub fn new(w: usize, h: usize) -> Self {
        let s = (w as f32 / 1920.0).min(h as f32 / 1080.0);
        let ox = (w as f32 - 1920.0 * s) / 2.0;
        let oy = (h as f32 - 1080.0 * s) / 2.0;
        Self { w, h, px: vec![0; w * h], s, ox, oy, clip: (0, 0, w as i32, h as i32), scratch: Vec::new() }
    }

    #[inline]
    pub fn x(&self, v: f32) -> f32 { self.ox + v * self.s }
    #[inline]
    pub fn y(&self, v: f32) -> f32 { self.oy + v * self.s }
    #[inline]
    pub fn d(&self, v: f32) -> f32 { v * self.s }
    /// pixel → design units (for the mouse)
    pub fn to_design(&self, px: f32, py: f32) -> (f32, f32) { ((px - self.ox) / self.s, (py - self.oy) / self.s) }

    pub fn set_clip(&mut self, x: f32, y: f32, w: f32, h: f32) {
        let (x0, y0) = (self.x(x) as i32, self.y(y) as i32);
        let (x1, y1) = (self.x(x + w) as i32, self.y(y + h) as i32);
        self.clip = (x0.max(0), y0.max(0), x1.min(self.w as i32), y1.min(self.h as i32));
    }
    pub fn reset_clip(&mut self) { self.clip = (0, 0, self.w as i32, self.h as i32); }

    /// One pixel with an alpha 0..=255 (already including coverage).
    #[inline]
    pub fn plot_a(&mut self, x: i32, y: i32, src: u32, a: u32) {
        let (cx0, cy0, cx1, cy1) = self.clip;
        if x < cx0 || y < cy0 || x >= cx1 || y >= cy1 { return; }
        let i = y as usize * self.w + x as usize;
        self.px[i] = blend(self.px[i], src, a);
    }

    /// Plain rectangle in pixels (no scaling), used for full-screen fills.
    pub fn fill_px(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, c: Rgba) {
        let (cx0, cy0, cx1, cy1) = self.clip;
        let (x0, y0, x1, y1) = (x0.max(cx0), y0.max(cy0), x1.min(cx1), y1.min(cy1));
        if x1 <= x0 || y1 <= y0 { return; }
        let a = c.a();
        for y in y0..y1 {
            let row = &mut self.px[y as usize * self.w + x0 as usize..y as usize * self.w + x1 as usize];
            if a >= 255 { row.fill(c.0 & 0x00FF_FFFF); } else { for p in row.iter_mut() { *p = blend(*p, c.0, a); } }
        }
    }

    /// Filled rounded rectangle with smooth (anti-aliased) corners, design units.
    pub fn rrect(&mut self, x: f32, y: f32, w: f32, h: f32, r: f32, c: Rgba) {
        if w <= 0.0 || h <= 0.0 { return; }
        let (px0, py0, pw, ph) = (self.x(x), self.y(y), self.d(w), self.d(h));
        let r = self.d(r).min(pw / 2.0).min(ph / 2.0).max(0.0);
        self.rrect_fx(fx(px0), fx(py0), fx(px0 + pw), fx(py0 + ph), fx(r), c);
    }

    fn rrect_fx(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, r: i32, c: Rgba) {
        let (cx0, cy0, cx1, cy1) = self.clip;
        let ca = c.a();
        let (pxa, pxb) = ((x0 >> 8).max(cx0), ((x1 + FX - 1) >> 8).min(cx1));
        let (pya, pyb) = ((y0 >> 8).max(cy0), ((y1 + FX - 1) >> 8).min(cy1));
        // columns strictly inside the straight part of the edges need no per-pixel work
        let inner_x0 = (x0 + r + FX) >> 8;
        let inner_x1 = (x1 - r - FX) >> 8;
        for py in pya..pyb {
            let pcy = py * FX + FX / 2;
            let row = py as usize * self.w;
            let in_band = pcy >= y0 + r + FX / 2 && pcy <= y1 - r - FX / 2;
            let vy = (pcy - y0 + FX / 2).min(y1 - pcy + FX / 2).clamp(0, FX);
            if vy == 0 { continue; }
            let mut px = pxa;
            while px < pxb {
                if in_band && px >= inner_x0 && px < inner_x1 && vy == FX {
                    // solid run
                    let end = inner_x1.min(pxb);
                    let s = &mut self.px[row + px as usize..row + end as usize];
                    if ca >= 255 { s.fill(c.0 & 0x00FF_FFFF); } else { for p in s.iter_mut() { *p = blend(*p, c.0, ca); } }
                    px = end;
                    continue;
                }
                let cov = rr_cov(px * FX + FX / 2, pcy, x0, y0, x1, y1, r);
                if cov > 0 {
                    let i = row + px as usize;
                    self.px[i] = blend(self.px[i], c.0, alpha(ca, cov));
                }
                px += 1;
            }
        }
    }

    /// The comic "sticker" box: hard shadow, coloured edge, filled middle.
    pub fn comic_box(&mut self, x: f32, y: f32, w: f32, h: f32, r: f32, fill: Rgba, edge: Rgba, bw: f32, shadow: Option<(Rgba, f32)>) {
        if let Some((sc, off)) = shadow { self.rrect(x + off, y + off, w, h, r, sc); }
        self.rrect(x, y, w, h, r, edge);
        self.rrect(x + bw, y + bw, w - 2.0 * bw, h - 2.0 * bw, (r - bw).max(0.0), fill);
    }

    /// Outline only (ring) of a rounded rectangle.
    pub fn rrect_outline(&mut self, x: f32, y: f32, w: f32, h: f32, r: f32, bw: f32, c: Rgba) {
        let (ox, oy, ow, oh) = (self.x(x), self.y(y), self.d(w), self.d(h));
        let b = self.d(bw);
        let ro = self.d(r).min(ow / 2.0).min(oh / 2.0);
        let ri = (ro - b).max(0.0);
        let (o0, o1, o2, o3, orr) = (fx(ox), fx(oy), fx(ox + ow), fx(oy + oh), fx(ro));
        let (i0, i1, i2, i3, irr) = (fx(ox + b), fx(oy + b), fx(ox + ow - b), fx(oy + oh - b), fx(ri));
        let (cx0, cy0, cx1, cy1) = self.clip;
        let ca = c.a();
        let bpx = (b as i32) + 2;
        for py in (o1 >> 8).max(cy0)..((o3 + FX - 1) >> 8).min(cy1) {
            let pcy = py * FX + FX / 2;
            let row = py as usize * self.w;
            // rows in the middle only touch the left and right bands
            let mid = pcy > i1 + irr + FX && pcy < i3 - irr - FX;
            let mut px = (o0 >> 8).max(cx0);
            let end = ((o2 + FX - 1) >> 8).min(cx1);
            while px < end {
                if mid && px > (o0 >> 8) + bpx && px < (o2 >> 8) - bpx { px = (o2 >> 8) - bpx; continue; }
                let pcx = px * FX + FX / 2;
                let outer = rr_cov(pcx, pcy, o0, o1, o2, o3, orr);
                if outer > 0 {
                    let inner = if i2 > i0 && i3 > i1 { rr_cov(pcx, pcy, i0, i1, i2, i3, irr) } else { 0 };
                    let cov = outer - inner;
                    if cov > 0 {
                        let i = row + px as usize;
                        self.px[i] = blend(self.px[i], c.0, alpha(ca, cov));
                    }
                }
                px += 1;
            }
        }
    }

    /// Filled ellipse (anti-aliased), design units: centre and radii.
    pub fn ellipse(&mut self, cx: f32, cy: f32, rx: f32, ry: f32, c: Rgba) {
        let (cx, cy, rx, ry) = (self.x(cx), self.y(cy), self.d(rx), self.d(ry));
        self.ellipse_px(cx, cy, rx, ry, c);
    }

    pub fn ellipse_px(&mut self, cx: f32, cy: f32, rx: f32, ry: f32, c: Rgba) {
        if rx <= 0.0 || ry <= 0.0 { return; }
        let (fcx, fcy, frx) = (fx(cx), fx(cy), fx(rx));
        // squash y so the ellipse becomes a circle of radius rx
        let k = fx(rx / ry); // y scale, fixed
        let (cx0, cy0, cx1, cy1) = self.clip;
        let ca = c.a();
        for py in ((fx(cy - ry) >> 8) - 1).max(cy0)..((fx(cy + ry) >> 8) + 2).min(cy1) {
            let dy = ((py * FX + FX / 2 - fcy) as i64 * k as i64 >> 8) as i64;
            let row = py as usize * self.w;
            for px in ((fx(cx - rx) >> 8) - 1).max(cx0)..((fx(cx + rx) >> 8) + 2).min(cx1) {
                let dx = (px * FX + FX / 2 - fcx) as i64;
                let d = isqrt((dx * dx + dy * dy) as u64);
                let cov = frx - d + FX / 2;
                if cov <= 0 { continue; }
                let i = row + px as usize;
                self.px[i] = blend(self.px[i], c.0, alpha(ca, cov));
            }
        }
    }

    /// Ring (circle outline) of width `bw`, design units.
    pub fn ring(&mut self, cx: f32, cy: f32, r: f32, bw: f32, c: Rgba) {
        let (cx, cy, r, bw) = (self.x(cx), self.y(cy), self.d(r), self.d(bw));
        let (fcx, fcy) = (fx(cx), fx(cy));
        let (ro, ri) = (fx(r + bw / 2.0), fx(r - bw / 2.0));
        let (cx0, cy0, cx1, cy1) = self.clip;
        let ca = c.a();
        let rpx = (ro >> 8) + 2;
        for py in ((fcy >> 8) - rpx).max(cy0)..((fcy >> 8) + rpx).min(cy1) {
            let dy = (py * FX + FX / 2 - fcy) as i64;
            let row = py as usize * self.w;
            for px in ((fcx >> 8) - rpx).max(cx0)..((fcx >> 8) + rpx).min(cx1) {
                let dx = (px * FX + FX / 2 - fcx) as i64;
                let d = isqrt((dx * dx + dy * dy) as u64);
                let cov = (ro - d + FX / 2).clamp(0, FX) * (d - ri + FX / 2).clamp(0, FX) >> 8;
                if cov <= 0 { continue; }
                let i = row + px as usize;
                self.px[i] = blend(self.px[i], c.0, alpha(ca, cov));
            }
        }
    }

    /// Filled polygon (even-odd scanline, 4 sub-rows per pixel for soft edges), design units.
    pub fn polygon(&mut self, pts: &[(f32, f32)], c: Rgba) {
        let mut p = [(0i32, 0i32); 64];
        let n = pts.len().min(64);
        for (i, &(x, y)) in pts.iter().take(n).enumerate() { p[i] = (fx(self.x(x)), fx(self.y(y))); }
        self.polygon_fx(&p[..n], c);
    }

    pub fn polygon_px(&mut self, pts: &[(f32, f32)], c: Rgba) {
        let mut p = [(0i32, 0i32); 64];
        let n = pts.len().min(64);
        for (i, &(x, y)) in pts.iter().take(n).enumerate() { p[i] = (fx(x), fx(y)); }
        self.polygon_fx(&p[..n], c);
    }

    fn polygon_fx(&mut self, p: &[(i32, i32)], c: Rgba) {
        if p.len() < 3 { return; }
        let (cx0, cy0, cx1, cy1) = self.clip;
        let ymin = p.iter().map(|q| q.1).min().unwrap_or(0);
        let ymax = p.iter().map(|q| q.1).max().unwrap_or(0);
        let xmin = p.iter().map(|q| q.0).min().unwrap_or(0);
        let xmax = p.iter().map(|q| q.0).max().unwrap_or(0);
        let x0 = (xmin >> 8).max(cx0);
        let x1 = ((xmax >> 8) + 1).min(cx1);
        if x1 <= x0 { return; }
        let width = (x1 - x0) as usize;
        let mut acc = core::mem::take(&mut self.scratch);
        acc.clear();
        acc.resize(width, 0);
        const SUB: i32 = 4;
        let ca = c.a();
        let mut xs = [0i32; 64];
        for py in (ymin >> 8).max(cy0)..((ymax >> 8) + 1).min(cy1) {
            for v in acc.iter_mut() { *v = 0; }
            let mut any = false;
            for s in 0..SUB {
                let fy = py * FX + (s * FX + FX / 2) / SUB;
                let mut n = 0;
                for i in 0..p.len() {
                    let (ax, ay) = p[i];
                    let (bx, by) = p[(i + 1) % p.len()];
                    if (ay <= fy && by > fy) || (by <= fy && ay > fy) {
                        xs[n] = ax + ((fy - ay) as i64 * (bx - ax) as i64 / (by - ay) as i64) as i32;
                        n += 1;
                    }
                }
                xs[..n].sort_unstable();
                let mut k = 0;
                while k + 1 < n {
                    let (l, r) = (xs[k].max(x0 * FX), xs[k + 1].min(x1 * FX));
                    k += 2;
                    if r <= l { continue; }
                    any = true;
                    let (li, ri) = (l >> 8, (r - 1) >> 8);
                    if li == ri {
                        acc[(li - x0) as usize] += r - l;
                    } else {
                        acc[(li - x0) as usize] += (li + 1) * FX - l;
                        for x in li + 1..ri { acc[(x - x0) as usize] += FX; }
                        acc[(ri - x0) as usize] += r - ri * FX;
                    }
                }
            }
            if !any { continue; }
            let row = py as usize * self.w;
            for (k, cov) in acc.iter().enumerate() {
                if *cov <= 0 { continue; }
                let i = row + x0 as usize + k;
                self.px[i] = blend(self.px[i], c.0, alpha(ca, *cov / SUB));
            }
        }
        self.scratch = acc;
    }

    /// Thick line as a quad, design units.
    pub fn line(&mut self, x0: f32, y0: f32, x1: f32, y1: f32, w: f32, c: Rgba) {
        let (dx, dy) = (x1 - x0, y1 - y0);
        let len = libm::sqrtf(dx * dx + dy * dy).max(0.0001);
        let (nx, ny) = (-dy / len * w / 2.0, dx / len * w / 2.0);
        self.polygon(&[(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], c);
        // round caps
        self.ellipse(x0, y0, w / 2.0, w / 2.0, c);
        self.ellipse(x1, y1, w / 2.0, w / 2.0, c);
    }

    /// Picture at a pixel position (already scaled), with an extra opacity.
    pub fn image_px(&mut self, img: &Image, x: i32, y: i32, opacity: f32) {
        let (cx0, cy0, cx1, cy1) = self.clip;
        let op = (opacity.clamp(0.0, 1.0) * 255.0) as u32;
        let xa = (cx0 - x).max(0);
        let xb = (cx1 - x).min(img.w as i32);
        if xb <= xa { return; }
        for iy in 0..img.h as i32 {
            let py = y + iy;
            if py < cy0 || py >= cy1 { continue; }
            let row = py as usize * self.w;
            let srow = iy as usize * img.w;
            for ix in xa..xb {
                let s = img.px[srow + ix as usize];
                let a = if op >= 255 { s >> 24 } else { mul255(s >> 24, op) };
                if a == 0 { continue; }
                let i = row + (x + ix) as usize;
                self.px[i] = blend(self.px[i], s, a);
            }
        }
    }

    /// Alpha mask (a rendered glyph) at a pixel position.
    pub fn mask_px(&mut self, mask: &[u8], mw: usize, mh: usize, x: i32, y: i32, c: Rgba) {
        let (cx0, cy0, cx1, cy1) = self.clip;
        let ca = c.a();
        for my in 0..mh as i32 {
            let py = y + my;
            if py < cy0 || py >= cy1 { continue; }
            let row = py as usize * self.w;
            for mx in 0..mw as i32 {
                let px = x + mx;
                if px < cx0 || px >= cx1 { continue; }
                let m = mask[my as usize * mw + mx as usize] as u32;
                if m == 0 { continue; }
                let i = row + px as usize;
                self.px[i] = blend(self.px[i], c.0, if ca >= 255 { m } else { mul255(m, ca) });
            }
        }
    }
}
