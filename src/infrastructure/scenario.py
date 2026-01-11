from importlib import import_module
from application.background import acceleration_system, fill_background, movement_system
from application.boundary_collision import boundary_collision_system
from application.display import (
    create_export_system,
    create_interactive_system,
    duration_system,
    handle_events,
)
from application.rendering import circle, bounds
from ecs.entity import Entity
from ecs.system import SystemsGroup
from ecs.world import World
from infrastructure.config import get_config
from infrastructure.surface import get_surface
from scenarios.types import Scenario


def get_writer(config=get_config()):
    import imageio

    return imageio.get_writer(config["output"], fps=config["fps"])


def _get_base_scenario(
    surface=get_surface(), config=get_config(), writer_fn=get_writer
) -> Scenario:
    def bake(world: World):
        surface_entity = Entity()
        surface_entity.add_component(surface)
        world.add(surface_entity)

    return Scenario(
        bake,
        SystemsGroup(
            [duration_system],
            [acceleration_system, movement_system, boundary_collision_system],
            [],
        ),
        SystemsGroup(
            [fill_background, handle_events],
            [circle.render, bounds.render],
            [
                (
                    create_export_system(writer_fn())
                    if config.get("output") is not None
                    else create_interactive_system()
                )
            ],
        ),
    )


def get_scenario(base=_get_base_scenario(), config=get_config()) -> Scenario:
    module = import_module(f"scenarios.{config['scenario']}")
    scenario: Scenario = module.scenario
    return base.merge(scenario)
