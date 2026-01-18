from ecs.scheduler import tick
from infrastructure.clock import get_clock
from infrastructure.config import get_config
from infrastructure.scenario import get_scenario
from infrastructure.world import get_world
from functools import partial


def get_loop(

    scenario = get_scenario(),
    world = get_world(),
    config = get_config(),
    clock = get_clock()
):
    def simulation_pass():
        scenario.simulation(world)

    def rendering_pass(alpha: float):
        world.alpha = alpha
        scenario.rendering(world)
   
    scenario.bake(world)
    return partial(
        tick,
        simulation_pass,
        rendering_pass,
        config['timedelta'],
        clock
    )
