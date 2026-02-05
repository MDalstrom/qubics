mod generated;
mod schema;

pub use generated::*;

use std::collections::HashMap;
use tokio::net::TcpStream;
use tokio::io::AsyncReadExt;
use crate::generated::network_generated::network::{root_as_batch, MessagePayload};
use crate::schema::{read_schema_files, extract_objects};
use flatbuffers_reflection::reflection;

#[derive(Debug, Clone)]
struct WorldState {
    type_map: HashMap<u32, String>,
    schema_map: HashMap<String, Vec<u8>>,
    handshake_done: bool,
}

impl WorldState {
    fn new(schema_map: HashMap<String, Vec<u8>>) -> Self {
        Self {
            type_map: HashMap::new(),
            schema_map,
            handshake_done: false,
        }
    }

    fn with_handshake(self, type_map: HashMap<u32, String>) -> Self {
        Self {
            type_map,
            schema_map: self.schema_map,
            handshake_done: true,
        }
    }
}

async fn receive_message(stream: &mut TcpStream) -> Result<Vec<u8>, std::io::Error> {
    let mut size_buf = [0u8; 4];
    stream.read_exact(&mut size_buf).await?;

    let size = u32::from_le_bytes(size_buf) as usize;

    let mut buf = vec![0u8; size];
    stream.read_exact(&mut buf).await?;

    Ok(buf)
}

fn parse_handshake(data: &[u8]) -> Option<HashMap<u32, String>> {
    root_as_batch(data).ok()
        .and_then(|batch| batch.messages())
        .and_then(|messages| {
            messages.iter()
                .find(|msg| msg.payload_type() == MessagePayload::Handshake)
                .and_then(|msg| msg.payload_as_handshake())
                .map(|hs| {
                    println!("Handshake received - Protocol v{}", hs.protocol_version());
                    
                    hs.component_types()
                        .map(|comp_types| {
                            println!("Registered {} component types:", comp_types.len());
                            comp_types.iter()
                                .filter_map(|info| {
                                    let name = info.name()?.to_string();
                                    let type_id = info.type_id();
                                    println!("  [{}] {}", type_id, name);
                                    Some((type_id, name))
                                })
                                .collect::<HashMap<u32, String>>()
                        })
                        .unwrap_or_default()
                })
        })
}

