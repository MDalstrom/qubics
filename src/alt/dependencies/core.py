from domain import Entity, World
from alt.dependencies.config import get_config
from pygame import Surface
import pygame


def get_surface(config = get_config()) -> Surface:
    pygame.init()
    return pygame.display.set_mode((config['width'], config['height']))

def get_world(surface = get_surface()):
    world = World()
    
    surface_entity = Entity()
    surface_entity.add_component(surface)
    world.add(surface_entity)

    return world
