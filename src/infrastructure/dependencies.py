from functools import partial


_config = {
    'width': 384,
    'height': 768,
    'bg_color': (255, 255, 255),
    'fps': 120,
    'duration': 10,
    'sim_dt': 1.0 / 120.0
}


# Cached instances
_cached_config = None
_cached_world = None
_cached_state = None
_cached_update = None


def get_config():
    global _cached_config
    if _cached_config is not None:
        return _cached_config
    
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
    _cached_config = merged
    
    return merged


def create_bounds():
    from pygame import Rect
    from domain import Entity
    from components import Bounds
    
    entity = Entity()
    entity.add_component(Bounds(Rect(50, 50, 300, 600), (0, 0, 0)))
    return entity


def _create_world():
    """Create game world with entities."""
    global _cached_world
    if _cached_world is not None:
        return _cached_world
    
    from infrastructure import heroes
    from domain import World
    
    world = World()
    heroes.create_armer(world, 40, 200.0, 150.0, 60, (255, 100, 100), 0, 20)
    heroes.create_swordsman(world, 25, 205.0, 400.0, 50, (100, 100, 255), 0, 0)
    world.add(create_bounds())
    
    _cached_world = world
    return world


def _get_simulation_systems():
    """Get list of simulation systems."""
    import systems
    
    return [
        systems.save_state_system,
        systems.acceleration_system,
        systems.movement_system,
        systems.rotation_system,
        systems.parent_system,
        systems.boundary_collision_system,
        systems.collision_system,
        systems.damage_system,
        systems.remove_dead_system
    ]


def _get_render_fns_list():
    """Get list of render functions."""
    import renderers
    
    return [
        renderers.render_system,
        renderers.bounds_render_system
    ]


def get_simulation_state():
    """Get simulation state with world."""
    global _cached_state
    if _cached_state is not None:
        return _cached_state
    
    from simulation import SimulationState
    
    world = _create_world()
    _cached_state = SimulationState(world)
    return _cached_state


def get_update_fn():
    """Get simulation update function."""
    global _cached_update
    if _cached_update is not None:
        return _cached_update
    
    from simulation import create_simulation
    
    world = _create_world()
    systems = _get_simulation_systems()
    _, update = create_simulation(world, systems)
    _cached_update = update
    return update


def get_render_fns():
    """Get render functions list."""
    return _get_render_fns_list()


def get_backend():
    """Get rendering backend instance."""
    config = get_config()
    
    if config.get('output'):
        from backends.export import VideoBackend
        
        total_frames = config['duration'] * config['fps']
        return VideoBackend(
            config['width'], 
            config['height'], 
            config['bg_color'],
            config['fps'],
            config['output'],
            total_frames
        )
    else:
        from backends.interactive import InteractiveBackend
        
        return InteractiveBackend(
            config['width'],
            config['height'],
            config['bg_color'],
            config['fps'],
            "Balls Fight"
        )


def get_clock():
    """Get clock function based on mode."""
    config = get_config()
    
    if config.get('output'):
        from clock import deterministic_clock
        return deterministic_clock(1.0 / config['fps'])
    else:
        from clock import real_time_clock
        return real_time_clock()


def get_loop_params():
    """Get loop controller and its parameters."""
    config = get_config()
    
    if config.get('output'):
        from loop_controller import run_fixed_frames
        
        total_frames = config['duration'] * config['fps']
        frame_dt = 1.0 / config['fps']
        
        return {
            'loop': run_fixed_frames,
            'extra': {
                'frame_dt': frame_dt,
                'total_frames': total_frames
            }
        }
    else:
        from loop_controller import run_game_loop
        
        return {
            'loop': run_game_loop,
            'extra': {
                'clock': get_clock()
            }
        }

