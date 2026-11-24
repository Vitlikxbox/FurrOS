//! FurrBoot's own settings that the menu can change, kept in a non-volatile EFI variable so they survive a
//! reboot without writing to the disk (UEFI SetVariable, spec 2.10 §8.2). FurrOS can read and write them too:
//! /sys/firmware/efi/efivars/FurrBootTheme-9868b1f9-c27c-4bbd-926e-76ef5b5ada1a (4 bytes of attributes, then
//! the theme name in ASCII).

use alloc::string::String;
use uefi::runtime::{self, VariableAttributes, VariableVendor};
use uefi::{cstr16, guid};

const VENDOR: VariableVendor = VariableVendor(guid!("9868b1f9-c27c-4bbd-926e-76ef5b5ada1a"));

pub fn theme() -> Option<String> {
    let (data, _) = runtime::get_variable_boxed(cstr16!("FurrBootTheme"), &VENDOR).ok()?;
    let s = core::str::from_utf8(&data).ok()?.trim_matches(char::from(0)).trim();
    if s.is_empty() || s.len() > 32 { None } else { Some(s.into()) }
}

pub fn set_theme(name: &str) -> bool {
    let attrs = VariableAttributes::NON_VOLATILE | VariableAttributes::BOOTSERVICE_ACCESS | VariableAttributes::RUNTIME_ACCESS;
    runtime::set_variable(cstr16!("FurrBootTheme"), &VENDOR, attrs, name.as_bytes()).is_ok()
}
