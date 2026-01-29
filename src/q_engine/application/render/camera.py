from q_engine.ecs.components import Component
from q_engine.application.types import Scalar

class Camera(Component):
    fov: Scalar
    near: Scalar
    far: Scalar
