from threading import Lock
from time import sleep, time
from typing import Callable


dependencies = []

def wait(condition: Callable, timeout: float = 5.0):
    def finish(cancel = [False]):
        start_time = time()
        while not cancel[0] and condition():
            if time() - start_time > timeout:
                break
            sleep(0.01)
    return finish

def finish():
    while len(dependencies) > 0:
        dependency = dependencies.pop()
        dependency()

def create_pool(create: Callable):
    lock = Lock()
    buffers = []
    rented_count = [0]
    
    def release(buffer):
        with lock:
            buffers.append(buffer)
            rented_count[0] -= 1

    def rent():
        with lock:
            if len(buffers) == 0:
                result = create()
            else:
                result = buffers.pop(0)
            rented_count[0] += 1
            return result
    
    @wait
    def finish():
        with lock:
            return rented_count[0] > 0
    dependencies.append(finish)

    return rent, release
