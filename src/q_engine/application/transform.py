from q_engine.ecs.components import component, Component
from q_engine.units import Float32x4x4


@component
class Transform(Component):
    matrices: Float32x4x4

