import numpy as np


class generic_dyn_ndarray:
    def __class_getitem__(cls, params):
        if not isinstance(params, tuple):
            params = (params,)
        
        return type('dyn_ndarray', (), {
            '__dtype__': params[0],
            '__shape__': params[1:]
        })

Float32x4x4 = generic_dyn_ndarray[np.float32, 4, 4]
Float32x4 = generic_dyn_ndarray[np.float32, 4]
Float32x3 = generic_dyn_ndarray[np.float32, 3]
Float32x2 = generic_dyn_ndarray[np.float32, 2]
Float32x1 = generic_dyn_ndarray[np.float32]
Boolean = generic_dyn_ndarray[np.bool, 1]
