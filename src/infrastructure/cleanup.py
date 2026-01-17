from time import sleep, time
from typing import Callable


dependencies = []

def wait(condition: Callable, timeout: float = 5.0):
    def finish(cancel = [False]):
        start_time = time()
        while not cancel[0] and condition():
            if time() - start_time > timeout:
                print(f"[WARNING] Cleanup timeout after {timeout}s - forcing exit")
                break
            sleep(0.01)
    return finish

def finish():
    while len(dependencies) > 0:
        dependency = dependencies.pop()
        dependency()

