import importlib
from pathlib import Path
import sys
from typing import Callable, TypeVar
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def reload(source: str):
    root = Path(source).parent.resolve()
    for m in list(sys.modules.values()):
        if m and hasattr(m, "__file__") and m.__file__:
            if m.__file__ is source:
                continue

            m_path = Path(m.__file__).resolve()
            if root in m_path.parents or m_path == root:
                print("reloading", m)
                importlib.reload(m)


def watch(fn: Callable):
    class ChangeHandler(FileSystemEventHandler):
        def __init__(self, fn: Callable):
            self.on_any_event = fn

    obs = Observer()
    handler = ChangeHandler(fn)
    obs.schedule(handler, '.', recursive=True)
    obs.start()

T = TypeVar('T', bound=Callable)
def dispatch(fn: T | None) -> tuple[T, Callable]:
    def update(next):
        nonlocal fn
        fn = next

    def call(*args, **kwargs):
        nonlocal fn
        if not fn:
            return
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exception(e)
            fn = None
            return

    return call, update
