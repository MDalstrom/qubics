from infrastructure.world import for_each
from domain import World, Entity
from components import Transform, Rigidbody, Acceleration


@for_each
def save_state_system(world: World, _: Entity, transform: Transform) -> None:
    transform.save_previous()


@for_each
def acceleration_system(world: World, _: Entity, rigidbody: Rigidbody, acceleration: Acceleration) -> None:
    rigidbody.vx += acceleration.ax * world.delta_time
    rigidbody.vy += acceleration.ay * world.delta_time


@for_each
def movement_system(world: World, _: Entity, transform: Transform, rigidbody: Rigidbody) -> None:
    wx, wy = transform.get_world_position()
    wx += rigidbody.vx * world.delta_time
    wy += rigidbody.vy * world.delta_time
    transform.set_world_position(wx, wy)


@for_each
def rotation_system(world: World, _: Entity, transform: Transform, rigidbody: Rigidbody) -> None:
    angle = transform.get_world_angle()
    angle += rigidbody.angular_velocity * world.delta_time
    transform.set_world_angle(angle)
    rigidbody.angular_velocity *= max(0.0, 1.0 - rigidbody.angular_damping * world.delta_time)
