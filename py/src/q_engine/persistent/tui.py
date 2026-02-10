from dataclasses import dataclass
from textual.app import App


@dataclass
class State:
    app: App


def get_state() -> State:
    from q_engine.tui import EcsInspectorApp
    app = EcsInspectorApp()
    return State(app)


state = get_state()
