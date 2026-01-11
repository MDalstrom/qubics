from dataclasses import dataclass
import numpy as np
import pygame
from pygame import Surface
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@dataclass
class Duration:
    max_time: float
    elapsed: float = 0.0


@dataclass
class End: ...


def handle_events(world: World):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            raise ValueError("Interrupted")


@for_each
def duration_system(world: World, _: Entity, duration: Duration):
    duration.elapsed += world.timestep
    if duration.elapsed < duration.max_time:
        return
    raise ValueError("Duration reached")


def create_interactive_system():
    def interactive_system(world: World):
        pygame.display.flip()

    return interactive_system


def create_export_system(writer):
    @for_each
    def export_system(_: World, __: Entity, surface: Surface):
        frame_array = pygame.surfarray.array3d(surface)
        frame_array = np.transpose(frame_array, (1, 0, 2))
        writer.append_data(frame_array)

    return export_system
