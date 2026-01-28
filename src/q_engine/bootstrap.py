from functools import partial
from importlib import import_module
from argparse import ArgumentParser
from q_engine.domain import Loop, Tick
from q_engine.persistent.metal_deps import get_state


def get_config():
    parser = ArgumentParser()
    parser.add_argument("--api")
    parser.add_argument("--scene", default="default")
    parser.add_argument("--ticks", default=120)
    return parser.parse_args()


def get_run(state=get_state(), config=get_config()) -> Loop:
    if config.api == "metal":
        import q_engine.metal as metal
        return partial(metal.run, state)
    raise


def get_tick(config=get_config()) -> Tick:
    module = import_module(f"q_engine.scenes.{config.scene}")
    return module.get_tick()

