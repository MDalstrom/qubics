from q_engine.ecs.components import Component, World
import numpy as np

class Camera(Component):
    def __init__(self) -> None:
        self.fov: float = np.pi / 180 * 80
        self.near: float = .01
        self.far: float = 1000.0

    def add(self, i, size=1): ...

