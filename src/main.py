import sys
from typing import Callable
from infrastructure import cleanup
from watch import FileWatcher
import rreload
from logging import Logger

def get_loop():
    import infrastructure.scheduler as scheduler
    return scheduler.get_loop()

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
            except Exception as e:
                print(e)
                current = lambda: fallback
        if not current:
            current = get_loop()
        try:
            return current(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            import traceback
            traceback.print_exception(e)
            return fallback

    loop = wrap
else:
    loop = get_loop()

running = True
accumulator = 0.0
while running:
    try:
        accumulator = loop(accumulator)
    except KeyboardInterrupt:
        running = False

print("cleaning up...")
cleanup.finish()
