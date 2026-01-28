import numpy as np
from typing import Annotated, TypeAlias
from numpy.typing import NDArray

Matrix4x4: TypeAlias = Annotated[NDArray[np.float32], "shape (4, 4)"]

def create_view_matrix(eye: np.ndarray, center: np.ndarray, up: np.ndarray) -> Matrix4x4:
    """Create view matrix (world to camera)"""
    f = (center - eye)
    f = f / np.linalg.norm(f)
    
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    
    u = np.cross(s, f)
    
    view = np.eye(4, dtype=np.float32, order='F')
    view[0, :3] = s
    view[1, :3] = u
    view[2, :3] = -f
    view[0, 3] = -np.dot(s, eye)
    view[1, 3] = -np.dot(u, eye)
    view[2, 3] = np.dot(f, eye)
    
    return view

def create_perspective_matrix(fov: float, aspect: float, near: float, far: float) -> Matrix4x4:
    """Create perspective projection matrix"""
    f = 1.0 / np.tan(fov / 2)
    
    proj = np.zeros((4, 4), dtype=np.float32, order='F')
    proj[0, 0] = f / aspect
    proj[1, 1] = f
    proj[2, 2] = (far + near) / (near - far)
    proj[2, 3] = -1.0
    proj[3, 2] = (2 * far * near) / (near - far)
    
    return proj

def create_orthographic_matrix(left: float, right: float, bottom: float, top: float, near: float, far: float) -> Matrix4x4:
    """Create orthographic projection (for UI, 2D)"""
    ortho = np.zeros((4, 4), dtype=np.float32, order='F')
    ortho[0, 0] = 2 / (right - left)
    ortho[1, 1] = 2 / (top - bottom)
    ortho[2, 2] = -2 / (far - near)
    ortho[0, 3] = -(right + left) / (right - left)
    ortho[1, 3] = -(top + bottom) / (top - bottom)
    ortho[2, 3] = -(far + near) / (far - near)
    ortho[3, 3] = 1.0
    
    return ortho

view = create_view_matrix(
    eye=np.array([0, 5, 10], dtype=np.float32),
    center=np.array([0, 0, 0], dtype=np.float32),
    up=np.array([0, 1, 0], dtype=np.float32)
)

proj = create_perspective_matrix(fov=np.pi/4, aspect=16/9, near=0.1, far=100)
viewProj = proj @ view

