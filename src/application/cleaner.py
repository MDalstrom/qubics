from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


class Destroyed():
    pass

@for_each
def system(world: World, entity: Entity, _: Destroyed):
    world.entities.remove(entity)
