import mlx.core as mx

class Position:
    def __init__(self) -> None:
        self.x = mx.zeros(1, dtype=mx.float32)
        self.y = mx.zeros(1, dtype=mx.float32)

class Velocity:
    def __init__(self) -> None:
        self.x = mx.zeros(1, dtype=mx.float32)
        self.y = mx.zeros(1, dtype=mx.float32)





