from pygame import Surface
from infrastructure.config import get_config


def get_export_surface(config = get_config()) -> Surface:
    return Surface((config['width'], config['height']))

def get_realtime_surface(config = get_config()) -> Surface:
    import pygame
    return pygame.display.set_mode((config['width'], config['height']))

def get_surface(config = get_config()):
    if config.get('output') is None:
        return get_realtime_surface()
    else:
        return get_export_surface()
