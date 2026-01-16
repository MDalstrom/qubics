from importlib import import_module

from application import cleaner, physics
from application.metal import display_metal
from application.background import fill_background
from application import collisions
from application.collisions.components import CollisionMatrix
from application.debug.drawer import debug
from application.display import (
    Duration,
    create_export_system,
    create_interactive_system,
    duration_system,
    handle_events,
)
from application.physics.rigidbody import acceleration_system, velocity_system, angular_damping_system
from application.transform import save_transform_state, Transform
from application.rendering import circle, line, box
from application import metal
from application.rendering.viewport import Viewport
from application.stats.systems import create_render_text, deal_damage
from ecs.entity import Entity
from ecs.system import System, SystemsGroup
from ecs.world import World
from infrastructure.config import get_config
from scenarios.types import Scenario


_collision_layers = [
    ('default', 'default')
]

def get_writer(config=get_config()):
    import imageio

    return imageio.get_writer(config["output"], fps=config["fps"])

def nop(world: World):
    pass

def optional(s: System | None) -> System:
    if s:
        return s
    return nop


def _get_base_scenario(
    config=get_config(), writer_fn=get_writer
) -> Scenario:
    resolution = (config['width'], config['height'])
    virtual_size = (config['virtual_width'], config['virtual_height'])
    mtk_system, viewport = display_metal.create_interactive_system(resolution, virtual_size)

    def bake(world: World):
        world.add(viewport)
        collision_matrix_entity = Entity('collision_matrix')
        collision_matrix_entity.add_component(CollisionMatrix(_collision_layers))
        world.add(collision_matrix_entity) 

        duration: float | None = config['duration']
        if duration:
            duration_entity = Entity('duration')
            duration_entity.add_component(Duration(duration))
            world.add(duration_entity)

    

    return Scenario(
        bake,
        SystemsGroup(
            [duration_system, save_transform_state],
            [*collisions.export, *physics.alt],
            [deal_damage, cleaner.system],
        ),
        SystemsGroup(
            [metal.handle_events],
            [
                metal.draw_shape_system
            ],
            [
                # (
                #     create_export_system(writer_fn(), (config['width'], config['height']))
                #     if config.get("output") is not None
                #     else create_interactive_system((config['width'], config['height']))
                # )
                mtk_system
            ],
        ),
    )


def get_scenario(base=_get_base_scenario(), config=get_config()) -> Scenario:
    module = import_module(f"scenarios.{config['scenario']}")
    scenario: Scenario = module.scenario
    return base.merge(scenario)
