from functools import partial


config = {
    'width': 384,
    'height': 768,
    'bg_color': (255, 255, 255),
    'fps': 60
} 


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
        ],
        renderers=[
            renderers.sphere,
            renderers.bounds
        ]
    )


def export_backend(filename, duration):
    from backends.export import run
    return partial(run, output_file=filename, duration=duration, config=config)


def interactive_backend():
    from backends.interactive import run
    return partial(run, config=config)

