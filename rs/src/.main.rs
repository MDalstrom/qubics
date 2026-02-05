mod generated;
mod world_state;

use tokio::net::TcpStream;
use tokio::io::AsyncReadExt;
use tokio::sync::mpsc;
use ratatui::{
    Frame,
    layout::{Constraint, Layout},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    style::{Color, Style},
};
use flatbuffers_reflection::reflection;
use std::io;
use crossterm::event::{self, Event, KeyCode};
use world_state::WorldState;

use crate::generated::{root_as_batch, MessagePayload};

async fn receive_message(stream: &mut TcpStream) -> Result<Vec<u8>, std::io::Error> {
    let mut size_buf = [0u8; 4];
    stream.read_exact(&mut size_buf).await?;
    
    let size = u32::from_le_bytes(size_buf) as usize;
    
    let mut buf = vec![0u8; size];
    stream.read_exact(&mut buf).await?;
    
    Ok(buf)
}

fn decode_message(data: &[u8], state: WorldState) -> WorldState {
    match root_as_batch(data) {
        Ok(batch) => {
            if let Some(messages) = batch.messages() {
                return messages.iter().fold(state, |acc_state, msg| {
                    match msg.payload_type() {
                        MessagePayload::Handshake => {
                            if let Some(hs) = msg.payload_as_handshake() {
                                let protocol_version = hs.protocol_version();
                                let mut types = Vec::new();
                                
                                if let Some(comp_types) = hs.component_types() {
                                    for info in comp_types.iter() {
                                        types.push((
                                            info.type_id(),
                                            info.name().unwrap_or("<unnamed>").to_string(),
                                            info.schema_hash(),
                                        ));
                                    }
                                }
                                
                                acc_state.register_handshake(protocol_version, types)
                            } else {
                                acc_state
                            }
                        }
                        MessagePayload::EntityUpdate => {
                            if let Some(update) = msg.payload_as_entity_update() {
                                let _entity_id = update.entity_id();
                                let mut updates = Vec::new();
                                
                                if let Some(comp_updates) = update.component_updates() {
                                    for comp in comp_updates.iter() {
                                        let data = comp.data().map(|d| d.bytes().to_vec());
                                        updates.push((comp.type_id(), data));
                                    }
                                }
                                
                                acc_state.apply_update(updates)
                            } else {
                                acc_state
                            }
                        }
                        _ => acc_state,
                    }
                });
            }
            state
        }
        Err(e) => {
            state.set_message(format!("Decode error: {:?}", e))
        }
    }
}

async fn network_task(tx: mpsc::UnboundedSender<Vec<u8>>) {
    loop {
        match TcpStream::connect("127.0.0.1:8080").await {
            Ok(mut stream) => {
                while let Ok(buf) = receive_message(&mut stream).await {
                    if tx.send(buf).is_err() {
                        break;
                    }
                }
            }
            Err(_e) => {
            }
        }
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
    }
}

fn format_table_recursive<'a>(table: &flatbuffers::Table<'a>, table_def: &reflection::Object<'a>, schema: &reflection::Schema<'a>, indent: usize) -> String {
    let mut s = String::new();
    let indent_str = "  ".repeat(indent);

    for field in table_def.fields().unwrap() {
        let field_name = field.name().unwrap();
        let voffset = field.offset();
        
        if table.get_field(voffset, false) {
            s.push_str(&format!("\n{}{}: ", indent_str, field_name));
            let field_type = field.type_().unwrap();
            match field_type.base_type() {
                reflection::BaseType::Obj => {
                    if let Some(nested_table) = table.get_table(voffset) {
                        let nested_table_def = &schema.objects().unwrap().get(field_type.index() as usize);
                        s.push_str(&format_table_recursive(&nested_table, nested_table_def, schema, indent + 1));
                    } else {
                        s.push_str("<null>");
                    }
                }
                reflection::BaseType::Vector => {
                    let vec_type = field_type.element();
                    match vec_type {
                        reflection::BaseType::Obj => {
                            let struct_def = &schema.objects().unwrap().get(field_type.index() as usize);
                            if struct_def.is_struct() {
                                if let Some(vector) = table.get_vector_of_bytes(voffset) {
                                    let struct_size = struct_def.bytesize() as usize;
                                    s.push_str(&format!("({} items)", vector.len() / struct_size));
                                    for (i, chunk) in vector.chunks(struct_size).enumerate() {
                                        s.push_str(&format!("\n{}  {}:", &indent_str, i));
                                        for struct_field in struct_def.fields().unwrap() {
                                            let name = struct_field.name().unwrap();
                                            let offset = struct_field.offset() as usize;
                                            let val_str = match struct_field.type_().unwrap().base_type() {
                                                reflection::BaseType::Float => {
                                                    let mut b = [0u8; 4];
                                                    b.copy_from_slice(&chunk[offset..offset+4]);
                                                    format!("{:.2}", f32::from_le_bytes(b))
                                                },
                                                _ => "<unsupported>".to_string()
                                            };
                                            s.push_str(&format!(" {}: {}", name, val_str));
                                        }
                                    }
                                }
                            } else {
                                s.push_str("<vector of tables unsupported>");
                            }
                        }
                        _ => {
                            s.push_str("<vector of scalars unsupported>");
                        }
                    }
                }
                reflection::BaseType::String => {
                    if let Some(str_val) = table.get_string(voffset) {
                        s.push_str(str_val);
                    } else {
                        s.push_str("<null_string>");
                    }
                }
                reflection::BaseType::Float => s.push_str(&format!("{:.2}", table.get(voffset, 0.0f32).unwrap())),
                reflection::BaseType::Double => s.push_str(&format!("{:.2}", table.get(voffset, 0.0f64).unwrap())),
                reflection::BaseType::Int => s.push_str(&format!("{}", table.get(voffset, 0i32).unwrap())),
                reflection::BaseType::UInt => s.push_str(&format!("{}", table.get(voffset, 0u32).unwrap())),
                reflection::BaseType::Long => s.push_str(&format!("{}", table.get(voffset, 0i64).unwrap())),
                reflection::BaseType::ULong => s.push_str(&format!("{}", table.get(voffset, 0u64).unwrap())),
                reflection::BaseType::Short => s.push_str(&format!("{}", table.get(voffset, 0i16).unwrap())),
                reflection::BaseType::UShort => s.push_str(&format!("{}", table.get(voffset, 0u16).unwrap())),
                reflection::BaseType::Byte => s.push_str(&format!("{}", table.get(voffset, 0i8).unwrap())),
                reflection::BaseType::UByte => s.push_str(&format!("{}", table.get(voffset, 0u8).unwrap())),
                reflection::BaseType::Bool => s.push_str(&format!("{}", table.get(voffset, false).unwrap())),
                _ => s.push_str("<unsupported>"),
            }
        }
    }
    s
}

