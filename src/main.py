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
    fallback = 0.0

    watcher = FileWatcher()
    def wrap(*args, **kwargs):
        global current
        if watcher.changed():
            rreload(__file__)
            current = None
        if not current:
            current = get_loop()
        try:
            return current(*args, **kwargs)
        except:
            return fallback

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
