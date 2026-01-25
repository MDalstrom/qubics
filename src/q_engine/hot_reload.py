import importlib
from pathlib import Path
import sys
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BLACKLIST = {
    'q_engine.metal.deps'
}

def reload(source: str):
    root = Path(source).parent.resolve()
    for module_name, m in list(sys.modules.items()):
        if m and hasattr(m, "__file__") and m.__file__:
            if m.__file__ is source:
                continue
            if any(blacklisted in module_name for blacklisted in BLACKLIST):
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
    

