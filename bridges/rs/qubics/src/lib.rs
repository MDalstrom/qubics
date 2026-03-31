pub mod component;
pub mod plugin;
pub mod system;

pub use component::Component;

/// Re-exports for use by proc-macros (they reference these via `::qubics::reexport::…`).
pub mod reexport {
    pub use qubics_sys::ComponentDescriptor;
}

// Re-exported for use by proc-macro expansions in downstream crates.
#[doc(hidden)]
pub use inventory;

pub mod prelude {
    pub use crate::component::Component;
    pub use qubics_macros::{system, Component};
    pub use std::ffi::c_void;
}
