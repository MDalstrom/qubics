from __future__ import annotations
from typing import Callable
import Cocoa
import Metal

from color import Color
from recorder import FFmpegRecorder
from scenarios.types import Scenario
from ecs.system import SystemsGroup

from .handle_events import handle_events
from .shape import draw_shape_system
from .interactive import create as create_interactive, create_view
from .export import create as create_export, create_texture
from .factory import create, create_delegate, create_device, create_library, create_pipeline

device = create_device()

library = create_library(
    device
)

pipeline = create_pipeline(
    library,
    device,
    vertex_fn_name="vertex_main",
    fragment_fn_name="fragment_main",
)

def get_interactive(
    width: int, height: int,
    color: Color,
):
    rect = Cocoa.NSMakeRect(0, 0, width, height)
    background_color = Metal.MTLClearColorMake(color.r, color.g, color.b, color.a)
    delegate = create_delegate()
    view = create_view(
        device, delegate,
        rect=rect,
        background_color=background_color
    )
    return create_interactive(view)

def get_export(
    width: int, height: int, 
    fps: int, 
    path: str, 
    color: Color,
    create_pool: Callable
):
    recorder = FFmpegRecorder(width, height, fps, path)

    from infrastructure import cleanup
    cleanup.dependencies.append(recorder.finish)
    
    texture = create_texture(device, width=width, height=height)
    return create_export(texture, device, recorder, create_pool, width=width, height=height, background_color=color)
    
def get_scenario():
    base = create(device, pipeline)
    core = Scenario(
        SystemsGroup([], [], []),
        SystemsGroup([], [], []),
        rendering=SystemsGroup([handle_events], [draw_shape_system], []),
    )

    return base.merge(core)
