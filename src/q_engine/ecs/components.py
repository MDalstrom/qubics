import numpy as np
from typing import (
    TypeVar,
    Protocol, get_type_hints
)


T = TypeVar('T', bound='Component')
class Component(Protocol):
    def __getitem__(self: T, key: int | slice) -> T: ...
    def assert_exist(self, key: int | slice): ...

def component(cls: type) -> type[Component]:
    fields = []
    
    for name, hint in get_type_hints(cls).items():
        if hasattr(hint, '__dtype__') and hasattr(hint, '__shape__'):
            fields.append((name, hint.__shape__, hint.__dtype__))

    def __init__(self):
        for name, shape, dtype in fields:
            setattr(self, name, np.zeros([1, *shape], dtype=dtype))
    setattr(cls, "__init__", __init__)

    def __getitem__(self, key: int | slice):
        if isinstance(key, int):
            key = slice(key, key + 1)
        view = cls()
        for name, _, dtype in fields:
            arr: np.ndarray = getattr(self, name)
            setattr(view, name, arr[key])
        return view
    setattr(cls, "__getitem__", __getitem__)

    def assert_exist(self, key: int | slice):
        if isinstance(key, int):
            key = slice(key, key + 1)

        for name, _, dtype in fields:
            arr: np.ndarray = getattr(self, name)

            if arr.shape[0] == 0:
                arr = np.zeros([1, *arr.shape[1:]], dtype=dtype)
                setattr(self, name, arr)

            while key.stop - 1 >= arr.shape[0]:
                arr = np.concat([arr, arr], dtype=dtype)
                setattr(self, name, arr)
    setattr(cls, "assert_exist", assert_exist)

    return cls


