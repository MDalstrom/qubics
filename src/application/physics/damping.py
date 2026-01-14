from dataclasses import dataclass
from application.physics.velocity import Velocity
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@dataclass
class Damping():
    linear: float
    angular: float

@for_each
def apply_linear(world: World, entity: Entity, velocity: Velocity, damping: Damping):
    velocity.linear *= 1 - damping.linear * world.timestep

@for_each
def apply_angular(world: World, entity: Entity, velocity: Velocity, damping: Damping):
    velocity.angular *= 1 - damping.angular * world.timestep
