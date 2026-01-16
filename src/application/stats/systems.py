from application.collisions.components import Collider
from application.stats.components import Damage, Health
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@for_each
def deal_damage(world: World, entity: Entity, damage: Damage, collider: Collider):
    for c in collider.collisions:
        health = c.other.get_component(Health)
        if not health: 
            return
        health.value -= damage.value

