from functools import partial
from importlib import import_module
from argparse import ArgumentParser
from q_engine.domain import Loop, Tick
import ctypes


def get_config():
    parser = ArgumentParser()
    parser.add_argument("--api")
    parser.add_argument("--scene", default="default")
    parser.add_argument("--ticks", default=120)
    parser.add_argument("--shaderslib")
    parser.add_argument("--ecslib")
    parser.add_argument("--metalbootlib", default="swift/libmetalboot.dylib")
    parser.add_argument("--render3dlib")
    return parser.parse_args()


def get_run(config = get_config()) -> Loop:
    if config.api == "metal":
        metalboot = ctypes.CDLL(config.metalbootlib)
        metalboot.metal_boot.argtypes = [ctypes.c_void_p]
        metalboot.metal_boot.restype = None
        
        def run(tick: Tick):
            tick_fn = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(tick)
            metalboot.metal_boot(tick_fn)
        
        return run
    elif config.api == "tui":
        from q_engine.tui import mk_run
        return partial(mk_run)
    raise


def get_tick(config = get_config()) -> Tick:
    module = import_module(f"q_engine.scenes.{config.scene}")
    return module.get_tick()
