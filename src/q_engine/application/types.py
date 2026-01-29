from typing import Annotated, TypeAlias
import numpy.typing as npt
import numpy as np

Vector4: TypeAlias = Annotated[npt.NDArray[np.float32], (('N', 4), np.float32)]
Vector3: TypeAlias = Annotated[npt.NDArray[np.float32], (('N', 3), np.float32)]
Vector2: TypeAlias = Annotated[npt.NDArray[np.float32], (('N', 2), np.float32)]
Scalar: TypeAlias = Annotated[npt.NDArray[np.float32], (('N',), np.float32)]
Matrix4x4: TypeAlias = Annotated[npt.NDArray[np.float32], (('N', 4, 4), np.float32)]
Quaternion: TypeAlias = Annotated[npt.NDArray[np.float32], (('N', 4), np.float32)]
