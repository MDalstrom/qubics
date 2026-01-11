from typing import Callable, Protocol


class ClockFn(Protocol):
    def __call__(self) -> float:
        ...
 

def tick(
    simulation_pass: Callable,
    rendering_pass: Callable[[float], None],
    fixed_step: float,
    clock: ClockFn,
    accumulator: float
) -> float:
    delta = clock()

    accumulator += delta
    while accumulator >= fixed_step:
        simulation_pass()
        accumulator -= fixed_step

    rendering_pass(accumulator / fixed_step)
    return accumulator

