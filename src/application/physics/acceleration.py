from application.math import Vector
from application.physics.velocity import Velocity
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


class Acceleration(Vector): ...

@for_each
def apply(world: World, entity: Entity, acceleration: Acceleration, velocity: Velocity):
    velocity.linear += acceleration * world.timestep

