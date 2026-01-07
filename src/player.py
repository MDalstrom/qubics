from infrastructure.world import World, Entity
from components import Destroyed


def play(surface, world: World, systems, renderers):
    
    for system in systems:
        for entity in world:
            if entity.get_component(Destroyed):
                continue
            system(world, entity)

    for renderer in renderers:
        for entity in world:
            if entity.get_component(Destroyed):
                continue
            renderer(surface, entity)

