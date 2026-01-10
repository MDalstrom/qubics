from typing import Callable, Protocol


class ClockFn(Protocol):
    def __call__(self) -> float:
        ...
 

def tick(
    simulation_pass: Callable,
    rendering_pass: Callable[[float], None],
    fixed_step: float,
    clock: ClockFn,
):
    elapsed = [0.0]
    
    def _inner():
        delta = clock()

        elapsed[0] += delta
        while elapsed[0] >= fixed_step:
            simulation_pass()
            elapsed[0] -= fixed_step

        rendering_pass(elapsed[0] / fixed_step)

    return _inner

