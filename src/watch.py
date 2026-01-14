from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.changed = False

    def on_any_event(self, event):
        if event.src_path.endswith('.py'):
            self.changed = True


class FileWatcher:
    def __init__(self):
        self.handler = ChangeHandler()
        self.observer = Observer()

        self.observer.schedule(self.handler, ".", recursive=True)
        self.observer.start()

    def changed(self):
        if self.handler.changed:
            self.handler.changed = False
            return True
        return False

    def stop(self):
        self.observer.stop()
        self.observer.join()

