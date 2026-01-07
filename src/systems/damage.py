from components import Health, CircleCollider, Damage, Destroyed
from infrastructure.world import World, Entity, for_each


@for_each
def damage_system(world: World, _: Entity, health: Health, collider: CircleCollider) -> None:
    for other_idx in collider.collisions:
        other = world[other_idx]
        damage = other.get_component(Damage)
        if damage:
            health.hp -= damage.value()


@for_each
def remove_dead_system(_: World, entity: Entity, health: Health) -> None:
    if health.hp <= 0:
        entity.add_component(Destroyed())
