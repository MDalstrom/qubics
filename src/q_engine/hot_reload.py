import importlib
from pathlib import Path
import sys
from typing import ParamSpec, TypeVar, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

stoplist = {
    'q_engine.persistent'
}

def reload(source: str):
    root = Path(source).parent.resolve()
    for m in list(sys.modules.values()):
        if m and hasattr(m, "__file__") and m.__file__:
            if m.__file__ is source:
                continue
            if any([m.__name__.startswith(sample) for sample in stoplist]):
                continue
            m_path = Path(m.__file__).resolve()
            if root in m_path.parents or m_path == root:
                print("reloading", m)
                importlib.reload(m)


def watch(fn: Callable):
    class ChangeHandler(FileSystemEventHandler):
        def __init__(self):
            pass
        def on_any_event(self, event):
            fn(event)

    obs = Observer()
    handler = ChangeHandler()
    obs.schedule(handler, '.', recursive=True)
    obs.start()

P = ParamSpec('P')
T = TypeVar('T')
Fn = Callable[P, T]
def dispatch(fn: Fn | None) -> tuple[Fn, Callable[[Fn], None]]:
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
