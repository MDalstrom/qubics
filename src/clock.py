"""
Clock functions for time management.
Uses Protocol pattern instead of classes for simplicity.
"""
from typing import Protocol


class Clock(Protocol):
    """Returns current time in seconds."""
    def __call__(self) -> float:
        ...


def real_time_clock() -> Clock:
    """Clock based on actual wall time."""
    import pygame
    
    def get_time() -> float:
        return pygame.time.get_ticks() / 1000.0
    
    return get_time


def deterministic_clock(dt: float) -> Clock:
    """Clock that advances by fixed dt each call - for video export."""
    time = {'current': 0.0}
    
    def get_time() -> float:
        current = time['current']
        time['current'] += dt
        return current
    
    return get_time
