use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct ComponentInfo {
    pub type_id: u32,
    pub name: String,
    pub schema_hash: u64,
    pub entity_count: usize,
    pub last_data_size: usize,
    pub data: Option<Vec<u8>>,
}

#[derive(Clone, Debug)]
pub struct WorldState {
    pub components: HashMap<u32, ComponentInfo>,
    pub protocol_version: u32,
    pub connected: bool,
    pub last_message: String,
    pub debug_info: String,
    pub message_count: u64,
}

impl WorldState {
    pub fn new() -> Self {
        WorldState {
            components: HashMap::new(),
            protocol_version: 0,
            connected: false,
            last_message: "Starting...".to_string(),
            debug_info: String::new(),
            message_count: 0,
        }
    }
    
    pub fn set_connected(mut self, connected: bool) -> Self {
        self.connected = connected;
        self
    }
    
    pub fn set_message(mut self, msg: String) -> Self {
        self.last_message = msg;
        self.message_count += 1;
        self
    }
    
    pub fn register_handshake(mut self, protocol_version: u32, types: Vec<(u32, String, u64)>) -> Self {
        self.protocol_version = protocol_version;
        for (type_id, name, hash) in types {
            self.components.insert(type_id, ComponentInfo {
                type_id,
                name,
                schema_hash: hash,
                entity_count: 0,
                last_data_size: 0,
                data: None,
            });
        }
        let msg = format!("Handshake: {} components registered", self.components.len());
        self.debug_info = format!("IDs: {:?}", self.components.keys().collect::<Vec<_>>());
        self.last_message = msg;
        self.message_count += 1;
        self
    }
    
    pub fn apply_update(mut self, updates: Vec<(u32, Option<Vec<u8>>)>) -> Self {
        let update_count = updates.len();
        let mut debug_lines = vec![format!("Reg: {} types", self.components.len())];
        
        for (type_id, data) in updates {
            if let Some(info) = self.components.get_mut(&type_id) {
                let data_size = data.as_ref().map_or(0, |d| d.len());
                let old_count = info.entity_count;
                info.last_data_size = data_size;
                info.entity_count = if data_size > 0 { data_size / 12 } else { 0 };
                info.data = data;
                debug_lines.push(format!("[{}]: {}→{}", type_id, old_count, info.entity_count));
            } else {
                debug_lines.push(format!("[{}]: NOT FOUND", type_id));
            }
        }
        
        self.debug_info = debug_lines.join(" ");
        let total = self.total_entities();
        let msg = format!("Updated {} components, {} total entities", update_count, total);
        self.last_message = msg;
        self.message_count += 1;
        self
    }
    
    pub fn total_entities(&self) -> usize {
        self.components.values().map(|c| c.entity_count).sum()
    }
    
    pub fn components_with_entities(&self) -> usize {
        self.components.values().filter(|c| c.entity_count > 0).count()
    }
}

impl Default for WorldState {
    fn default() -> Self {
        Self::new()
    }
}
