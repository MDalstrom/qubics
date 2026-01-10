from importlib import import_module

from alt.dependencies.config import get_config
from alt.scenarios.types import Scenario

def get_scenario(config=get_config()) -> Scenario:
    module = import_module(f'alt.scenarios.{config['scenario']}')
    return module.scenario
