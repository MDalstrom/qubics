from functools import partial
from importlib import import_module
from argparse import ArgumentParser
from q_engine.domain import Loop, Tick


def get_config():
    parser = ArgumentParser()
    parser.add_argument("--api")
    parser.add_argument("--scene", default="default")
    parser.add_argument("--ticks", default=120)
    return parser.parse_args()


def get_run(config = get_config()) -> Loop:
    if config.api == "metal":
        from q_engine.metal import run
        from q_engine.persistent.metal import state
        return partial(run, state)
    raise


def get_tick(config = get_config()) -> Tick:
    module = import_module(f"q_engine.scenes.{config.scene}")
    return module.get_tick()

