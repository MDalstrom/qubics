from q_engine.units import Float32x3x3
from q_engine.ecs.components import component, Component


@component
class Transform(Component):
    matrices: Float32x3x3
