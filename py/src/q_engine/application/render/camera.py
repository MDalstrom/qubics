from flatbuffers.builder import Builder
from typing import Callable
from q_generated.components.PerspectiveCamera import PerspectiveCamera
from q_generated.components.OrthographicCamera import OrthographicCamera
from q_generated.components.Viewport import Viewport
from q_generated.components.CameraCache import CameraCache
from q_generated.components.Transform3D import Transform3D
from q_generated.components import CameraCache as CameraCacheMod
from q_generated.units import Matrix4x4 as Matrix4x4Mod
from q_generated.units.Vector4 import Vector4
import numpy as np


def mk_orthographic(get_aspect: Callable[[], float]):
    def mk_matrix(size, aspect, near, far):
        top = size
        right = top * aspect
        bottom = -top
        left = -right

        sLength = 1.0 / (right - left)
        sHeight = 1.0 / (top   - bottom)
        sDepth  = 1.0 / (far   - near)

        P, Q, R, S = [np.zeros(4, dtype=np.float32) for _ in range(4)]

        P[0] = 2.0 * sLength
        P[1] = 0.0
        P[2] = 0.0
        P[3] = 0.0

        Q[0] = 0.0
        Q[1] = 2.0 * sHeight
        Q[2] = 0.0
        Q[3] = 0.0

        R[0] = 0.0
        R[1] = 0.0
        R[2] = sDepth
        R[3] = 0.0

        S[0] =  0.0
        S[1] =  0.0
        S[2] = -near  * sDepth
        S[3] =  1.0

        return np.array([P,Q,R,S])

    def system(world: WorldHandle):
        camera_comp_id = world.register_component_type(OrthographicCamera)
        viewport_comp_id = world.register_component_type(Viewport)
        transform_comp_id = world.register_component_type(Transform3D)
        cache_comp_id = world.register_component_type(CameraCache)
        
        for chunk in world.query_chunks([camera_comp_id, viewport_comp_id, transform_comp_id, cache_comp_id]):
            camera_data = chunk.get_component_buffer_bytes(camera_comp_id)
            viewport_data = chunk.get_component_buffer_bytes(viewport_comp_id)
            transform_data = chunk.get_component_buffer_bytes(transform_comp_id)
            
            if not all([camera_data, viewport_data, transform_data]):
                continue
            
            camera = OrthographicCamera.GetRootAs(camera_data, 0)
            viewport = Viewport.GetRootAs(viewport_data, 0)
            transform = Transform3D.GetRootAs(transform_data, 0)
            
            entity_count = min(camera.SizeLength(), viewport.NearLength(), transform.MatricesLength())
            
            for i in range(entity_count):
                size = camera.Size(i)
                near = viewport.Near(i)
                far = viewport.Far(i)
                
                mat = transform.Matrices(i)
                m0 = mat.M0(Vector4())
                m1 = mat.M1(Vector4())
                m2 = mat.M2(Vector4())
                m3 = mat.M3(Vector4())
                transform_matrix = np.array([
                    [m0.X(), m0.Y(), m0.Z(), m0.W()],
                    [m1.X(), m1.Y(), m1.Z(), m1.W()],
                    [m2.X(), m2.Y(), m2.Z(), m2.W()],
                    [m3.X(), m3.Y(), m3.Z(), m3.W()]
                ], dtype=np.float32)
                
                view = np.linalg.inv(transform_matrix)
                projection = mk_matrix(size, get_aspect(), near, far)
                vp_matrix = view @ projection
                
                builder = Builder()
                
                CameraCacheMod.StartViewProjectionVector(builder, 1)
                Matrix4x4Mod.CreateMatrix4x4(builder, *vp_matrix.flatten().tolist())
                vp_offset = builder.EndVector()
                
                CameraCacheMod.CameraCacheStart(builder)
                CameraCacheMod.AddViewProjection(builder, vp_offset)
                cache_obj = CameraCacheMod.CameraCacheEnd(builder)
                
                builder.Finish(cache_obj)
                cache_data = bytes(builder.Output())
                
                chunk.set_component_buffer(cache_comp_id, cache_data)

    return system

def mk_perspective(get_aspect: Callable[[], float]):
    def mk_matrix(fov: float, aspect: float, near: float, far: float):
        f = 1.0 / np.tan(fov * 0.5)

        P, Q, R, S = [np.zeros(4, dtype=np.float32) for _ in range(4)]

        P[0] = f / aspect
        P[1] = 0.0
        P[2] = 0.0
        P[3] = 0.0

        Q[0] = 0.0
        Q[1] = f
        Q[2] = 0.0
        Q[3] = 0.0

        R[0] = 0.0
        R[1] = 0.0
        R[2] = far / (far - near)
        R[3] = 1.0

        S[0] = 0.0
        S[1] = 0.0
        S[2] = -near * far / (far - near)
        S[3] = 0.0

        return np.array([P, Q, R, S])
    
    def system(world: World):
        camera_comp_id = world.register_component_type(PerspectiveCamera)
        viewport_comp_id = world.register_component_type(Viewport)
        transform_comp_id = world.register_component_type(Transform3D)
        cache_comp_id = world.register_component_type(CameraCache)
        
        for chunk in world.query_chunks([camera_comp_id, viewport_comp_id, transform_comp_id, cache_comp_id]):
            camera_data = chunk.get_component_buffer_bytes(camera_comp_id)
            viewport_data = chunk.get_component_buffer_bytes(viewport_comp_id)
            transform_data = chunk.get_component_buffer_bytes(transform_comp_id)
            
            if not all([camera_data, viewport_data, transform_data]):
                continue
            
            camera = PerspectiveCamera.GetRootAs(camera_data, 0)
            viewport = Viewport.GetRootAs(viewport_data, 0)
            transform = Transform3D.GetRootAs(transform_data, 0)
            
            entity_count = min(camera.FovLength(), viewport.NearLength(), transform.MatricesLength())
            
            for i in range(entity_count):
                fov = camera.Fov(i)
                near = viewport.Near(i)
                far = viewport.Far(i)
                
                mat = transform.Matrices(i)
                m0 = mat.M0(Vector4())
                m1 = mat.M1(Vector4())
                m2 = mat.M2(Vector4())
                m3 = mat.M3(Vector4())
                transform_matrix = np.array([
                    [m0.X(), m0.Y(), m0.Z(), m0.W()],
                    [m1.X(), m1.Y(), m1.Z(), m1.W()],
                    [m2.X(), m2.Y(), m2.Z(), m2.W()],
                    [m3.X(), m3.Y(), m3.Z(), m3.W()]
                ], dtype=np.float32)
                
                view = np.linalg.inv(transform_matrix)
                projection = mk_matrix(fov, get_aspect(), near, far)
                vp_matrix = view @ projection
                
                # Build and set camera cache
                builder = Builder()
                
                CameraCacheMod.StartViewProjectionVector(builder, 1)
                Matrix4x4Mod.CreateMatrix4x4(builder, *vp_matrix.flatten().tolist())
                vp_offset = builder.EndVector()
                
                CameraCacheMod.CameraCacheStart(builder)
                CameraCacheMod.AddViewProjection(builder, vp_offset)
                cache_obj = CameraCacheMod.CameraCacheEnd(builder)
                
                builder.Finish(cache_obj)
                cache_data = bytes(builder.Output())
                
                chunk.set_component_buffer(cache_comp_id, cache_data)

    return system
