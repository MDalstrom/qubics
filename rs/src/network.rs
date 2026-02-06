use flatbuffers_reflection::reflection;
use std::collections::HashMap;
use std::fmt::Write;
use tokio::io::AsyncReadExt;
use tokio::net::TcpStream;
use tokio::sync::mpsc;

#[derive(Debug, Clone)]
pub enum NetworkMessage {
    Log(String),
    EntityUpdate {
        entity_id: u32,
        component_name: String,
        component_data: String,
    },
    Handshake(String),
    ConnectionStatus(String),
}

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
}

async fn receive_message(stream: &mut TcpStream) -> Result<Vec<u8>, std::io::Error> {
    let mut size_buf = [0u8; 4];
    stream.read_exact(&mut size_buf).await?;
    let size = u32::from_le_bytes(size_buf) as usize;
    let mut buf = vec![0u8; size];
    stream.read_exact(&mut buf).await?;
    Ok(buf)
}

async fn parse_handshake(
    data: &[u8],
    tx: &mpsc::Sender<NetworkMessage>,
) -> Option<HashMap<u32, String>> {
    if let Some(batch) = root_as_batch(data).ok() {
        if let Some(messages) = batch.messages() {
            if let Some(msg) = messages
                .iter()
                .find(|msg| msg.payload_type() == MessagePayload::Handshake)
            {
                if let Some(hs) = msg.payload_as_handshake() {
                    let mut s = String::new();
                    writeln!(s, "Handshake received - Protocol v{}", hs.protocol_version())
                        .unwrap();
                    if let Some(comp_types) = hs.component_types() {
                        writeln!(s, "Registered {} component types:", comp_types.len()).unwrap();
                        let type_map = comp_types
                            .iter()
                            .filter_map(|info| {
                                let name = info.name()?.to_string();
                                let type_id = info.type_id();
                                writeln!(s, "  [{}] {}", type_id, name).unwrap();
                                Some((type_id, name))
                            })
                            .collect::<HashMap<u32, String>>();
                        tx.send(NetworkMessage::Handshake(s)).await.unwrap();
                        return Some(type_map);
                    }
                }
            }
        }
    }
    None
}

