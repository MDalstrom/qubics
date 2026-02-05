from flatbuffers.builder import Builder
from q_generated.components import Shape as ShapeMod
from q_generated.units import Vector2 as Vector2Mod
from q_generated.units import Color as ColorMod # Added import for Color
from q_generated.components.Shape import Shape

from q_engine.ecs.c_bindings import WorldHandle
from q_engine.server.protocol import NetworkWorld
from q_engine.server import mk_socket

import numpy as np


def bake(world):
    comp_id = world.register_component_type(Shape)
    entity = world.create_entity([comp_id])
    
    builder = Builder()

    vertices = np.array([
        (0.0, 0.5),
        (-0.5, -0.5),
        (0.5, -0.5)
    ], dtype=np.float32)
    
    colors = np.array([
        (1.0, 0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0, 1.0),
        (0.0, 0.0, 1.0, 1.0)
    ], dtype=np.float32)

    ShapeMod.StartVerticesVector(builder, len(vertices))
    for v in reversed(vertices):
        Vector2Mod.CreateVector2(builder, v[0], v[1])
    vertices_offset = builder.EndVector()

    ShapeMod.StartColorsVector(builder, len(colors))
    for c in reversed(colors):
        ColorMod.CreateColor(builder, c[0], c[1], c[2], c[3])
    colors_offset = builder.EndVector()

    ShapeMod.ShapeStart(builder)
    ShapeMod.AddVertices(builder, vertices_offset)
    ShapeMod.AddColors(builder, colors_offset)
    shape_obj = ShapeMod.ShapeEnd(builder)
    
    builder.Finish(shape_obj)
    
    component_data = bytes(builder.Output())
    for chunk in world.query_chunks([comp_id]):
        chunk.set_component_buffer(comp_id, component_data)

    return entity, comp_id


def get_tick():
    world = WorldHandle(chunk_capacity=256)
    world = NetworkWorld(world)
    transmit = mk_socket(world)
    
    entity, comp_id = bake(world)
    
    def tick(command_buffer):
        transmit(world)
        
        data = None
        for c in world.query_chunks([comp_id]):
            data = c.get_component_buffer_bytes(comp_id)
            break
        if not data:
            return
        update = world.build_entity_update(entity, comp_id, data)
        transmit.broadcast(update)
        
    return tick

