use std::collections::HashMap;
use std::fs;
use flatbuffers_reflection::reflection::root_as_schema;

pub fn read_schema_files(dir_path: &str) -> std::io::Result<HashMap<String, Vec<u8>>> {
    let mut schema_map = HashMap::new();

    for entry in fs::read_dir(dir_path)? {
        let entry = entry?;
        let path = entry.path();

        if path.is_file() {
            if let Ok(bytes) = fs::read(&path) {
                if let Some(file_name) = path.file_name() {
                    if let Some(name_str) = file_name.to_str() {
                        schema_map.insert(name_str.to_string(), bytes);
                    }
                }
            }
        }
    }

    Ok(schema_map)
}

pub fn extract_objects(schema_map: HashMap<String, Vec<u8>>) -> HashMap<String, String> {
    let mut objects_map = HashMap::new();

    for (file_name, bytes) in schema_map {
        if let Ok(schema) = root_as_schema(&bytes) {
            let objects = schema.objects();
            for object in objects {
                let obj_name = object.name();
                objects_map.insert(obj_name.to_string(), file_name.clone());
            }
        }
    }

    objects_map
}
