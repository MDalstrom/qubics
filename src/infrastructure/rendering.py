from rendering.factory import (
    create_device,
    create_library,
    create_pipeline,
    create_delegate,
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

@singleton
def get_delegate():
    return create_delegate()

@singleton
def get_view(config = get_config()):
    device = get_device()
    delegate = get_delegate()
    rect = (0, 0, config['width'], config['height'])
    color = config['background-color']
    background_color = (color.r, color.g, color.b, color.a)
    return create_view(device, delegate, rect, background_color)

@singleton
def get_texture(config = get_config()):
    device = get_device()
    return create_texture(device, width=config['width'], height=config['height'])
