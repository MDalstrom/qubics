from typing import Callable, Protocol


class Tick(Protocol):
    def __call__(self): ...

class Loop(Protocol):
    def __call__(self, tick: Tick) -> None: ...



