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
use std::io;
use crossterm::event::{self, Event, KeyCode};
use world_state::WorldState;

#[allow(dead_code, unused_imports, non_snake_case, clippy::all)]
mod network_generated {
    include!(concat!(env!("OUT_DIR"), "/components_generated.rs"));
}

use network_generated::network::{root_as_batch, MessagePayload};

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

fn render(frame: &mut Frame, state: &WorldState) {
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
    
    let mut items: Vec<ListItem> = state.components.values()
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
                    text.push_str("\n  Data:");
                    let num_floats_to_show = (data.len() / 4).min(6);
                    for i in 0..num_floats_to_show {
                        let start = i * 4;
                        let end = start + 4;
                        if data.len() >= end {
                            let mut float_bytes = [0u8; 4];
                            float_bytes.copy_from_slice(&data[start..end]);
                            text.push_str(&format!(" {:.2}", f32::from_le_bytes(float_bytes)));
                        }
                    }
                    if data.len() > 24 {
                        text.push_str(" ...");
                    }
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
    
    loop {
        while let Ok(buf) = rx.try_recv() {
            if !buf.is_empty() {
                state = decode_message(&buf, state);
            } else {
                state = state.set_connected(true);
            }
        }
        
        terminal.draw(|frame| render(frame, &state))?;
        
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
