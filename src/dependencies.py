from functools import partial
from os import error, wait
from typing import Optional


_config = {
    'width': 384,
    'height': 768,
    'bg_color': (255, 255, 255),
    'fps': 60
} 


def get_config():
    def merge(base: dict, override: dict, path=[]):
        for key in override:
            if key in base:
                if isinstance(base[key], dict) and isinstance(override[key], dict):
                    merge(base[key], override[key], path + [str(key)])
                elif override[key] is not None:
                    base[key] = override[key]
            else:
                base[key] = override[key]
        return base

    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-d", "--duration", type=int)
    parser.add_argument("-w", "--width", type=int)
    parser.add_argument("-h", "--height", type=int)
    parser.add_argument("--fps", type=int)
    parsed_config = vars(parser.parse_args())

    merged = merge(_config, parsed_config)
    
    return merged

def create_bounds():
    from pygame import Rect
    return {
        'bounds': True,
        'rect': Rect(50, 50, 300, 600),
        'color': (0, 0, 0)
    }


def create_sphere(hp, x, y, radius, color, vx, vy):
    return {
        'sphere': True,
        'hp': hp,
        'x': x,
        'y': y,
        'radius': radius,
        'color': color,
        'vx': vx,
        'vy': vy,
        'collisions': []
    }


def get_player():
    import systems
    import renderers
    from player import play
    return partial(play, 
        world=[
            create_sphere(25, 200.0, 150.0, 60, (255, 100, 100), 3.0, 2.0),
            create_sphere(40, 500.0, 400.0, 50, (100, 100, 255), -2.5, -3.5),
            create_bounds()
        ],
        systems=[
            systems.move,
            systems.collide_boundary,
            systems.clean_collisions,
            systems.collide_spheres,
            systems.subtract_health
        ],
        renderers=[
            renderers.sphere,
            renderers.bounds
        ]
    )


def export_backend():
    from backends.export import run
    return partial(run, config=get_config())


def interactive_backend():
    from backends.interactive import run
    return partial(run, config=get_config())

