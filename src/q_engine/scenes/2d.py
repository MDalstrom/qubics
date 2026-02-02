from q_engine.d2.transform import Transform
from q_engine.ecs.command_buffer import CommandBuffer, DeferredEntity
from q_engine.d2.render.shape import mk_shape_system, Shape
from q_engine.ecs.world import World, Entity
from q_engine.persistent.metal import state as state
from q_engine.metal import get_aspect, mk_library
from q_engine.application.render.camera import mk_orthographic, CameraCache, Viewport, OrthographicCamera
from functools import partial
import numpy as np


def bake(cb: CommandBuffer):
    cb = CommandBuffer()
    
    e: DeferredEntity

    e = cb.create_entity()
    cb.add_component(e, Transform)
    def set_transform(e: Entity, transform: Transform):
        pass
    cb.set_component(e, Transform, set_transform)
    
    cb.add_component(e, Shape)
    def set_shape(e: Entity, shape: Shape):
        shape.vertices[e.index] = np.array([
            [-1, -1],
            [-1, 1],
            [1, 1],
            [1, -1],
        ])
        shape.colors[e.index] = np.repeat([1, 1, 1, 1], 4)
    cb.set_component(e, Shape, set_shape)

    e = cb.create_entity()
    cb.add_component(e, CameraCache)

    cb.add_component(e, Transform)
    def set_transform(e: Entity, transform: Transform):
        pass
    cb.set_component(e, Transform, set_transform)

    cb.add_component(e, OrthographicCamera)
    def set_orthographic(e: Entity, camera: OrthographicCamera):
        camera.size = 5
    cb.set_component(e, OrthographicCamera, set_orthographic)

    cb.add_component(e, Viewport)
    def set_viewport(e: Entity, viewport: Viewport):
        viewport.far[e.index] = 100
        viewport.near[e.index] = 0.1
    cb.set_component(e, Viewport, set_viewport)

def get_tick(
    state=state, 
    simulation_dt=1/60.0
):
    world = World()

    cb = CommandBuffer()
    bake(cb)
    cb.playback(world)

    library = mk_library(state.device)
    camera = mk_orthographic(partial(get_aspect, state))
    render = mk_shape_system(state.device, state.view, library)

    def game_tick(command_buffer):
        camera(world=world)
        render(world=world, command_buffer=command_buffer)

    return game_tick
