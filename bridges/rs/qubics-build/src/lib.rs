use std::path::PathBuf;
use std::process::Command;

pub fn generate(deps: &[&str]) {
    let out_dir = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    let deps_dir = out_dir.join("epk-deps");
    let lock_file = out_dir.join("epk-lock.toml");

    let deps_toml = deps
        .iter()
        .map(|d| format!("  \"{d}\""))
        .collect::<Vec<_>>()
        .join(",\n");

    let build_manifest = out_dir.join("manifest.toml");
    std::fs::write(
        &build_manifest,
        format!("name = \"build\"\nversion = \"0.0.1\"\ndeps = [\n{deps_toml}\n]\n"),
    )
    .expect("failed to write synthesized manifest.toml");

    let status = Command::new("epk")
        .args([
            "install",
            &format!("--manifest={}", build_manifest.display()),
            &format!("--build-dir={}", deps_dir.display()),
            &format!("--lock-file={}", lock_file.display()),
        ])
        .status()
        .expect("failed to run epk — is it installed?");

    assert!(status.success(), "epk install failed");

    let mut builder = bindgen::Builder::default();
    let mut found_headers = false;

    for pkg_entry in std::fs::read_dir(&deps_dir).expect("failed to read epk-deps dir") {
        let pkg_dir = pkg_entry.expect("failed to read entry").path();
        if !pkg_dir.is_dir() {
            continue;
        }
        for entry in std::fs::read_dir(&pkg_dir).expect("failed to read package dir") {
            let path = entry.expect("failed to read entry").path();
            if path.extension().and_then(|e| e.to_str()) == Some("h") {
                println!("cargo:rerun-if-changed={}", path.display());
                builder = builder.header(path.to_str().unwrap().to_string());
                found_headers = true;
            }
        }
    }

    assert!(found_headers, "no .h files found under {}", deps_dir.display());

    for dep in deps {
        let dep_escaped = regex::escape(
            &deps_dir.join(dep).to_str().unwrap().replace('\\', "/"),
        );
        builder = builder.allowlist_file(format!("{dep_escaped}/.*\\.h"));
    }

    builder
        .clang_arg(format!("-I{}", deps_dir.display()))
        .generate()
        .expect("bindgen failed")
        .write_to_file(out_dir.join("bindings.rs"))
        .expect("failed to write bindings");

    let pkg_name = std::env::var("CARGO_PKG_NAME").unwrap();
    let pkg_version = std::env::var("CARGO_PKG_VERSION").unwrap();
    let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    std::fs::write(
        manifest_dir.join("manifest.toml"),
        format!("name = \"{pkg_name}\"\nversion = \"{pkg_version}\"\ndeps = [\n{deps_toml}\n]\n"),
    )
    .expect("failed to write package manifest.toml");
}
