from importlib import import_module
from argparse import ArgumentParser
from q_engine.alt.ecs.systems import assemble


def get_config():
    parser = ArgumentParser()
    parser.add_argument('--api')
    parser.add_argument('--scene', default='default')
    parser.add_argument('--ticks', default=120)
    return parser.parse_args()

def get_run(config = get_config()):
    if config.api == 'metal':
        from q_engine.alt.metal.deps import run
        return run
    raise 
   

def get_tick(config = get_config()):
    module = import_module(f'q_engine.alt.scenes.{config.scene}')
    return assemble(
        module.bake,
        module.simulate_fc,
        module.render_fc,
        1 / config.ticks
    )
