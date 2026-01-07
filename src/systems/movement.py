from infrastructure.world import World, Entity, for_each
from components import Transform, Velocity


@for_each
def movement_system(world: World, _: Entity, transform: Transform, velocity: Velocity) -> None:
    
    wx, wy = transform.get_world_position()
    wx += velocity.vx * world.delta_time
    wy += velocity.vy * world.delta_time
    transform.set_world_position(wx, wy)


@for_each
def rotation_system(world: World, _: Entity, transform: Transform, velocity: Velocity) -> None:
    angle = transform.get_world_angle()
    angle += velocity.angular_velocity * world.delta_time
    transform.set_world_angle(angle)
    velocity.angular_velocity *= 0.98 ** (world.delta_time * 60)
