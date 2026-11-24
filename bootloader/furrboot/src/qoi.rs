//! QOI image decoder (qoiformat.org) for the art baked into FurrBoot.

use crate::gfx::Image;
use alloc::vec::Vec;

pub fn decode(data: &[u8]) -> Option<Image> {
    if data.len() < 22 || &data[..4] != b"qoif" { return None; }
    let w = u32::from_be_bytes([data[4], data[5], data[6], data[7]]) as usize;
    let h = u32::from_be_bytes([data[8], data[9], data[10], data[11]]) as usize;
    if w == 0 || h == 0 || w * h > 16_000_000 { return None; }
    let n = w * h;
    let mut out: Vec<u32> = Vec::with_capacity(n);
    let mut index = [[0u8; 4]; 64];
    let mut p = [0u8, 0, 0, 255];
    let mut i = 14;
    let mut run = 0u32;
    while out.len() < n {
        if run > 0 {
            run -= 1;
        } else {
            let b1 = *data.get(i)?;
            i += 1;
            match b1 {
                0xFE => { p[0] = *data.get(i)?; p[1] = *data.get(i + 1)?; p[2] = *data.get(i + 2)?; i += 3; }
                0xFF => { p.copy_from_slice(data.get(i..i + 4)?); i += 4; }
                _ => match b1 >> 6 {
                    0 => p = index[b1 as usize],
                    1 => {
                        p[0] = p[0].wrapping_add(((b1 >> 4) & 3).wrapping_sub(2));
                        p[1] = p[1].wrapping_add(((b1 >> 2) & 3).wrapping_sub(2));
                        p[2] = p[2].wrapping_add((b1 & 3).wrapping_sub(2));
                    }
                    2 => {
                        let b2 = *data.get(i)?;
                        i += 1;
                        let dg = (b1 & 0x3F).wrapping_sub(32);
                        p[0] = p[0].wrapping_add(dg.wrapping_sub(8).wrapping_add((b2 >> 4) & 0x0F));
                        p[1] = p[1].wrapping_add(dg);
                        p[2] = p[2].wrapping_add(dg.wrapping_sub(8).wrapping_add(b2 & 0x0F));
                    }
                    _ => run = (b1 & 0x3F) as u32,
                },
            }
        }
        let h = (p[0] as usize * 3 + p[1] as usize * 5 + p[2] as usize * 7 + p[3] as usize * 11) % 64;
        index[h] = p;
        out.push((p[3] as u32) << 24 | (p[0] as u32) << 16 | (p[1] as u32) << 8 | p[2] as u32);
    }
    Some(Image { w, h, px: out })
}
