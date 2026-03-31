# Qubics [WIP]

A plugin-based game engine where every part is a package managed by EPK.

## Packages

A package produces a set of `.dylib` and `.h` files. Two contracts define how packages interact with the engine:

**Backend contract** (`void run(tick_function)`) — a backend owns the main loop and calls the provided tick function each frame.

**Plugin contract** (`PluginSystems qubics_plugin(Registry*)`) — a plugin registers components in the registry and returns an array of `SystemDescriptor`s. Each descriptor carries a function pointer plus read/write archetype declarations, which the scheduler uses to sort systems into parallel stages.

The ECS core itself is also a package, providing World, Registry, and Scheduler as a shared library.

## Bootstrapping

`make run` resolves all packages into `build/`. The C entrypoint loads `build/ecs/ecs.dylib` first, then iterates over subdirectories looking for `.dylib` files that export either:

- `run` (`void (*)(tick_function)`) — the backend
- `qubics_plugin` (`PluginSystems (*)(Registry*)`) — a plugin

It collects all system descriptors into a scheduler, finds the backend, and enters its main loop.

## EPK package manager

EPK (implementation in `packages/`) manages the dependency graph. Each package has a `manifest.toml` declaring name, version, and deps. The workflow:

1. `epk add <path>` — registers a package source in the local registry (`~/.local/share/epk/`)
2. `epk install` — resolves the root `manifest.toml`, locks versions, fetches/builds packages, and symlinks artifacts into `build/`

**Hot-reloading:** `epk watch` runs alongside the entrypoint. It polls each package with `make -q` to check if sources are newer than artifacts, rebuilds what changed, and touches a `.stamp` file in the build directory. The C entrypoint checks `.stamp` mtime on every tick and reloads all plugins when it changes.

## Rust bridge (currently vibe-coded)

The Rust bridge (`bridges/rs/`) lets you write plugins in Rust. It provides:

- `#[derive(Component)]` — generates a static `ComponentDescriptor` for a struct
- `#[system(reads = [A], writes = [B])]` — wraps a function into a C-compatible trampoline and auto-registers it via `inventory`, so `qubics_plugin` is exported without manual wiring

```rust
use qubics::prelude::*;

#[derive(Component)]
struct Position { x: f32, y: f32 }

#[system(writes = [Position])]
fn move_things(_world: *mut c_void) {
    // ...
}
```
