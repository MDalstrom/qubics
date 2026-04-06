use core::mem::size_of;
use qubics::{bake, Archetype, WorldApi};

include!(concat!(env!("OUT_DIR"), "/bindings.rs"));

fn component_id(name: &str) -> u32 {
    const FNV_OFFSET: u32 = 2166136261;
    const FNV_PRIME: u32 = 16777619;
    name.bytes().fold(FNV_OFFSET, |hash, b| hash.wrapping_mul(FNV_PRIME) ^ b as u32)
}

static TRIANGLE_VERTS: [f32; 6] = [
    -0.5, -0.5,
     0.5, -0.5,
     0.0,  0.5,
];

static mut MESH: Mesh2DShared = Mesh2DShared {
    vertex_buffer: TRIANGLE_VERTS.as_ptr() as *mut _,
    vertex_count: 3,
    color: [1.0, 0.5, 0.2, 1.0],
};

#[bake]
fn setup(world: WorldApi) {
    unsafe {
        let registry = qubics::registry();

        let transform_desc = (registry.register_generic.unwrap())(component_id("Transform"), size_of::<Transform>());
        let viewport_desc  = (registry.register_generic.unwrap())(component_id("Viewport"),  size_of::<Viewport>());
        let mesh_desc      = (registry.register_shared.unwrap())(component_id("Mesh2DShared"), core::ptr::addr_of_mut!(MESH).cast());

        let mut cam_comps = [viewport_desc, transform_desc];
        let cam_arch = Archetype {
            generic: cam_comps.as_mut_ptr(),
            generic_count: 2,
            shared: core::ptr::null_mut(),
            shared_count: 0,
        };
        (world.create_entity.unwrap())(cam_arch);

        let cam_r = (world.query_at_least.unwrap())(cam_arch);
        let chunk_bufs = *cam_r.buffers as *mut *mut core::ffi::c_void;
        *(*chunk_bufs as *mut Viewport) = Viewport {
            left: -1.0, right: 1.0, bottom: -1.0, top: 1.0,
            near_z: -1.0, far_z: 1.0,
        };
        *(*chunk_bufs.add(1) as *mut Transform) = Transform {
            matrix: [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
        };

        let mut tri_comps  = [transform_desc];
        let mut tri_shared = [mesh_desc];
        let tri_arch = Archetype {
            generic: tri_comps.as_mut_ptr(),
            generic_count: 1,
            shared: tri_shared.as_mut_ptr(),
            shared_count: 1,
        };
        (world.create_entity.unwrap())(tri_arch);

        let tri_r = (world.query_at_least.unwrap())(tri_arch);
        let tri_bufs = *tri_r.buffers as *mut *mut core::ffi::c_void;
        *(*tri_bufs as *mut Transform) = Transform {
            matrix: [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
        };
    }
}
