use qubics::prelude::*;

#[derive(Component)]
struct Position {
    x: f32,
    y: f32,
}

#[system(writes = [Position])]
fn hello(_world: *mut c_void) {
    println!("hello from rust!");
}
