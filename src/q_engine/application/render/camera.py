from q_engine.ecs.components import Component

class Camera(Component):
    fov: float
    near: float
    far: float
