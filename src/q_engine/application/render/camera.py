from q_engine.ecs.systems.query import query
from typing import Callable
from q_engine.ecs.components import component, Component
from q_engine.units import Float32x4x4, Float32x1
from q_engine.application.transform import Transform
import numpy as np


@component
class PerspectiveCamera(Component):
    fov: Float32x1

@component
class OrthographicCamera(Component):
    size: Float32x1

@component
class Viewport(Component):
    near: Float32x1
    far: Float32x1

@component
class CameraCache(Component):
    viewProjectionMatrix: Float32x4x4

def mk_orthographic(get_aspect: Callable[[], float]):
    def mk_matrix(size, aspect, far, near):
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

    @query
    def system(transform: Transform, camera: OrthographicCamera, viewport: Viewport, cache: CameraCache):
        view = np.linalg.inv(transform.matrices[0])
        projection = mk_matrix(camera.size, get_aspect(), viewport.near, viewport.far)
        cache.viewProjectionMatrix = view @ projection

    return system

def mk_perspective(get_aspect: Callable[[], float]):
    def mk_matrix(fov: float, aspect: float, near: float, far: float) -> Float32x4x4:
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
    
    def system(transform: Transform, camera: PerspectiveCamera, viewport: Viewport, cache: CameraCache):
        view = np.linalg.inv(transform.matrices[0])
        projection = mk_matrix(camera.fov, get_aspect(), viewport.near, viewport.far)
        cache.viewProjectionMatrix = view @ projection

    return query
