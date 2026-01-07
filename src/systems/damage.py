from components import Health, CircleCollider, Damage, Destroyed
from infrastructure.world import World, Entity, for_each


@for_each(Health, CircleCollider)
def damage_system(world: World, entity: Entity) -> None:
    health = entity.get_component(Health)
    collider = entity.get_component(CircleCollider)
    
    for other_idx in collider.collisions:
        other = world[other_idx]
        damage = other.get_component(Damage)
        if damage:
            health.hp -= damage.value()


@for_each(Health)
def remove_dead_system(world: World, entity: Entity) -> None:
    health = entity.get_component(Health)
    if health.hp <= 0:
        entity.add_component(Destroyed())
