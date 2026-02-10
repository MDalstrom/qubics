import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Static, Label
from textual.reactive import reactive
from textual.containers import Container
from q_ecs.types import World


class EcsInspectorApp(App):
    CSS = """
    Screen {
        background: $surface;
    }
    #tree-view {
        width: 100%;
        height: 1fr;
        border: solid $primary;
    }
    #info-bar {
        height: 3;
        background: $panel;
        border: solid $primary;
    }
    """
    
    BINDINGS = [("q", "quit", "Quit")]
    
    world_info = reactive("")
    
    def __init__(self, tick_fn=None):
        super().__init__()
        self.tick_fn = tick_fn
        self.tick_task = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="tree-view"):
            yield Tree("ECS World")
        with Container(id="info-bar"):
            yield Label(self.world_info)
        yield Footer()
    
    async def on_mount(self) -> None:
        if self.tick_fn:
            self.tick_task = asyncio.create_task(self.run_tick_loop())
    
    async def run_tick_loop(self):
        """Run the game tick in a loop."""
        tick_count = 0
        while True:
            try:
                self.tick_fn()
                tick_count += 1
                self.world_info = f"Tick: {tick_count}"
                await asyncio.sleep(1.0 / 60.0)  # 60 FPS
            except Exception as e:
                self.world_info = f"Error: {e}"
                break
    
    def watch_world_info(self, new_info: str) -> None:
        """Update info bar when world_info changes."""
        try:
            label = self.query_one("#info-bar Label", Label)
            label.update(new_info)
        except:
            pass
    
    def update_world_view(self, world_handle: int) -> None:
        """Update tree view with world state."""
        try:
            tree = self.query_one(Tree)
            tree.clear()
            tree.root.label = "ECS World"
            
            world_struct = World.from_address(world_handle)
            
            for i in range(world_struct.containers_count):
                container = world_struct.containers[i]
                total_entities = sum(
                    container.chunks[j].entities_count 
                    for j in range(container.chunks_count)
                )
                
                container_node = tree.root.add(
                    f"Container {i} ({total_entities} entities)"
                )
                container_node.add(f"Components: {container.archetype.length}")
                container_node.add(f"Chunks: {container.chunks_count}")
                
                for j in range(container.chunks_count):
                    chunk = container.chunks[j]
                    chunk_node = container_node.add(
                        f"Chunk {j} ({chunk.entities_count} entities)"
                    )
                
                container_node.expand()
        except Exception as e:
            self.world_info = f"Error updating view: {e}"


def run(state, tick):
    """Run the TUI application with the given tick function."""
    state.app.tick_fn = tick
    state.app.run()

