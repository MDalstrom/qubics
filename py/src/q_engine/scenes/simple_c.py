from q_engine.bootstrap import get_config
from q_engine.metal import mk_library
from q_engine.persistent.metal import state as metal_state
from q_engine.d2.render.shape import mk_shape_system
from flatbuffers.builder import Builder
from q_generated.components import Shape as ShapeMod
from q_generated.components import Transform2D as Transform2DMod
from q_generated.components import CameraCache as CameraCacheMod
from q_generated.units import Vector2 as Vector2Mod
from q_generated.units import Color as ColorMod
from q_generated.units import Matrix3x3 as Matrix3x3Mod
from q_generated.units import Matrix4x4 as Matrix4x4Mod
from q_generated.components.Shape import Shape
from q_generated.components.Transform2D import Transform2D
from q_generated.components.CameraCache import CameraCache

from q_engine.ecs.c_bindings import WorldHandle
from q_engine.server.protocol import NetworkWorld
from q_engine.server import mk_socket

import numpy as np


def bake(world):
    # Register component types
    shape_comp_id = world.register_component_type(Shape)
    transform_comp_id = world.register_component_type(Transform2D)
    camera_comp_id = world.register_component_type(CameraCache)
    
    # Create camera entity
    camera_entity = world.create_entity([camera_comp_id])
    
    # Create camera cache with identity view-projection matrix
    camera_builder = Builder()
    identity_matrix = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ]
    
    CameraCacheMod.StartViewProjectionVector(camera_builder, 1)
    Matrix4x4Mod.CreateMatrix4x4(camera_builder, *identity_matrix)
    vp_offset = camera_builder.EndVector()
    
    CameraCacheMod.CameraCacheStart(camera_builder)
    CameraCacheMod.AddViewProjection(camera_builder, vp_offset)
    camera_obj = CameraCacheMod.CameraCacheEnd(camera_builder)
    
    camera_builder.Finish(camera_obj)
    camera_data = bytes(camera_builder.Output())
    
    for chunk in world.query_chunks([camera_comp_id]):
        chunk.set_component_buffer(camera_comp_id, camera_data)
    
    # Create shape entity with transform
    shape_entity = world.create_entity([shape_comp_id, transform_comp_id])
    
    # Build shape component
    shape_builder = Builder()
    
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

    ShapeMod.StartVerticesVector(shape_builder, len(vertices))
    for v in reversed(vertices):
        Vector2Mod.CreateVector2(shape_builder, v[0], v[1])
    vertices_offset = shape_builder.EndVector()

    ShapeMod.StartColorsVector(shape_builder, len(colors))
    for c in reversed(colors):
        ColorMod.CreateColor(shape_builder, c[0], c[1], c[2], c[3])
    colors_offset = shape_builder.EndVector()

    ShapeMod.ShapeStart(shape_builder)
    ShapeMod.AddVertices(shape_builder, vertices_offset)
    ShapeMod.AddColors(shape_builder, colors_offset)
    shape_obj = ShapeMod.ShapeEnd(shape_builder)
    
    shape_builder.Finish(shape_obj)
    shape_data = bytes(shape_builder.Output())
    
    # Build transform component (identity matrix)
    transform_builder = Builder()
    
    Transform2DMod.StartMatricesVector(transform_builder, 1)
    Matrix3x3Mod.CreateMatrix3x3(transform_builder,
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0
    )
    matrices_offset = transform_builder.EndVector()
    
    Transform2DMod.Transform2DStart(transform_builder)
    Transform2DMod.AddMatrices(transform_builder, matrices_offset)
    transform_obj = Transform2DMod.Transform2DEnd(transform_builder)
    
    transform_builder.Finish(transform_obj)
    transform_data = bytes(transform_builder.Output())
    
    # Set component buffers
    for chunk in world.query_chunks([shape_comp_id, transform_comp_id]):
        chunk.set_component_buffer(shape_comp_id, shape_data)
        chunk.set_component_buffer(transform_comp_id, transform_data)

    return shape_entity, shape_comp_id


def get_tick(state = metal_state, config = get_config()):
    world = WorldHandle(chunk_capacity=256)
    world = NetworkWorld(world)
    transmit = mk_socket(world)
    
    entity, comp_id = bake(world)

    library = mk_library(state.device, config.shaderslib)
    s_render = mk_shape_system(state.device, state.view, library)

    def tick(command_buffer):
        s_render(world, command_buffer)

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