// All decode functions should be synchronous
fn decode_field_value<'data, 'schema>(
    s: &mut String,
    table: &flatbuffers::Table<'data>,
    field: &reflection::Field<'schema>,
    schema: &reflection::Schema<'schema>,
    indent: usize,
) {
    let voffset = field.offset();
    let field_name = field.name();
    let indent_str = "  ".repeat(indent);

    let field_type = field.type_();
    match field_type.base_type() {
        reflection::BaseType::Float => {
            if let Some(val) = unsafe { table.get::<f32>(voffset, Some(0.0f32)) } {
                writeln!(s, "{}{}: {:.2}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::Double => {
            if let Some(val) = unsafe { table.get::<f64>(voffset, Some(0.0f64)) } {
                writeln!(s, "{}{}: {:.2}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::Int => {
            if let Some(val) = unsafe { table.get::<i32>(voffset, Some(0i32)) } {
                writeln!(s, "{}{}: {}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::UInt => {
            if let Some(val) = unsafe { table.get::<u32>(voffset, Some(0u32)) } {
                writeln!(s, "{}{}: {}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::Long => {
            if let Some(val) = unsafe { table.get::<i64>(voffset, Some(0i64)) } {
                writeln!(s, "{}{}: {}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::ULong => {
            if let Some(val) = unsafe { table.get::<u64>(voffset, Some(0u64)) } {
                writeln!(s, "{}{}: {}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::Bool => {
            if let Some(val) = unsafe { table.get::<bool>(voffset, Some(false)) } {
                writeln!(s, "{}{}: {}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::Vector => {
            decode_vector_field(s, table, field, schema, indent);
        }
        reflection::BaseType::Obj => {
            decode_object_field(s, table, field, schema, indent);
        }
        _ => {
            writeln!(s, "{}{}: <unsupported type>", indent_str, field_name).unwrap();
        }
    }
}

fn decode_vector_field<'data, 'schema>(
    s: &mut String,
    table: &flatbuffers::Table<'data>,
    field: &reflection::Field<'schema>,
    schema: &reflection::Schema<'schema>,
    indent: usize,
) {
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
                let vtable = table.vtable();
                let vtable_size = vtable.num_bytes() as usize;

                if voffset as usize >= vtable_size {
                    writeln!(s, "{}{}: <field not in vtable>", indent_str, field_name).unwrap();
                    return;
                }

                let field_offset_value = vtable.get(voffset);
                if field_offset_value == 0 {
                    writeln!(s, "{}{}: 0 items", indent_str, field_name).unwrap();
                    return;
                }

                // Read the UOffset to the vector. It's a relative offset.
                let buf = table.buf();
                let uoffset_loc = table.loc() + field_offset_value as usize;

                if uoffset_loc + 4 > buf.len() {
                    writeln!(s, "{}{}: <offset out of bounds>", indent_str, field_name).unwrap();
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
                    writeln!(s, "{}{}: <vector data out of bounds>", indent_str, field_name).unwrap();
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

                writeln!(
                    s,
                    "{} {} : {} items (DEBUG: vec_data_start={}, uoffset={}, uoffset_loc={}, bytes=[{},{},{},{}])",
                    indent_str,
                    field_name,
                    vec_len,
                    vec_data_start,
                    uoffset,
                    uoffset_loc,
                    buf[vec_data_start],
                    buf[vec_data_start + 1],
                    buf[vec_data_start + 2],
                    buf[vec_data_start + 3]
                ).unwrap();

                // The actual vector elements start at vec_data_start + 4
                let elements_start = vec_data_start + 4;

                for i in 0..vec_len {
                    writeln!(s, "{}   [{}]", indent_str, i).unwrap();
                    let item_offset = elements_start + i * struct_size;

                    if item_offset + struct_size > buf.len() {
                        writeln!(s, "{}     <out of bounds>", indent_str).unwrap();
                        continue;
                    }

                    for struct_field in obj_def.fields() {
                        decode_struct_field(s, buf, item_offset, &struct_field, indent + 2);
                    }
                }
            }
        }
        _ => {
            writeln!(s, "{}{}: <vector of scalars>", indent_str, field_name).unwrap();
        }
    }
}


fn decode_struct_field<'schema>(
    s: &mut String,
    buf: &[u8],
    base_offset: usize,
    field: &reflection::Field<'schema>,
    indent: usize,
) {
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
                writeln!(s, "{}{}: {:.2}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::Double => {
            if offset + 8 <= buf.len() {
                let bytes = [
                    buf[offset],
                    buf[offset + 1],
                    buf[offset + 2],
                    buf[offset + 3],
                    buf[offset + 4],
                    buf[offset + 5],
                    buf[offset + 6],
                    buf[offset + 7],
                ];
                let val = f64::from_le_bytes(bytes);
                writeln!(s, "{}{}: {:.2}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::Int => {
            if offset + 4 <= buf.len() {
                let bytes = [buf[offset], buf[offset + 1], buf[offset + 2], buf[offset + 3]];
                let val = i32::from_le_bytes(bytes);
                writeln!(s, "{}{}: {}", indent_str, field_name, val).unwrap();
            }
        }
        reflection::BaseType::UInt => {
            if offset + 4 <= buf.len() {
                let bytes = [buf[offset], buf[offset + 1], buf[offset + 2], buf[offset + 3]];
                let val = u32::from_le_bytes(bytes);
                writeln!(s, "{}{}: {}", indent_str, field_name, val).unwrap();
            }
        }
        _ => {} // Ignore other types for now
    }
}

fn decode_object_field<'data, 'schema>(
    s: &mut String,
    table: &flatbuffers::Table<'data>,
    field: &reflection::Field<'schema>,
    schema: &reflection::Schema<'schema>,
    indent: usize,
) {
    let voffset = field.offset();
    let field_name = field.name();
    let indent_str = "  ".repeat(indent);

    let field_type = field.type_();
    if let Some(nested_table) =
        unsafe { table.get::<flatbuffers::ForwardsUOffset<flatbuffers::Table>>(voffset, None) }
    {
        let obj_def = schema.objects().get(field_type.index() as usize);
        writeln!(s, "{}{}:", indent_str, field_name).unwrap();
        decode_table_recursive(s, &nested_table, &obj_def, schema, indent + 1);
    }
}

fn decode_table_recursive<'data, 'schema>(
    s: &mut String,
    table: &flatbuffers::Table<'data>,
    obj_def: &reflection::Object<'schema>,
    schema: &reflection::Schema<'schema>,
    indent: usize,
) {
    for field in obj_def.fields() {
        decode_field_value(s, table, &field, schema, indent);
    }
}

fn decode_component<'data, 'schema_map_val>(
    s: &mut String,
    bytes: &'data [u8],
    comp_name: &str,
    schema_map: &'schema_map_val HashMap<String, Vec<u8>>,
) {
    writeln!(
        s,
        "  Rust received {} bytes: {:?}",
        bytes.len(),
        &bytes[..bytes.len().min(60)]
    )
    .unwrap();

    let schema_bytes = schema_map.values().find_map(|bytes_ref| { // Renamed bytes to bytes_ref to avoid confusion
        reflection::root_as_schema(bytes_ref)
            .ok()
            .filter(|schema_ref| schema_ref.objects().iter().any(|obj| obj.name() == comp_name))
            .map(|_| bytes_ref.as_slice())
    });

    if let Some(schema_bytes_slice) = schema_bytes { // Renamed to bytes_slice
        if let Ok(schema) = reflection::root_as_schema(schema_bytes_slice) {
            if let Some(obj_def) = schema.objects().iter().find(|obj| obj.name() == comp_name) {
                if bytes.len() < 4 {
                    writeln!(s, "  <invalid buffer: too short, {} bytes>", bytes.len()).unwrap();
                    return;
                }

                let root_offset =
                    u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]) as usize;
                let table_loc = root_offset;

                if table_loc >= bytes.len() {
                    writeln!(
                        s,
                        "  <invalid buffer: table location {} out of bounds for {} bytes>",
                        table_loc,
                        bytes.len()
                    )
                    .unwrap();
                    return;
                }

                let table = unsafe { flatbuffers::Table::new(bytes, table_loc) };
                decode_table_recursive(s, &table, &obj_def, &schema, 1);
                return;
            }
        }
    }

    writeln!(s, "  <unknown component: {}>", comp_name).unwrap();
}

async fn process_entity_updates(
    data: &[u8],
    state: &WorldState,
    tx: &mpsc::Sender<NetworkMessage>,
) {
    if let Some(batch) = root_as_batch(data).ok() {
        if let Some(messages) = batch.messages() {
            for msg in messages {
                if msg.payload_type() == MessagePayload::EntityUpdate {
                    if let Some(update) = msg.payload_as_entity_update() {
                        let entity_id = update.entity_id();
                        if let Some(comp_updates) = update.component_updates() {
                            for comp in comp_updates {
                                let type_id = comp.type_id();
                                let comp_name = state
                                    .type_map
                                    .get(&type_id)
                                    .map(|s| s.as_str())
                                    .unwrap_or("<unknown>");
                                let mut s = String::new();
                                if let Some(data_vec) = comp.data() {
                                    decode_component(
                                        &mut s,
                                        data_vec.bytes(),
                                        comp_name,
                                        &state.schema_map,
                                    );
                                } else {
                                    writeln!(s, "  <no data>").unwrap();
                                }
                                tx.send(NetworkMessage::EntityUpdate {
                                    entity_id: entity_id as u32,
                                    component_name: comp_name.to_string(),
                                    component_data: s,
                                })
                                .await
                                .unwrap();
                            }
                        }
                    }
                }
            }
        }
    }
}

async fn process_message(
    data: Vec<u8>,
    state: WorldState,
    tx: &mpsc::Sender<NetworkMessage>,
) -> WorldState {
    if data.is_empty() {
        return state;
    }

    if !state.handshake_done {
        if let Some(type_map) = parse_handshake(&data, tx).await {
            return WorldState {
                type_map,
                schema_map: state.schema_map,
                handshake_done: true,
            };
        }
    } else {
        process_entity_updates(&data, &state, tx).await;
    }
    state
}

pub async fn connection_loop(
    address: &str,
    schema_map: HashMap<String, Vec<u8>>,
    tx: mpsc::Sender<NetworkMessage>,
) {
    let mut state = WorldState::new(schema_map.clone());

    loop {
        tx.send(NetworkMessage::ConnectionStatus(format!("Connecting to {}...", address))).await.unwrap();
        match TcpStream::connect(address).await {
            Ok(mut stream) => {
                tx.send(NetworkMessage::ConnectionStatus("Connected!\n".to_string())).await.unwrap();
                loop {
                    match receive_message(&mut stream).await {
                        Ok(data) => {
                            state = process_message(data, state.clone(), &tx).await;
                        }
                        Err(_) => {
                            tx.send(NetworkMessage::ConnectionStatus("Connection lost, reconnecting...\n".to_string()))
                                .await
                                .unwrap();
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
