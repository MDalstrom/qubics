from typing import Callable


def singleton(fn: Callable):
    cache = None
    def inner(*args, **kwargs):
        nonlocal cache
        if not cache:
            cache = fn(*args, **kwargs)
        return cache
    return inner
