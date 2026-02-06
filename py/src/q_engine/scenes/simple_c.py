from q_engine.bootstrap import get_config
from q_engine.metal import mk_library
from q_engine.persistent.metal import state as metal_state
from q_engine.d2.render.shape import mk_shape_system
from q_engine.application.render.camera import mk_orthographic
from flatbuffers.builder import Builder
from q_generated.components import Shape as ShapeMod
from q_generated.components import Transform2D as Transform2DMod
from q_generated.components import Transform3D as Transform3DMod
from q_generated.components import OrthographicCamera as OrthographicCameraMod
from q_generated.components import Viewport as ViewportMod
from q_generated.components import CameraCache as CameraCacheMod
from q_generated.units import Vector2 as Vector2Mod
from q_generated.units import Color as ColorMod
from q_generated.units import Matrix3x3 as Matrix3x3Mod
from q_generated.units import Matrix4x4 as Matrix4x4Mod
from q_generated.components.Shape import Shape
from q_generated.components.Transform2D import Transform2D
from q_generated.components.Transform3D import Transform3D
from q_generated.components.OrthographicCamera import OrthographicCamera
from q_generated.components.Viewport import Viewport
from q_generated.components.CameraCache import CameraCache

from q_engine.ecs.c_bindings import WorldHandle
from q_engine.server.protocol import NetworkWorld
from q_engine.server import mk_socket

import numpy as np


def bake(world):
    # Register component types
    shape_comp_id = world.register_component_type(Shape)
    transform2d_comp_id = world.register_component_type(Transform2D)
    transform3d_comp_id = world.register_component_type(Transform3D)
    camera_comp_id = world.register_component_type(OrthographicCamera)
    viewport_comp_id = world.register_component_type(Viewport)
    cache_comp_id = world.register_component_type(CameraCache)
    
    # Create camera entity with Transform3D, OrthographicCamera, Viewport, and CameraCache
    camera_entity = world.create_entity([transform3d_comp_id, camera_comp_id, viewport_comp_id, cache_comp_id])
    
    # Build camera transform (identity matrix at origin)
    camera_transform_builder = Builder()
    Transform3DMod.StartMatricesVector(camera_transform_builder, 1)
    Matrix4x4Mod.CreateMatrix4x4(camera_transform_builder,
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, -5.0, 1.0
    )
    transform_offset = camera_transform_builder.EndVector()
    Transform3DMod.Transform3DStart(camera_transform_builder)
    Transform3DMod.AddMatrices(camera_transform_builder, transform_offset)
    transform_obj = Transform3DMod.Transform3DEnd(camera_transform_builder)
    camera_transform_builder.Finish(transform_obj)
    camera_transform_data = bytes(camera_transform_builder.Output())
    
    # Build orthographic camera (size = 1.0)
    camera_builder = Builder()
    OrthographicCameraMod.StartSizeVector(camera_builder, 1)
    camera_builder.PrependFloat32(1.0)
    size_offset = camera_builder.EndVector()
    OrthographicCameraMod.OrthographicCameraStart(camera_builder)
    OrthographicCameraMod.AddSize(camera_builder, size_offset)
    camera_obj = OrthographicCameraMod.OrthographicCameraEnd(camera_builder)
    camera_builder.Finish(camera_obj)
    camera_data = bytes(camera_builder.Output())
    
    # Build viewport (near = 0.1, far = 100.0)
    viewport_builder = Builder()
    ViewportMod.StartNearVector(viewport_builder, 1)
    viewport_builder.PrependFloat32(0.1)
    near_offset = viewport_builder.EndVector()
    ViewportMod.StartFarVector(viewport_builder, 1)
    viewport_builder.PrependFloat32(100.0)
    far_offset = viewport_builder.EndVector()
    ViewportMod.ViewportStart(viewport_builder)
    ViewportMod.AddNear(viewport_builder, near_offset)
    ViewportMod.AddFar(viewport_builder, far_offset)
    viewport_obj = ViewportMod.ViewportEnd(viewport_builder)
    viewport_builder.Finish(viewport_obj)
    viewport_data = bytes(viewport_builder.Output())
    
    # Build initial cache (identity matrix)
    cache_builder = Builder()
    CameraCacheMod.StartViewProjectionVector(cache_builder, 1)
    Matrix4x4Mod.CreateMatrix4x4(cache_builder,
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    )
    vp_offset = cache_builder.EndVector()
    CameraCacheMod.CameraCacheStart(cache_builder)
    CameraCacheMod.AddViewProjection(cache_builder, vp_offset)
    cache_obj = CameraCacheMod.CameraCacheEnd(cache_builder)
    cache_builder.Finish(cache_obj)
    cache_data = bytes(cache_builder.Output())
    
    # Set camera component buffers
    for chunk in world.query_chunks([transform3d_comp_id, camera_comp_id, viewport_comp_id, cache_comp_id]):
        chunk.set_component_buffer(transform3d_comp_id, camera_transform_data)
        chunk.set_component_buffer(camera_comp_id, camera_data)
        chunk.set_component_buffer(viewport_comp_id, viewport_data)
        chunk.set_component_buffer(cache_comp_id, cache_data)
    
    # Create shape entity with transform
    shape_entity = world.create_entity([shape_comp_id, transform2d_comp_id])
    
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
    
    # Set shape component buffers
    for chunk in world.query_chunks([shape_comp_id, transform2d_comp_id]):
        chunk.set_component_buffer(shape_comp_id, shape_data)
        chunk.set_component_buffer(transform2d_comp_id, transform_data)

    return shape_entity, shape_comp_id


def get_tick(state = metal_state, config = get_config()):
    world = WorldHandle(chunk_capacity=256)
    world = NetworkWorld(world)
    transmit = mk_socket(world)
    
    entity, comp_id = bake(world)

    library = mk_library(state.device, config.shaderslib)
    s_render = mk_shape_system(state.device, state.view, library)
    s_camera = mk_orthographic(lambda: 1.0)  # Aspect ratio 1:1

    def tick(command_buffer):
        s_camera(world)  # Update camera view-projection matrix
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
