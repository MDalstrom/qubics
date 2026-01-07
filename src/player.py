from infrastructure.world import World
from components import Destroyed


def play(surface, world: World, systems, renderers, dt: float = 0):
    
    world.delta_time = dt
    
    if dt > 0:
        for system in systems:
            system(world)
    
    for renderer in renderers:
        for entity in world:
            if entity.get_component(Destroyed):
                continue
            renderer(surface, entity)