fn render_component_data<'a>(data: &'a [u8], component_name: &str, schema: &reflection::Schema<'a>) -> String {
    let table_def = match schema.objects().unwrap().iter().find(|o| o.name().unwrap() == component_name) {
        Some(t) => t,
        None => return "\n  <Component not in schema>".to_string(),
    };

    if table_def.is_struct() {
        return "\n  <Struct roots unsupported>".to_string();
    }

    let root_table = match flatbuffers::root::<flatbuffers::Table>(data) {
        Ok(t) => t,
        Err(_) => return "\n  <Failed to parse as Flatbuffer table>".to_string(),
    };
    
    let mut s = format!("\n  {}:", component_name);
    s.push_str(&format_table_recursive(&root_table, &table_def, schema, 1));
    s
}

fn render(frame: &mut Frame, state: &WorldState, schema: &reflection::Schema) {
    let chunks = Layout::vertical([
        Constraint::Length(4),
        Constraint::Min(0),
        Constraint::Length(4),
        Constraint::Length(4),
    ]).split(frame.area());
    
    let header = Paragraph::new(format!(
        "ECS Inspector | Protocol v{} | {} components | {} total entities | {} with data | {}",
        state.protocol_version,
        state.components.len(),
        state.total_entities(),
        state.components_with_entities(),
        if state.connected { "Connected" } else { "Disconnected" }
    ))
    .block(Block::default().borders(Borders::ALL).title("Status"))
    .style(Style::default().fg(if state.connected { Color::Green } else { Color::Red }));
    frame.render_widget(header, chunks[0]);
    
    let items: Vec<ListItem> = state.components.values()
        .map(|c| {
            let style = if c.entity_count > 0 {
                Style::default().fg(Color::Green)
            } else {
                Style::default().fg(Color::Gray)
            };

            let mut text = format!(
                "[{}] {} | {} entities | {} bytes | hash: {:016x}",
                c.type_id, c.name, c.entity_count, c.last_data_size, c.schema_hash
            );

            if let Some(data) = &c.data {
                if !data.is_empty() {
                    text.push_str(&render_component_data(data, &c.name, schema));
                }
            }
            
            ListItem::new(text).style(style)
        })
        .collect();
    
    if items.is_empty() {
        items.push(ListItem::new("No components registered yet...").style(Style::default().fg(Color::Yellow)));
    }
    
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Components"));
    frame.render_widget(list, chunks[1]);
    
    let debug = Paragraph::new(state.debug_info.clone())
        .block(Block::default().borders(Borders::ALL).title("Debug"))
        .style(Style::default().fg(Color::Cyan));
    frame.render_widget(debug, chunks[2]);
    
    let footer = Paragraph::new(format!(
        "{} | Msg #{} | Press 'q' to quit",
        state.last_message,
        state.message_count
    ))
    .block(Block::default().borders(Borders::ALL).title("Last Message"));
    frame.render_widget(footer, chunks[3]);
}

#[tokio::main]
async fn main() -> io::Result<()> {
    let (tx, mut rx) = mpsc::unbounded_channel();
    
    tokio::spawn(async move {
        network_task(tx).await;
    });
    
    let mut terminal = ratatui::init();
    terminal.clear()?;
    
    let mut state = WorldState::new().set_message("Connecting to server...".to_string());
    
    let schema_bytes = include_bytes!(concat!(env!("OUT_DIR"), "/all.bfbs"));
    let schema = reflection::root_as_schema(schema_bytes).unwrap();
    
    loop {
        while let Ok(buf) = rx.try_recv() {
            if !buf.is_empty() {
                state = decode_message(&buf, state);
            } else {
                state = state.set_connected(true);
            }
        }
        
        terminal.draw(|frame| render(frame, &state, &schema))?;
        
        if event::poll(std::time::Duration::from_millis(16))? {
            if let Event::Key(key) = event::read()? {
                if key.code == KeyCode::Char('q') {
                    break;
                }
            }
        }
    }
    
    ratatui::restore();
    Ok(())
}
