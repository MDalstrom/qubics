from application.collisions.components import Collider
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@for_each
def clear_collisions(_: World, __: Entity, collider: Collider) -> None:
    collider.collisions = []

