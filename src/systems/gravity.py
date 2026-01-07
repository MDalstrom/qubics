from components import Velocity, Acceleration, Health
from infrastructure.world import World, Entity


def gravity_system(world: World, entity: Entity) -> None:
    velocity = entity.get_component(Velocity)
    acceleration = entity.get_component(Acceleration)
    health = entity.get_component(Health)

    if not velocity or not acceleration or not health:
        return

    velocity.vx += acceleration.ax
    velocity.vy += acceleration.ay
