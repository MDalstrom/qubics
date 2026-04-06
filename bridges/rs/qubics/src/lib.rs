use linkme::distributed_slice;

pub use qubics_macros::{bake, render, simulate};

include!(concat!(env!("OUT_DIR"), "/bindings.rs"));

#[doc(hidden)]
#[derive(Clone, Copy)]
pub struct ComponentMeta {
    pub id: u32,
    pub stride: usize,
}

#[doc(hidden)]
pub struct BakeEntry {
    pub run: unsafe extern "C" fn(*mut WorldApi),
}
unsafe impl Send for BakeEntry {}
unsafe impl Sync for BakeEntry {}

#[doc(hidden)]
pub struct SimulationEntry {
    pub run: unsafe extern "C" fn(*mut WorldApi, *const SimulationState),
    pub reads: &'static [ComponentMeta],
    pub writes: &'static [ComponentMeta],
}
unsafe impl Send for SimulationEntry {}
unsafe impl Sync for SimulationEntry {}

#[doc(hidden)]
pub struct RenderEntry {
    pub run: unsafe extern "C" fn(*mut WorldApi, *mut core::ffi::c_void),
    pub reads: &'static [ComponentMeta],
    pub writes: &'static [ComponentMeta],
}
unsafe impl Send for RenderEntry {}
unsafe impl Sync for RenderEntry {}

#[doc(hidden)]
#[distributed_slice]
pub static BAKE_SYSTEMS: [BakeEntry] = [..];

#[doc(hidden)]
#[distributed_slice]
pub static SIMULATION_SYSTEMS: [SimulationEntry] = [..];

#[doc(hidden)]
#[distributed_slice]
pub static RENDER_SYSTEMS: [RenderEntry] = [..];

unsafe fn resolve(
    registry: &RegistryApi,
    components: &[ComponentMeta],
) -> Vec<ComponentDescriptor> {
    components
        .iter()
        .map(|info| {
            let found = (registry.find.unwrap())(info.id);
            if !found.is_null() {
                found
            } else {
                (registry.register_generic.unwrap())(info.id, info.stride)
            }
        })
        .collect()
}

fn build_archetype(ptrs: Vec<ComponentDescriptor>) -> Archetype {
    let generic_count = ptrs.len();
    let generic = if ptrs.is_empty() {
        core::ptr::null_mut()
    } else {
        Box::into_raw(ptrs.into_boxed_slice()) as *mut ComponentDescriptor
    };
    Archetype {
        generic,
        generic_count,
        shared: core::ptr::null_mut(),
        shared_count: 0,
    }
}

fn empty_archetype() -> Archetype {
    Archetype {
        generic: core::ptr::null_mut(),
        generic_count: 0,
        shared: core::ptr::null_mut(),
        shared_count: 0,
    }
}

static mut G_REGISTRY: core::mem::MaybeUninit<RegistryApi> = core::mem::MaybeUninit::uninit();

pub unsafe fn registry() -> &'static RegistryApi {
    G_REGISTRY.assume_init_ref()
}

#[no_mangle]
pub unsafe extern "C" fn qubics_plugin(registry: RegistryApi) -> PluginState {
    G_REGISTRY.write(registry);

    let bake: Vec<SystemDescriptor> = BAKE_SYSTEMS
        .iter()
        .map(|entry| SystemDescriptor {
            fn_: Some(core::mem::transmute(entry.run)),
            reads: empty_archetype(),
            writes: empty_archetype(),
        })
        .collect();

    let simulation: Vec<SystemDescriptor> = SIMULATION_SYSTEMS
        .iter()
        .map(|entry| SystemDescriptor {
            fn_: Some(core::mem::transmute(entry.run)),
            reads: build_archetype(resolve(&registry, entry.reads)),
            writes: build_archetype(resolve(&registry, entry.writes)),
        })
        .collect();

    let render: Vec<SystemDescriptor> = RENDER_SYSTEMS
        .iter()
        .map(|entry| SystemDescriptor {
            fn_: Some(core::mem::transmute(entry.run)),
            reads: build_archetype(resolve(&registry, entry.reads)),
            writes: build_archetype(resolve(&registry, entry.writes)),
        })
        .collect();

    fn vec_into_raw<T>(v: Vec<T>) -> *mut T {
        if v.is_empty() {
            return core::ptr::null_mut();
        }
        Box::into_raw(v.into_boxed_slice()) as *mut T
    }

    PluginState {
        bake_count: bake.len(),
        bake: vec_into_raw(bake),
        simulation_count: simulation.len(),
        simulation: vec_into_raw(simulation),
        render_count: render.len(),
        render: vec_into_raw(render),
    }
}
