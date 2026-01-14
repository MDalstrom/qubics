from dataclasses import dataclass, field
from application.math import Vector
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@dataclass
class Velocity():
    linear: Vector = field(default_factory=Vector.zero)
    angular: float = 0.0

@for_each
def apply_linear(world: World, _: Entity, velocity: Velocity, transform: Transform):
    wx, wy = transform.get_world_position()
    wx += velocity.linear.x * world.timestep
    wy += velocity.linear.y * world.timestep
    transform.set_world_position(wx, wy)

@for_each
def apply_angular(world: World, _: Entity, velocity: Velocity, transform: Transform):
    angle = transform.get_world_angle()
    angle += velocity.angular * world.timestep
    transform.set_world_angle(angle)