fn decode_field_value(table: &flatbuffers::Table, field: &reflection::Field, schema: &reflection::Schema, indent: usize) {
    let voffset = field.offset();
    let field_name = field.name();
    let indent_str = "  ".repeat(indent);
    
    let field_type = field.type_();
    match field_type.base_type() {
        reflection::BaseType::Float => {
            if let Some(val) = unsafe { table.get::<f32>(voffset, Some(0.0f32)) } {
                println!("{}{}: {:.2}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::Double => {
            if let Some(val) = unsafe { table.get::<f64>(voffset, Some(0.0f64)) } {
                println!("{}{}: {:.2}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::Int => {
            if let Some(val) = unsafe { table.get::<i32>(voffset, Some(0i32)) } {
                println!("{}{}: {}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::UInt => {
            if let Some(val) = unsafe { table.get::<u32>(voffset, Some(0u32)) } {
                println!("{}{}: {}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::Long => {
            if let Some(val) = unsafe { table.get::<i64>(voffset, Some(0i64)) } {
                println!("{}{}: {}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::ULong => {
            if let Some(val) = unsafe { table.get::<u64>(voffset, Some(0u64)) } {
                println!("{}{}: {}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::Bool => {
            if let Some(val) = unsafe { table.get::<bool>(voffset, Some(false)) } {
                println!("{}{}: {}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::Vector => {
            decode_vector_field(table, field, schema, indent);
        }
        reflection::BaseType::Obj => {
            decode_object_field(table, field, schema, indent);
        }
        _ => {
            println!("{}{}: <unsupported type>", indent_str, field_name);
        }
    }
}

fn decode_vector_field(table: &flatbuffers::Table, field: &reflection::Field, schema: &reflection::Schema, indent: usize) {
    let voffset = field.offset();
    let field_name = field.name();
    let indent_str = "  ".repeat(indent);
    
    let field_type = field.type_();
    let element_type = field_type.element();
    
    match element_type {
        reflection::BaseType::Obj => {
            let obj_def = schema.objects().get(field_type.index() as usize);
            if obj_def.is_struct() {
                // Read vector of structs manually
                // 1. Get the offset to the vector from vtable
                let vtable = unsafe { table.vtable() };
                let vtable_size = vtable.num_bytes() as usize;
                
                if voffset as usize >= vtable_size {
                    println!("{}{}: <field not in vtable>", indent_str, field_name);
                    return;
                }
                
                let field_offset_value = vtable.get(voffset);
                if field_offset_value == 0 {
                    println!("{}{}: 0 items", indent_str, field_name);
                    return;
                }
                
                // 2. Read the UOffset to the vector. It's a relative offset.
                let buf = table.buf();
                let uoffset_loc = table.loc() + field_offset_value as usize;
                
                if uoffset_loc + 4 > buf.len() {
                    println!("{}{}: <offset out of bounds>", indent_str, field_name);
                    return;
                }
                
                let uoffset = u32::from_le_bytes([
                    buf[uoffset_loc],
                    buf[uoffset_loc + 1],
                    buf[uoffset_loc + 2],
                    buf[uoffset_loc + 3],
                ]) as usize;
                
                // The vector data starts at uoffset_loc + uoffset
                let vec_data_start = uoffset_loc + uoffset;
                
                if vec_data_start + 4 > buf.len() {
                    println!("{}{}: <vector data out of bounds>", indent_str, field_name);
                    return;
                }
                
                // First 4 bytes at vec_data_start is the vector LENGTH (number of elements)
                let vec_len = u32::from_le_bytes([
                    buf[vec_data_start],
                    buf[vec_data_start + 1],
                    buf[vec_data_start + 2],
                    buf[vec_data_start + 3],
                ]) as usize;
                
                let struct_size = obj_def.bytesize() as usize;
                
                println!("{}{}: {} items (DEBUG: vec_data_start={}, uoffset={}, uoffset_loc={}, bytes=[{},{},{},{}])", 
                    indent_str, field_name, vec_len, vec_data_start, uoffset, uoffset_loc,
                    buf[vec_data_start], buf[vec_data_start + 1], buf[vec_data_start + 2], buf[vec_data_start + 3]);
                
                // The actual vector elements start at vec_data_start + 4
                let elements_start = vec_data_start + 4;
                
                // 4. Decode each struct in the vector
                for i in 0..vec_len {
                    println!("{}  [{}]:", indent_str, i);
                    let item_offset = elements_start + i * struct_size;
                    
                    if item_offset + struct_size > buf.len() {
                        println!("{}    <out of bounds>", indent_str);
                        continue;
                    }
                    
                    // Recursively decode struct fields
                    for struct_field in obj_def.fields() {
                        decode_struct_field(buf, item_offset, &struct_field, indent + 2);
                    }
                }
            }
        }
        _ => {
            println!("{}{}: <vector of scalars>", indent_str, field_name);
        }
    }
}

fn decode_struct_field(buf: &[u8], base_offset: usize, field: &reflection::Field, indent: usize) {
    let field_offset = field.offset() as usize;
    let field_name = field.name();
    let indent_str = "  ".repeat(indent);
    let offset = base_offset + field_offset;
    
    let field_type = field.type_();
    match field_type.base_type() {
        reflection::BaseType::Float => {
            if offset + 4 <= buf.len() {
                let bytes = [buf[offset], buf[offset + 1], buf[offset + 2], buf[offset + 3]];
                let val = f32::from_le_bytes(bytes);
                println!("{}{}: {:.2}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::Double => {
            if offset + 8 <= buf.len() {
                let bytes = [
                    buf[offset], buf[offset + 1], buf[offset + 2], buf[offset + 3],
                    buf[offset + 4], buf[offset + 5], buf[offset + 6], buf[offset + 7],
                ];
                let val = f64::from_le_bytes(bytes);
                println!("{}{}: {:.2}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::Int => {
            if offset + 4 <= buf.len() {
                let bytes = [buf[offset], buf[offset + 1], buf[offset + 2], buf[offset + 3]];
                let val = i32::from_le_bytes(bytes);
                println!("{}{}: {}", indent_str, field_name, val);
            }
        }
        reflection::BaseType::UInt => {
            if offset + 4 <= buf.len() {
                let bytes = [buf[offset], buf[offset + 1], buf[offset + 2], buf[offset + 3]];
                let val = u32::from_le_bytes(bytes);
                println!("{}{}: {}", indent_str, field_name, val);
            }
        }
        _ => {}
    }
}

fn decode_object_field(table: &flatbuffers::Table, field: &reflection::Field, schema: &reflection::Schema, indent: usize) {
    let voffset = field.offset();
    let field_name = field.name();
    let indent_str = "  ".repeat(indent);
    
    let field_type = field.type_();
    if let Some(nested_table) = unsafe { table.get::<flatbuffers::ForwardsUOffset<flatbuffers::Table>>(voffset, None) } {
        let obj_def = schema.objects().get(field_type.index() as usize);
        println!("{}{}:", indent_str, field_name);
        decode_table_recursive(&nested_table, &obj_def, schema, indent + 1);
    }
}

fn decode_table_recursive(table: &flatbuffers::Table, obj_def: &reflection::Object, schema: &reflection::Schema, indent: usize) {
    for field in obj_def.fields() {
        decode_field_value(table, &field, schema, indent);
    }
}

fn decode_component(bytes: &[u8], comp_name: &str, schema_map: &HashMap<String, Vec<u8>>) {
    println!("  Rust received {} bytes: {:?}", bytes.len(), &bytes[..bytes.len().min(60)]);
    
    // Find schema for this component
    let schema_bytes = schema_map.values()
        .find_map(|bytes| {
            reflection::root_as_schema(bytes).ok()
                .filter(|schema| {
                    schema.objects().iter().any(|obj| obj.name() == comp_name)
                })
                .map(|_| bytes.as_slice())
        });
    
    if let Some(schema_bytes) = schema_bytes {
        if let Ok(schema) = reflection::root_as_schema(schema_bytes) {
            if let Some(obj_def) = schema.objects().iter().find(|obj| obj.name() == comp_name) {
                // Read the root offset from the buffer
                if bytes.len() < 4 {
                    println!("  <invalid buffer: too short, {} bytes>", bytes.len());
                    return;
                }
                
                // A flatbuffer buffer contains a u32 offset at the start, which points to the root table.
                let root_offset = u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]) as usize;
                
                // The table is located at `root_offset` from the start of the buffer.
                let table_loc = root_offset;
                
                if table_loc >= bytes.len() {
                    println!("  <invalid buffer: table location {} out of bounds for {} bytes>", table_loc, bytes.len());
                    return;
                }
                
                let table = unsafe { flatbuffers::Table::new(bytes, table_loc) };
                decode_table_recursive(&table, &obj_def, &schema, 1);
                return;
            }
        }
    }
    
    println!("  <unknown component: {}>", comp_name);
}

fn process_entity_updates(data: &[u8], type_map: &HashMap<u32, String>, schema_map: &HashMap<String, Vec<u8>>) {
    root_as_batch(data).ok()
        .and_then(|batch| batch.messages())
        .into_iter()
        .flat_map(|messages| messages.iter())
        .filter(|msg| msg.payload_type() == MessagePayload::EntityUpdate)
        .filter_map(|msg| msg.payload_as_entity_update())
        .for_each(|update| {
            let entity_id = update.entity_id();
            
            update.component_updates()
                .into_iter()
                .flat_map(|comp_updates| comp_updates.iter())
                .for_each(|comp| {
                    let type_id = comp.type_id();
                    let comp_name = type_map.get(&type_id)
                        .map(|s| s.as_str())
                        .unwrap_or("<unknown>");

                    println!("\n[Entity {}] {}", entity_id, comp_name);
                    
                    comp.data()
                        .map(|data_vec| data_vec.bytes())
                        .map(|bytes| decode_component(bytes, comp_name, schema_map))
                        .unwrap_or_else(|| println!("  <no data>"));
                });
        });
}

async fn process_message(data: Vec<u8>, state: WorldState) -> WorldState {
    if data.is_empty() {
        return state;
    }

    if !state.handshake_done {
        parse_handshake(&data)
            .map(|type_map| {
                println!();
                WorldState {
                    type_map,
                    schema_map: state.schema_map.clone(),
                    handshake_done: true,
                }
            })
            .unwrap_or(state)
    } else {
        process_entity_updates(&data, &state.type_map, &state.schema_map);
        state
    }
}

async fn connection_loop(address: &str, schema_map: HashMap<String, Vec<u8>>) {
    let mut state = WorldState::new(schema_map.clone());

    loop {
        println!("Connecting to {}...", address);
        
        match TcpStream::connect(address).await {
            Ok(mut stream) => {
                println!("Connected!\n");
                
                loop {
                    match receive_message(&mut stream).await {
                        Ok(data) => {
                            state = process_message(data, state).await;
                        }
                        Err(_) => {
                            println!("Connection lost, reconnecting...\n");
                            state = WorldState::new(schema_map.clone());
                            break;
                        }
                    }
                }
            }
            Err(_) => {
                tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
            }
        }
    }
}

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let schema_map = read_schema_files("./build/bfbs")?;
    let _objects_map = extract_objects(schema_map.clone());
    println!("Loaded schema objects\n");

    connection_loop("127.0.0.1:8080", schema_map).await;

    Ok(())
}

