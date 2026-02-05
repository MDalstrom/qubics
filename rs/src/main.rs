mod generated;
mod network;
mod schema;
mod tui;

pub use generated::*; // Re-adding this line

use crate::schema::read_schema_files;
use std::io;
use tokio::sync::mpsc;

#[tokio::main]
async fn main() -> io::Result<()> {
    let (tx, rx) = mpsc::channel(100);
    let schema_map = read_schema_files("./build/bfbs")?;

    tokio::spawn(async move {
        network::connection_loop("127.0.0.1:8080", schema_map, tx).await;
    });

    let mut terminal = tui::setup_terminal()?;
    tui::run_app(&mut terminal, rx).await?;
    tui::restore_terminal(&mut terminal)?;

    Ok(())
}

