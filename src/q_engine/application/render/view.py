import numpy as np
from typing import Annotated, TypeAlias
from numpy.typing import NDArray

Matrix4x4: TypeAlias = Annotated[NDArray[np.float32], "shape (4, 4)"]

def mk_view(eye: np.ndarray, center: np.ndarray, up: np.ndarray) -> Matrix4x4:
    f = center - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)

    view_matrix_rm = np.array([
        [s[0], s[1], s[2], -np.dot(s, eye)],
        [u[0], u[1], u[2], -np.dot(u, eye)],
        [-f[0], -f[1], -f[2], np.dot(f, eye)],
        [0,    0,    0,    1]
    ], dtype=np.float32)
    return np.asfortranarray(view_matrix_rm)

def mk_ortho(size, aspect, far, near):
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

def mk_perspective(fov, aspect, near, far):
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
