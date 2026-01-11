from ecs.world import World
from infrastructure.config import get_config


def get_world(
    config=get_config(),
):
    return World(config["sim_dt"])
