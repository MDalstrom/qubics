import sys
from typing import Callable
from watch import FileWatcher
import rreload
import pygame
from logging import Logger

def get_loop():
    import infrastructure.scheduler as scheduler

    return scheduler.get_loop()


pygame.init()

logger = Logger('main')

if "--watch=true" in sys.argv:
    current: Callable | None = None
    fallback = 0.0

    watcher = FileWatcher()
    def wrap(*args, **kwargs):
        global current
        if watcher.changed():
            try:
                rreload(__file__)
                current = None
            except:
                current = lambda: fallback
        if not current:
            current = get_loop()
        try:
            return current(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(e)
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
