use crate::network::NetworkMessage;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    prelude::*,
    widgets::{Block, Borders, List, ListItem},
};
use std::{collections::HashMap, io, time::Duration};
use tokio::sync::mpsc;

#[derive(Debug, Clone)]
pub struct Component {
    pub name: String,
    pub data: String,
}

#[derive(Debug, Clone)]
pub struct Entity {
    pub id: u32,
    pub components: HashMap<String, Component>,
    pub expanded: bool,
}

impl Default for Entity {
    fn default() -> Self {
        Self {
            id: 0,
            components: HashMap::new(),
            expanded: false,
        }
    }
}

#[derive(Debug, Default)]
pub struct UiState {
    pub logs: Vec<String>,
    pub entities: HashMap<u32, Entity>,
    pub selected_index: usize,
}

pub fn setup_terminal() -> Result<Terminal<CrosstermBackend<io::Stdout>>, io::Error> {
    let mut stdout = io::stdout();
    enable_raw_mode()?;
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    Terminal::new(backend)
}

pub fn restore_terminal(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
) -> Result<(), io::Error> {
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;
    Ok(())
}

pub async fn run_app(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    mut rx: mpsc::Receiver<NetworkMessage>,
) -> io::Result<()> {
    let mut ui_state = UiState::default();

    loop {
        terminal.draw(|f| {
            let mut items = vec![];
            let mut entity_keys: Vec<_> = ui_state.entities.keys().collect();
            entity_keys.sort();

            for key in entity_keys {
                let entity = &ui_state.entities[key];
                let prefix = if entity.expanded { "▼" } else { "▶" };
                items.push(ListItem::new(format!("{} Entity {}", prefix, entity.id)));
                if entity.expanded {
                    for component in entity.components.values() {
                        items.push(ListItem::new(format!("  └─ {}", component.data.replace("\n", "\n     "))));
                    }
                }
            }

            let list = List::new(items)
                .block(Block::default().borders(Borders::ALL).title("Components"))
                .highlight_symbol("> ");
            
            f.render_stateful_widget(list, f.area(), &mut {
                let mut state = ratatui::widgets::ListState::default();
                state.select(Some(ui_state.selected_index));
                state
            });
        })?;

        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                let mut entity_keys: Vec<_> = ui_state.entities.keys().cloned().collect();
                entity_keys.sort();

                let current_items_count = ui_state.entities.values().fold(0, |acc, e| acc + 1 + if e.expanded { e.components.len() } else { 0 });

                match key.code {
                    KeyCode::Char('q') => return Ok(()),
                    KeyCode::Down => {
                        if current_items_count > 0 {
                            ui_state.selected_index = (ui_state.selected_index + 1) % current_items_count;
                        }
                    }
                    KeyCode::Up => {
                        if current_items_count > 0 {
                            ui_state.selected_index = if ui_state.selected_index == 0 {
                                current_items_count - 1
                            } else {
                                ui_state.selected_index - 1
                            };
                        }
                    }
                    KeyCode::Enter => {
                        let mut current_index = 0;
                        for key in entity_keys {
                            if current_index == ui_state.selected_index {
                                if let Some(entity) = ui_state.entities.get_mut(&key) {
                                    entity.expanded = !entity.expanded;
                                }
                                break;
                            }
                            current_index += 1;
                            if ui_state.entities[&key].expanded {
                                current_index += ui_state.entities[&key].components.len();
                            }
                        }
                    }
                    _ => {}
                }
            }
        }

        if let Ok(msg) = rx.try_recv() {
            match msg {
                NetworkMessage::Log(log) => ui_state.logs.push(log),
                NetworkMessage::ConnectionStatus(status) => ui_state.logs.push(status),
                NetworkMessage::Handshake(handshake_info) => ui_state.logs.push(handshake_info),
                NetworkMessage::EntityUpdate {
                    entity_id,
                    component_name,
                    component_data,
                } => {
                    let entity = ui_state.entities.entry(entity_id).or_insert_with(|| Entity {
                        id: entity_id,
                        ..Default::default()
                    });
                    entity.components.insert(
                        component_name.clone(),
                        Component {
                            name: component_name,
                            data: component_data,
                        },
                    );
                }
            }
        }
    }
}
