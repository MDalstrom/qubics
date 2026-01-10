from alt.application.background import acceleration_system, bounds_render_system, fill_background, movement_system, renderable_system
from alt.application.rendering import duration_system, Duration
from alt.scenarios.types import Scenario
from alt.dependencies.config import get_config
from domain import Entity, World
from systems.collision import boundary_collision_system
from .shared import create_bounds, create_background, create_sphere

config = get_config()

def bake(world: World):
    bounds = create_bounds()
    world.add(bounds)

    background = create_background()
    world.add(background)
    
    sphere = create_sphere(x=200, y=100, radius=20, color=(100, 150, 255), vx=100, vy=100)
    world.add(sphere)

    duration = Entity()
    duration.add_component(Duration(config['duration']))
    world.add(duration)


scenario = Scenario(
    bake, 
    [acceleration_system, movement_system, boundary_collision_system, duration_system],
    [fill_background, bounds_render_system, renderable_system]
)
