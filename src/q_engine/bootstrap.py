from functools import partial
from importlib import import_module
from argparse import ArgumentParser

from q_engine.domain import Loop, Tick
from q_engine.ecs.systems import assemble
from q_engine.metal import State


def get_config():
    parser = ArgumentParser()
    parser.add_argument("--api")
    parser.add_argument("--scene", default="default")
    parser.add_argument("--ticks", default=120)
    return parser.parse_args()


def get_run(config=get_config()) -> Loop:
    if config.api == "metal":
        import q_engine.metal as metal
        
        device = metal.device_fc()
        view = metal.view_fc(device)
        window = metal.window_fc()
        app = metal.app_fc()
        state = State(device, window, app, view)

        return partial(metal.run, state)
    raise


def get_tick(config=get_config()) -> Tick:
    module = import_module(f"q_engine.scenes.{config.scene}")
    return assemble(module.bake, module.simulate_fc, module.render_fc, 1 / config.ticks)

