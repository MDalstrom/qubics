---
name: new-plugin
description: Create a new Rust plugin for qubics. Use when asked to create/scaffold a new plugin, package, or system.
argument-hint: <plugin-name>
---

Create a new qubics Rust plugin named `$ARGUMENTS`.

## Steps

### 1. Scaffold the Cargo project

Create the directory at the project root under a location the user specifies (default: `plugins/$ARGUMENTS/`).

Create the following files:

**`Cargo.toml`**
```toml
[package]
name = "$ARGUMENTS"
version = "0.1.0"
edition = "2021"

[lib]
name = "$ARGUMENTS"       # use underscores for the lib name (replace hyphens)
crate-type = ["cdylib"]

[dependencies]
qubics = { path = "../../bridges/rs/qubics" }
```

Adjust the relative `path` to `bridges/rs/qubics` based on actual directory depth.

**`manifest.toml`** (epk package manifest)
```toml
name = "$ARGUMENTS"
version = "0.1.0"
deps = []
```

**`Makefile`**
```makefile
ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

$(BUILD_DIR)/$ARGUMENTS.dylib: src/lib.rs Cargo.toml
	cargo build --release
	cp target/release/lib<LIB_NAME>.dylib $(BUILD_DIR)
```

Replace `<LIB_NAME>` with the lib name from Cargo.toml (hyphens become underscores).

**`src/lib.rs`** — starter plugin with one component and one system:
```rust
use qubics::prelude::*;

#[derive(Component)]
struct ExampleComponent {
    value: f32,
}

#[system(writes = [ExampleComponent])]
fn example_system(_world: *mut c_void) {
    // TODO: implement
}
```

### 2. Register with epk

Add the plugin name to the `deps` array in the **root `manifest.toml`**.

### 3. Register with epk local registry

Run: `epk add <path-to-plugin-dir>`

This registers the plugin source in the local registry so `epk install` can find it.

### 4. Verify

Run `cargo build --release` inside the plugin directory to confirm it compiles.

## Key conventions

- Crate type MUST be `cdylib` — the engine loads plugins as `.dylib` shared libraries via `dlopen`
- Systems are auto-registered via the `inventory` crate — no manual wiring needed, just use `#[system(...)]`
- Every component type needs `#[derive(Component)]` which generates a static `ComponentDescriptor`
- The `#[system]` attribute takes `reads = [...]` and `writes = [...]` listing component types the system accesses — the scheduler uses these to determine which systems can run in parallel
- System functions take `(_world: *mut c_void)` as their signature
- The plugin exports `qubics_plugin` automatically through the `qubics` crate — do not define it manually
