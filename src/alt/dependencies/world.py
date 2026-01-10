from domain import World
from alt.dependencies.config import get_config


def get_world(
    config = get_config(), 
):
    return World(config['sim_dt'])
