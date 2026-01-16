from infrastructure.config import get_config
from ecs.scheduler import ClockFn


def get_export_clock(config=get_config()) -> ClockFn:
    def tick():
        return 1.0 / config["fps"]

    return tick


def get_realtime_clock() -> ClockFn:
    from time import time

    last = None

    def tick():
        nonlocal last
        current = time()
        if last is None:
            delta = 0.0
        else:
            delta = current - last
        last = current
        return delta

    return tick


def get_clock(config=get_config()):
    if config.get("output") is None:
        return get_realtime_clock()
    else:
        return get_export_clock()
