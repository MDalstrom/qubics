from typing import Protocol
from domain import World


class Baker(Protocol):
    def __call__(self, world: World) -> None:
        ...
