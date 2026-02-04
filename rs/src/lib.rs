#[allow(dead_code, unused_imports)]
pub mod generated {
    include!(concat!(env!("OUT_DIR"), "/components_generated.rs"));
}

pub use generated::*;
