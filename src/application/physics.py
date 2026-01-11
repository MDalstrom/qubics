from dataclasses import dataclass
from application.transform import Transform
from ecs.entity import EntityRef, Entity
from ecs.world import World
from ecs.system import for_each


@dataclass
class Rigidbody:
    vx: float
    vy: float
    angular_velocity: float = 0.0
    angular_damping: float = 0.0
    friction: float = 0.0
    restitution: float = 1.0


@dataclass
class Acceleration:
    ax: float = 0.0
    ay: float = 0.0


@dataclass
class Parent:
    owner: EntityRef
    offset_distance: float = 0.0
    offset_angle: float = 0.0


@for_each
def acceleration_system(
    world: World, _: Entity, rigidbody: Rigidbody, acceleration: Acceleration
) -> None:
    rigidbody.vx += acceleration.ax * world.timestep
    rigidbody.vy += acceleration.ay * world.timestep


@for_each
def movement_system(
    world: World, _: Entity, transform: Transform, rigidbody: Rigidbody
) -> None:
    transform.save_previous()
    wx, wy = transform.get_world_position()
    wx += rigidbody.vx * world.timestep
    wy += rigidbody.vy * world.timestep
    transform.set_world_position(wx, wy)
