import ctypes
from qubics import config
from qubics.types import TICK_FN


def run(tick_fc):
    cfg = config.make()

    backend = ctypes.CDLL(cfg.backend)
    engine = ctypes.CDLL(cfg.engine)
    world = engine.world_create()
    tick = tick_fc(world)

    backend.run(TICK_FN(tick))

if __name__ == "__main__":
    def tick_fc(world):
        def tick(render_context):
            ...
        return tick
    run(tick_fc)
