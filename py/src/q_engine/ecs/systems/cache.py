from functools import wraps
from typing import Callable


def cache(name: str):
    def wrapper(fn: Callable):
        last = None
        @wraps(fn)
        def inner(*args, **kwargs):
            nonlocal last
            current = kwargs[name]
            if last == current:
                return
            fn(args, kwargs)
            last = current 
        return inner
    return wrapper
