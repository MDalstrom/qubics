from domain import Entity
from alt.application.rendering import create_export_system, create_interactive_system, handle_events, duration_system
from alt.core.scheduler import ClockFn, tick
from alt.dependencies.config import get_config
from alt.dependencies.scenario import get_scenario
from alt.dependencies.world import get_world
from pygame import Surface


def get_writer(
    config = get_config()
):
    import imageio
    return imageio.get_writer(
        config['output'], 
        fps=config['fps']
    )

def get_export_surface(config = get_config()) -> Surface:
    import pygame
    pygame.init()
    return Surface((config['width'], config['height']))

def get_realtime_surface(config = get_config()) -> Surface:
    import pygame
    pygame.init()
    return pygame.display.set_mode((config['width'], config['height']))

def get_export_clock(config = get_config()) -> ClockFn:
    def tick():
        return 1.0 / config['fps']
    return tick

def get_realtime_clock(config = get_config()) -> ClockFn:
    from pygame.time import Clock
    clock = Clock()
    def tick():
        return clock.tick(config['fps']) / 1000.0
    return tick

def get_loop(
    scenario = get_scenario(),
    world = get_world(),
    config = get_config()
):
    print(config)

    clock = get_export_clock() if config.get('output') is not None else get_realtime_clock()
    surface = get_export_surface() if config.get('output') is not None else get_realtime_surface()
    
    simulation_systems = [
        duration_system,
        *scenario.simulation_systems
    ]

    rendering_systems = [
        handle_events,
        *scenario.rendering_systems,
        create_export_system(get_writer()) if config.get('output') is not None else create_interactive_system(),
    ]

    def simulation_pass():
        for system in simulation_systems:
            system(world)

    def rendering_pass(alpha: float):
        world.alpha = alpha
        for system in rendering_systems:
            system(world)
    
    scenario.bake(world)
    
    surface_entity = Entity()
    surface_entity.add_component(surface)
    world.add(surface_entity)

    return tick(
        simulation_pass,
        rendering_pass,
        config['sim_dt'],
        clock
    )
