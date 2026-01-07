from components import Transform, Velocity
from infrastructure.world import Entity


def movement_system(_, entity: Entity) -> None:
    transform = entity.get_component(Transform)
    velocity = entity.get_component(Velocity)
    
    if not transform or not velocity:
        return
    
    wx, wy = transform.get_world_position()
    wx += velocity.vx
    wy += velocity.vy
    transform.set_world_position(wx, wy)


def rotation_system(_, entity: Entity) -> None:
    transform = entity.get_component(Transform)
    velocity = entity.get_component(Velocity)
    
    if not transform or not velocity:
        return
    
    angle = transform.get_world_angle()
    angle += velocity.angular_velocity
    transform.set_world_angle(angle)
    velocity.angular_velocity *= 0.98
