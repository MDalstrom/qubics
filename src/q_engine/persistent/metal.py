import q_engine.metal as metal
from q_engine.metal import State


def get_state() -> State:
    device = metal.mk_device()
    view = metal.mk_view(device)
    window = metal.mk_window()
    app = metal.mk_app()

    return metal.State(device, window, app, view)

state = get_state()
