from ecs.world import World
from infrastructure.config import get_config


def get_world(
    config=get_config(),
):
    import traceback
    print("create new world")
    traceback.print_stack(limit=3)
    return World(config["sim_dt"] * config["timescale"])
