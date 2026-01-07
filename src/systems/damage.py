from components import Health, CircleCollider, Damage, Destroyed
from infrastructure.world import World, Entity


def damage_system(world: World, entity: Entity, dt: float) -> None:
    health = entity.get_component(Health)
    collider = entity.get_component(CircleCollider)
    
    if not health or not collider:
        return
    
    for other_idx in collider.collisions:
        other = world[other_idx]
        damage = other.get_component(Damage)
        if damage:
            health.hp -= damage.value()


def remove_dead_system(world: World, entity: Entity, dt: float) -> None:
    health = entity.get_component(Health)
    if health and health.hp <= 0:
        entity.add_component(Destroyed())
