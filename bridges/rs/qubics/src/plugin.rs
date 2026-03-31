use qubics_sys::{Archetype, PluginSystems, Registry, SystemDescriptor};

use crate::system::SystemRegistration;

/// Collects all systems registered via `#[system]` and returns them as a
/// C-compatible `PluginSystems` struct for the entrypoint to schedule.
///
/// # Memory contract
/// - `PluginSystems.descriptors` is heap-allocated via the global allocator
///   (Box) and must be freed with `free()` by the caller — which entrypoint
///   already does (`free(ps.descriptors)`).
/// - `Archetype.descriptors` arrays inside each `SystemDescriptor` point into
///   `'static` Rust memory and must NOT be freed by the caller.
#[no_mangle]
pub unsafe extern "C" fn qubics_plugin(_registry: *mut Registry) -> PluginSystems {
    let descriptors: Vec<SystemDescriptor> = inventory::iter::<SystemRegistration>()
        .map(|reg| {
            // The static slices live in the binary's data segment — valid forever.
            // Cast away const for C's non-const pointer fields; C never mutates them.
            let reads_ptr = reg.reads.as_ptr() as *mut *mut qubics_sys::ComponentDescriptor;
            let writes_ptr = reg.writes.as_ptr() as *mut *mut qubics_sys::ComponentDescriptor;

            SystemDescriptor {
                run: Some(reg.trampoline),
                reads: Archetype {
                    length: reg.reads.len(),
                    descriptors: reads_ptr,
                },
                writes: Archetype {
                    length: reg.writes.len(),
                    descriptors: writes_ptr,
                },
            }
        })
        .collect();

    let count = descriptors.len();
    // Leak the Vec so C can call free() on the raw pointer.
    let ptr = Box::into_raw(descriptors.into_boxed_slice()) as *mut SystemDescriptor;

    PluginSystems {
        descriptors: ptr,
        count,
    }
}
