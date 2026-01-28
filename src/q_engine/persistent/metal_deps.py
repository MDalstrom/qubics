from functools import lru_cache
import q_engine.metal as metal


@lru_cache(1)
def get_state():
    
    device = metal.device_fc()
    view = metal.view_fc(device)
    window = metal.window_fc()
    app = metal.app_fc()

    return metal.State(device, window, app, view)
