from threading import Lock
from typing import Callable
from rendering.factory import (
    create_device,
    create_library,
    create_pipeline,
    create_view,
    create_texture,
)
from singleton import singleton
from .config import get_config


@singleton
def get_device():
    return create_device()

@singleton
def get_library():
    device = get_device()
    return create_library(device)

@singleton
def get_pipeline():
    device = get_device()
    library = get_library()
    return create_pipeline(
        library, device,
        fragment_fn_name="fragment_main",
        vertex_fn_name="vertex_main"
    )

def fallback_loop(_: float): return 0.0
def wrap_catch(fn):
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except BaseException as e:
            import traceback
            traceback.print_exception(e)
            raise e
    return inner
loop_dispatcher = [fallback_loop]
loop_lock = Lock()
def set_dispatched(fn: Callable):
    with loop_lock:
        loop_dispatcher[0] = wrap_catch(fn)
def call_dispatched(*args, **kwargs):
    with loop_lock:
        return loop_dispatcher[0](*args, **kwargs)

@singleton
def get_view(config = get_config()):
    device = get_device()
    rect = (0, 0, config['width'], config['height'])
    color = config['background-color']
    background_color = (color.r, color.g, color.b, color.a)
    return create_view(device, call_dispatched, rect, background_color)

@singleton
def get_texture(config = get_config()):
    device = get_device()
    return create_texture(device, width=config['width'], height=config['height'])
