from importlib import import_module

from infrastructure.config import get_config
from scenarios.types import Scenario

def get_scenario(config=get_config()) -> Scenario:
    module = import_module(f'scenarios.{config["scenario"]}')
    return module.scenario
