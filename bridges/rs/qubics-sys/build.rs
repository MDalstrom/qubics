use std::path::PathBuf;
use std::process::Command;

fn main() {
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    let out_dir = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    let deps_dir = out_dir.join("epk-deps");
    let lock_file = out_dir.join("epk-lock.toml");
    let manifest = format!("{manifest_dir}/manifest.toml");

    let status = Command::new("epk")
        .args([
            "install",
            &format!("--manifest={manifest}"),
            &format!("--build-dir={}", deps_dir.display()),
            &format!("--lock-file={}", lock_file.display()),
        ])
        .status()
        .expect("failed to run epk — is it installed?");

    assert!(status.success(), "epk install failed");

    bindgen::Builder::default()
        .header(format!("{}/ecs/ecs.h", deps_dir.display()))
        .header(format!("{}/bridge-contracts/contract.h", deps_dir.display()))
        .clang_arg(format!("-I{}", deps_dir.display()))
        .allowlist_type("Registry")
        .allowlist_type("World")
        .allowlist_type("Archetype")
        .allowlist_type("ComponentDescriptor")
        .allowlist_type("Chunk")
        .allowlist_type("ChunkContainer")
        .allowlist_type("Entity")
        .allowlist_type("SystemDescriptor")
        .allowlist_type("SystemFn")
        .allowlist_type("PluginSystems")
        .generate()
        .expect("bindgen failed")
        .write_to_file(out_dir.join("bindings.rs"))
        .expect("failed to write bindings");

    println!("cargo:rerun-if-changed={manifest}");
}
