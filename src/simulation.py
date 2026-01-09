"""
Pure simulation logic - no rendering, no pygame, no frame assumptions.
Deterministic fixed-timestep simulation.
"""
from typing import Protocol
from domain import World


class SimulationState:
    """Holds current and previous world state for interpolation."""
    
    def __init__(self, world: World):
        self.world = world
    
    def save_previous(self) -> None:
        """Save current state as previous for interpolation."""
        for entity in self.world:
            from components import Transform
            transform = entity.get_component(Transform)
            if transform:
                transform.save_previous()


class UpdateFn(Protocol):
    def __call__(self, dt: float) -> None:
        ...


def create_simulation(world: World, systems: list) -> tuple[SimulationState, UpdateFn]:
    """Create a simulation with fixed timestep logic."""
    state = SimulationState(world)
    
    def update(dt: float) -> None:
        """Update simulation by one fixed timestep."""
        world.delta_time = dt
        for system in systems:
            system(world)
    
    return state, update
