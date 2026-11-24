//! Monotonic milliseconds from the CPU time-stamp counter, calibrated once against the firmware's
//! Stall() (UEFI has no monotonic clock service of its own while boot services run).

use core::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use core::time::Duration;

static T0: AtomicU64 = AtomicU64::new(0);
static PER_MS: AtomicU32 = AtomicU32::new(0); // f32 bits

fn tsc() -> u64 { unsafe { core::arch::x86_64::_rdtsc() } }

pub fn calibrate() {
    let a = tsc();
    uefi::boot::stall(Duration::from_millis(50));
    let b = tsc();
    let per_ms = ((b - a) as f32 / 50.0).max(1.0);
    PER_MS.store(per_ms.to_bits(), Ordering::Relaxed);
    T0.store(b, Ordering::Relaxed);
}

pub fn ms() -> f32 {
    let per = f32::from_bits(PER_MS.load(Ordering::Relaxed));
    if per <= 0.0 { return 0.0; }
    (tsc() - T0.load(Ordering::Relaxed)) as f32 / per
}

/// TSC ticks per millisecond (0 before calibrate()).
pub fn per_ms() -> f32 { f32::from_bits(PER_MS.load(Ordering::Relaxed)) }
