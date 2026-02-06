mod tui;
mod network;
mod schema;

use std::io;
use tokio::sync::mpsc;
use schema::read_schema_files;

#[tokio::main]
async fn main() -> io::Result<()> {
    let (tx, rx) = mpsc::channel(100);
    let schema_map = read_schema_files("./build/bfbs")?;

    q_generated::
    
    tokio::spawn(async move {
        network::connection_loop("127.0.0.1:8080", schema_map, tx).await;
    });

    let mut terminal = tui::setup_terminal()?;
    tui::run_app(&mut terminal, rx).await?;
    tui::restore_terminal(&mut terminal)?;

    Ok(())
}

