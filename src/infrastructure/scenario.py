from functools import partial
from importlib import import_module

from infrastructure import cleanup
from rendering.export import create as create_export
from rendering.interactive import create as create_interactive
from rendering.scenario import create as create_core

from application import cleaner, physics
from application.duration import duration_system, Duration
from application import collisions
from application.collisions.components import CollisionMatrix
from application.transform import save_transform_state
from application.stats.systems import deal_damage

from ecs.entity import Entity
from ecs.system import SystemsGroup, factory
from ecs.world import World
from recorder import FFmpegRecorder
from scenarios.types import Scenario

from .config import get_config
from .rendering import (
    get_device, 
    get_pipeline,
    get_texture,
    get_view,
)


def get_rendering_scenario(
    device = get_device(),
    pipeline = get_pipeline(),
    config = get_config(),
) -> Scenario:
    return create_core(
        device, pipeline,
        width=config['virtual_width'], height=config['virtual_height']
    )

def get_recorder(
    width: int, height: int, fps: int, path: str
):
    recorder = FFmpegRecorder(width, height, fps, path)
    cleanup.dependencies.append(recorder.finish)
    return recorder 

def get_backend_scenario(
    config = get_config(),
    device = get_device(),
    texture_fn = get_texture,
    recorder_fn = get_recorder,
    view_fn = get_view,
    create_pool = cleanup.create_pool,
) -> Scenario:
    path = config['output']
    if path:
        width = config['width']
        height = config['height']
        fps = config['fps']
        return create_export(
            texture_fn(),
            device,
            recorder_fn(width, height, fps, path),
            create_pool,
            width=width, height=height,
            background_color=config['background-color'],
        )
    else:
        return create_interactive(
            view_fn()
        )

def get_application_scenario() -> Scenario:
    _collision_layers = [("default", "default")]

    def bake_collision_matrix(world: World):
        e = Entity("collisions")
        e.add_component(CollisionMatrix(_collision_layers))
        world.add(e)

    @factory
    def bake_duration(config=get_config()):
        duration = config['duration']

        def bake(duration: float, world: World):
            e = Entity("duration")
            e.add_component(Duration(duration))
            world.add(e)

        if duration:
            return partial(bake, duration)

    return Scenario(
        bake=SystemsGroup(
            [bake_duration, bake_collision_matrix],
            [],
            []
        ),
        simulation=SystemsGroup(
            [duration_system, save_transform_state],
            [*collisions.export, *physics.systems],
            [deal_damage, cleaner.system],
        ),
        rendering=SystemsGroup(
            [],
            [],
            [],
        ),
    )

def get_scenario(
    core=get_rendering_scenario(),
    backend=get_backend_scenario(),
    application=get_application_scenario(), 
    config=get_config()
) -> Scenario:
    module = import_module(f"scenarios.{config['scenario']}")
    scenario: Scenario = module.scenario
    return (core
        .merge(backend)
        .merge(application)
        .merge(scenario)
    )
