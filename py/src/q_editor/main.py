import ctypes
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Static
from textual.reactive import reactive

from q_ecs.c_bindings import mk_world_factory
from q_ecs.network import Client
from q_ecs.types import Component
from q_engine.bootstrap import get_config

class TestComponent(Component):
    _fields_ = [("value", ctypes.c_int32)]

class TestComponent2(Component):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

class EcsInspectorApp(App):
    ENABLE_DEVTOOLS = True
    CSS = """
    Screen {
        background: transparent;
        color: $text;
    }
    #tree-view {
        dock: left;
        width: 40%;
        background: transparent;
    }
    #details-view {
        dock: right;
        width: 60%;
        padding: 0 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("d", "toggle_dark", "Toggle Dark")]

    world_data = reactive({})

    def __init__(self):
        super().__init__()
        self._dom_ready = False
        self.config = get_config()
        world_factory = mk_world_factory(self.config.ecslib)
        self.world = world_factory()
        self.client = Client(
            world=self.world,
            host='127.0.0.1',
            port=8888,
            component_types=[TestComponent, TestComponent2],
            update_callback=self._handle_network_update,
        )
        self.world_data = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Tree("ECS World", id="tree-view")
        yield Static(id="details-view")
        yield Footer()

    async def on_mount(self) -> None:
        self._dom_ready = True
        self.world_data = {
            "TestComponent": {"value": 0},
            "TestComponent2": {"x": 0.0, "y": 0.0},
        }
        asyncio.create_task(self.connect_and_listen())

    async def connect_and_listen(self):
        try:
            await self.client.connect()
            self.log("Client connected, starting listener...")
            await self.client.listen()
        except ConnectionRefusedError:
            details_pane = self.query_one("#details-view", Static)
            details_pane.update("Connection to server failed.")

    def watch_world_data(self, new_data: dict) -> None:
        self.log(f"WATCHER: Triggered with data: {new_data}")
        if not self._dom_ready:
            return

        tree = self.query_one(Tree)
        tree.clear()
        tree.root.label = "ECS World"

        for comp_name, comp_data in new_data.items():
            fields_str = ", ".join([
                f"{field_name}={field_value:.2f}" if isinstance(field_value, float) else f"{field_name}={field_value}"
                for field_name, field_value in comp_data.items()
            ])
            node = tree.root.add(f"{comp_name}: {fields_str}")
            node.expand()

    def _handle_network_update(self, message: bytes):
        self.log(f"CALLBACK: Received {len(message)} bytes in background.")
        if not message:
            return

        comp_id = message[0]
        raw_data = message[1:]
        
        comp_info = self.client.id_map.get(comp_id)
        if not comp_info:
            return

        if len(raw_data) == comp_info['stride']:
            comp_type = comp_info['type']
            comp_instance = comp_type.from_buffer_copy(raw_data)
            self.call_soon(self.update_world_data, comp_info, comp_instance)

    def update_world_data(self, comp_info: dict, comp_instance: Component):
        self.log(f"MAIN THREAD: Updating with {comp_info['name']}")
        comp_name = comp_info['name']

        new_comp_data = {fname: getattr(comp_instance, fname) for fname, _ in comp_instance._fields_}

        updated_data = self.world_data.copy()
        updated_data[comp_name] = new_comp_data
        self.world_data = updated_data

if __name__ == "__main__":
    app = EcsInspectorApp()
    app.run()
