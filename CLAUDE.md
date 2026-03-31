# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
make run          # install deps, build entrypoint, launch with hot-reload (epk watch + entrypoint)
make install      # just resolve/install packages into build/
```

**ECS tests:** `make -C ecs test` (compiles and runs scheduler_test.c)

**EPK package manager (Python):**
```bash
cd packages && pipx install -e --force .   # install the `epk` CLI
pytest                                      # run epk tests (pythonpath configured in pyproject.toml)
```

**Rust bridge sample:** `cargo build --release` inside `samples/rs-hello/`

## Architecture

Qubics is a plugin-based game engine built on an ECS (Entity Component System) core. Everything is compiled into shared libraries (`.dylib`) and loaded at runtime via `dlopen`. The entrypoint orchestrates the whole system.

### Entrypoint (`entrypoint/`)

A small C program (`main.c`) that serves as the runtime loader. It:
1. Loads the ECS library dynamically from `$QUBICS_PATH/ecs/ecs.dylib`
2. Scans the build directory for plugin `.dylib` files
3. Calls each plugin's `qubics_plugin()` export to collect ECS systems
4. Calls the backend's `run()` export to enter the main loop
5. On each frame tick, checks a `.stamp` file for changes and hot-reloads plugins if needed

### ECS Core (`ecs/`)

A C library providing the core ECS runtime, built as `ecs.dylib`:
- **World** — holds all entity data in archetype-grouped `ChunkContainer`s (SOA layout, `ENTITIES_PER_CHUNK=4`)
- **Registry** — tracks `ComponentDescriptor`s (name + stride)
- **Scheduler** — accepts `SystemDescriptor`s (function pointer + read/write archetypes), sorts them into parallel stages based on data access conflicts, and runs stages on `SCHEDULER_THREADS=4` pthreads

### Backends (`backends/`)

Backends export a `run(tick_function)` symbol — they own the main loop and call the tick function each frame.
- **metal** — macOS Metal backend (`metal.m`), creates an MTKView window and calls `tick_fn` with a `RenderContext` (device, commandQueue, mtkView) on each draw
- **contract** — the C header (`contract.h`) defining the `tick_function` / `run()` interface that all backends must implement

### Bridges (`bridges/`)

Bridges let non-C languages write plugins. They implement the plugin contract and translate between the language and the C ECS API.
- **contract** — C header defining `PluginSystems` struct and `plugin_fn` signature (`qubics_plugin(Registry*) -> PluginSystems`)
- **rs** (Rust bridge) — three crates:
  - `qubics-sys` — raw FFI bindings to ecs.h/scheduler.h (auto-generated via `build.rs`)
  - `qubics-macros` — proc macros: `#[derive(Component)]` and `#[system(reads=[...], writes=[...])]`
  - `qubics` — high-level Rust API re-exporting Component, system macro, and the `qubics_plugin` entrypoint via `inventory` for automatic system collection

### EPK Package Manager (`packages/`)

A Python CLI tool (`epk`) that manages qubics packages. Each package has a `manifest.toml` (name, version, deps). EPK handles:
- **resolve** — dependency resolution
- **lock** — lock file generation/parsing (`lock.toml`)
- **fetch** — fetching sources (file refs, git refs) or pre-built artifacts
- **build** — running `make` in package source dirs to produce artifacts
- **install** — symlinking built artifacts into the build directory
- **watch** — monitors lock file for changes and re-installs, writing a `.stamp` file to trigger entrypoint hot-reload

### Plugin Lifecycle

1. `manifest.toml` at project root declares dependencies (e.g., `ecs`, `backend-metal`, `rs-hello`)
2. `epk install` resolves, fetches, builds, and symlinks packages into `build/`
3. `epk watch` runs alongside the entrypoint, rebuilding on changes and updating `.stamp`
4. Entrypoint detects `.stamp` change → reloads all `.dylib` plugins → rebuilds scheduler → continues ticking

### Writing a Plugin (Rust example)

See `samples/rs-hello/`: create a `cdylib` crate depending on the `qubics` bridge, use `#[derive(Component)]` for data types and `#[system(writes=[...])]` for system functions. The `inventory` crate auto-registers systems — no manual wiring needed.
