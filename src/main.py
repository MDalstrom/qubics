import sys
from typing import Callable
from watch import FileWatcher
import rreload
import pygame


def get_loop():
    import infrastructure.scheduler as scheduler

    return scheduler.get_loop()


pygame.init()

if "--watch=true" in sys.argv:
    current: Callable | None = None
    watcher = FileWatcher()

    def wrap(*args, **kwargs):
        global current
        if watcher.changed():
            rreload(__file__)
            current = None
        if not current:
            current = get_loop()
        return current(*args, **kwargs)

    loop = wrap
else:
    loop = get_loop()

running = True
accumulator = 0.0
while running:
    try:
        accumulator = loop(accumulator)
    except (ValueError, KeyboardInterrupt):
        running = False
