from infrastructure.config import get_config
from ecs.scheduler import ClockFn


def get_export_clock(config = get_config()) -> ClockFn:
    def tick():
        return 1.0 / config['fps']
    return tick

def get_realtime_clock(config = get_config()) -> ClockFn:
    from pygame.time import Clock
    clock = Clock()
    def tick():
        return clock.tick(config['fps']) / 1000.0
    return tick

def get_clock(config = get_config()):
    if config.get('output') is None:
        return get_realtime_clock()
    else:
        return get_export_clock()
