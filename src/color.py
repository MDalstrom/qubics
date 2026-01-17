from dataclasses import dataclass


@dataclass
class Color():
    r: float
    g: float
    b: float
    a: float = 1.0

    def __iter__(self):
        yield self.r
        yield self.g
        yield self.b
        yield self.a
