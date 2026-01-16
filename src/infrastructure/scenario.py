from importlib import import_module
from application import cleaner, physics
from application.duration import duration_system, Duration
from application.metal import display_metal
from application import collisions
from application.collisions.components import CollisionMatrix
from application.transform import save_transform_state
from application import metal
from application.stats.systems import  deal_damage
from ecs.entity import Entity
from ecs.system import SystemsGroup
from ecs.world import World
from infrastructure.config import get_config
from scenarios.types import Scenario


_collision_layers = [
    ('default', 'default')
]

def _get_base_scenario(config = get_config()) -> Scenario:
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
            [*collisions.export, *physics.systems],
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
