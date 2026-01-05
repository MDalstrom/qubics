from functools import partial


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


def get_player():
    import systems
    import renderers
    from player import play
    from infrastructure import heroes
    from infrastructure.world import create_world
    
    world = create_world()
    heroes.create_armer(world, 25, 200.0, 150.0, 60, (255, 100, 100), 3.0, 2.0)
    heroes.create_swordsman(world, 40, 500.0, 400.0, 50, (100, 100, 255), -2.5, -3.5)
    world.add(create_bounds())
    
    return partial(play, 
        world=world.entities,
        systems=[
            systems.movement_system,
            systems.rotation_system,
            systems.parent_system,
            systems.boundary_collision_system,
            systems.collision_system,
            systems.damage_system,
            systems.remove_dead_system
        ],
        renderers=[
            renderers.render_system,
            renderers.bounds_render_system
        ]
    )


def export_backend():
    from backends.export import run
    return partial(run, config=get_config())


def interactive_backend():
    from backends.interactive import run
    return partial(run, config=get_config())

