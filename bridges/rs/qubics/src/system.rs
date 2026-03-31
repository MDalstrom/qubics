use std::ffi::c_void;
use qubics_sys::ComponentDescriptor;

pub struct SystemRegistration {
    pub trampoline: unsafe extern "C" fn(*mut c_void, *mut c_void),
    pub reads: &'static [&'static ComponentDescriptor],
    pub writes: &'static [&'static ComponentDescriptor],
}

// SAFETY: SystemRegistration holds only function pointers and references to
// 'static data — both are safe to share across threads.
unsafe impl Sync for SystemRegistration {}

crate::inventory::collect!(SystemRegistration);
