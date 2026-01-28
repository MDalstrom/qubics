import numpy as np
from functools import partial
from q_engine.application.render.mesh import Mesh, Transform, create
from q_engine.ecs.components import CommandBuffer, Entity, World
from q_engine.metal import library_fc
from q_engine.persistent.metal_deps import get_state

def bake(world: World):
    cb = CommandBuffer()
    e = cb.create_entity()
    cb.add_component(e, Mesh)
   
    @CommandBuffer.set_deferred(cb, e, Mesh)
    def _(e: Entity, mesh: Mesh):
        mesh.vertices = np.array([
            [-0.5, 0.1, 0.2, 0],
            [0, 0.5, 0, 0],
            [0.5, 0, 0, 0],
        ])

    cb.add_component(e, Transform)
    @CommandBuffer.set_deferred(cb, e, Transform)
    def _(e: Entity, mesh: Transform):
        mesh.matrices = np.array([np.eye(4, order='F')])
    cb.playback(world)

def get_tick(state = get_state()):
    world = World()
    
    bake(world)

    library = library_fc(state.device)
    s = create(state.device, state.view, library)
    s = partial(s, world)
    return s
