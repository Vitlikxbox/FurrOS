//! Colour themes. "comic" is the FurrOS look (same palette as furros.xyz).

use crate::gfx::Rgba;

#[derive(Clone, Copy)]
pub struct Theme {
    pub night: Rgba,
    pub plum: Rgba,
    pub paper: Rgba,
    pub ink: Rgba,
    pub cyan: Rgba,
    pub pink: Rgba,
    pub red: Rgba,
    pub yellow: Rgba,
    pub green: Rgba,
    pub maroon: Rgba,
    pub dim: Rgba,
    pub soft: Rgba,
    pub card: Rgba,
}

const fn hex(v: u32) -> Rgba { Rgba(0xFF00_0000 | v) }

pub const COMIC: Theme = Theme {
    night: hex(0x150B11), plum: hex(0x1E1218), paper: hex(0xFFECEC), ink: hex(0x0E080B),
    cyan: hex(0x7FF0F0), pink: hex(0xFF8CBE), red: hex(0xE23A44), yellow: hex(0xFFBE5A),
    green: hex(0x78E6A0), maroon: hex(0x781C2C), dim: hex(0xC8AAB4), soft: hex(0x4A2F3A), card: hex(0xFFF8F5),
};

/// Order of the T key and of i18n theme_names.
pub const NAMES: [&str; 6] = ["comic", "neon", "pastel", "night", "forest", "mono"];

pub fn by_name(name: &str) -> Theme {
    let mut t = COMIC;
    match name {
        "neon" => {
            t.cyan = hex(0x3DF5FF); t.pink = hex(0xFF3DCB); t.red = hex(0xFF2E63); t.yellow = hex(0xF9F871);
            t.green = hex(0x3DFF9A); t.maroon = hex(0x5A0FC8); t.night = hex(0x07040D); t.plum = hex(0x140C22); t.paper = hex(0xF2EBFF);
        }
        "pastel" => {
            t.cyan = hex(0xA8E6E2); t.pink = hex(0xF7B8D2); t.red = hex(0xE86A73); t.yellow = hex(0xFFD58A);
            t.green = hex(0xA6E8C0); t.maroon = hex(0x8E3B4C); t.night = hex(0x1C1418); t.plum = hex(0x271C21);
        }
        "night" => {
            t.cyan = hex(0x7FD0FF); t.pink = hex(0xB69CFF); t.red = hex(0xFF5C7A); t.yellow = hex(0xFFC56B);
            t.green = hex(0x7CF0B2); t.maroon = hex(0x1E3A8A); t.night = hex(0x0A0F1F); t.plum = hex(0x141B33); t.paper = hex(0xE9F0FF);
        }
        "forest" => {
            t.cyan = hex(0x9BE39B); t.pink = hex(0xF4B860); t.red = hex(0xE2603A); t.yellow = hex(0xF2D06B);
            t.green = hex(0xB8F28C); t.maroon = hex(0x2F5D3A); t.night = hex(0x0C130E); t.plum = hex(0x17221A); t.paper = hex(0xF1F5E8);
        }
        "mono" => {
            t.cyan = hex(0xFFFFFF); t.pink = hex(0xD9D9D9); t.red = hex(0xFF4D4D); t.yellow = hex(0xE6E6E6);
            t.green = hex(0xCFCFCF); t.maroon = hex(0x3A3A3A); t.night = hex(0x0B0B0B); t.plum = hex(0x181818); t.paper = hex(0xF2F2F2);
            t.dim = hex(0xB3B3B3);
        }
        _ => {}
    }
    t
}
