use std::process::Command;
use std::env;
use std::path::PathBuf;
use std::fs;

fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();
    let out_path = PathBuf::from(&out_dir);

    let network_schema = "../schemas/network.fbs";
    println!("cargo:rerun-if-changed={}", network_schema);

    let status = Command::new("flatc")
        .arg("--rust")
        .arg("-o")
        .arg(&out_path)
        .arg(network_schema)
        .status()
        .expect("Failed to execute flatc");

    if !status.success() {
        panic!("flatc command failed");
    }

    let generated_file = out_path.join("network_generated.rs");
    let dest_path = out_path.join("components_generated.rs");
    
    fs::copy(generated_file, dest_path).expect("Failed to copy generated file");
}
