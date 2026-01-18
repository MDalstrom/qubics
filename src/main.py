from infrastructure import cleanup
from infrastructure.rendering import set_dispatched, loop_lock
import rreload
from PyObjCTools import AppHelper
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self): ...

    def on_any_event(self, event):
        with loop_lock:
            if event.src_path.endswith('.py'):
                rreload(__file__)

        import infrastructure.scheduler as scheduler
        set_dispatched(scheduler.get_tick())

observer = Observer()
observer.schedule(ChangeHandler(), ".", recursive=True)
observer.start()

import infrastructure.scheduler as scheduler
set_dispatched(scheduler.get_tick())

try:
    AppHelper.runEventLoop()
except KeyboardInterrupt: ...
except Exception as e:
    import traceback
    traceback.print_exception(e)
finally:
    observer.stop()
    print("cleaning up")
    cleanup.finish()

# logger = Logger('main')
#
# if "--watch=true" in sys.argv:
#     current: Callable | None = None
#     fallback = 0.0
#
#     watcher = FileWatcher()
#     def wrap(*args, **kwargs):
#         global current
#         if watcher.changed():
#             try:
#                 rreload(__file__)
#                 current = None
#             except Exception as e:
#                 print(e)
#                 current = lambda *a, **kw: fallback
#         if not current:
#             current = scheduler.get_loop()
#         try:
#             return current(*args, **kwargs)
#         except KeyboardInterrupt:
#             raise
#         except Exception as e:
#             import traceback
#             traceback.print_exception(e)
#             return fallback
#
#     loop = wrap
# else:
#     loop = scheduler.get_loop()
#
# running = True
# accumulator = 0.0
# while running:
#     try:
#         accumulator = loop(accumulator)
#     except KeyboardInterrupt:
#         running = False
#
# print("cleaning up...")
# cleanup.finish()
