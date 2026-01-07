import math
from components import Parent, Transform
from infrastructure.world import World, Entity, for_each


@for_each(Parent, Transform)
def parent_system(world: World, entity: Entity) -> None:
    parent = entity.get_component(Parent)
    transform = entity.get_component(Transform)
    
    owner = world[parent.owner.index]
    if not owner:
        return
    
    owner_transform = owner.get_component(Transform)
    if not owner_transform:
        return
    
    angle = parent.offset_angle
    distance = parent.offset_distance
    
    transform.local_x = distance * math.cos(angle)
    transform.local_y = distance * math.sin(angle)
    transform.parent = owner_transform
