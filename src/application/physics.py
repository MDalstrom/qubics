from dataclasses import dataclass
from application.transform import Transform
from ecs.entity import EntityRef, Entity
from ecs.world import World
from ecs.system import for_each


@dataclass
class Rigidbody:
    vx: float
    vy: float
    mass: float = 1.0
    angular_velocity: float = 0.0
    angular_damping: float = 0.5
    inertia: float = 1000.0
    friction: float = 0.0
    restitution: float = 1.0
    position_correction: float = 0.2
    slop: float = 0.01
    
    @property
    def inv_mass(self) -> float:
        return 1.0 / self.mass if self.mass > 0 else 0.0
    
    @property
    def inv_inertia(self) -> float:
        return 1.0 / self.inertia if self.inertia > 0 else 0.0


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
def velocity_system(
    world: World, _: Entity, transform: Transform, rigidbody: Rigidbody
) -> None:
    wx, wy = transform.get_world_position()
    wx += rigidbody.vx * world.timestep
    wy += rigidbody.vy * world.timestep
    transform.set_world_position(wx, wy)
    
    angle = transform.get_world_angle()
    angle += rigidbody.angular_velocity * world.timestep
    transform.set_world_angle(angle)


@for_each
def damping_system(
    world: World, _: Entity, rigidbody: Rigidbody
) -> None:
    rigidbody.angular_velocity *= 1.0 - rigidbody.angular_damping * world.timestep
