from dataclasses import dataclass
import numpy as np
import pygame
from application.rendering.viewport import Viewport
from application.transform import Transform
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
            raise KeyboardInterrupt


@for_each
def duration_system(world: World, _: Entity, duration: Duration):
    duration.elapsed += world.timestep
    if duration.elapsed < duration.max_time:
        return
    raise ValueError("Duration reached")


def create_interactive_system(resolution: tuple[int, int]):
    output_surface = pygame.display.set_mode(resolution)
    @for_each
    def interactive_system(_: World, __: Entity, viewport: Viewport, transform: Transform):
        vw, vh = viewport.resolution
        cam_x, cam_y = transform.get_world_position()
        
        offset_x = int(cam_x - vw / 2)
        offset_y = int(cam_y - vh / 2)
        
        cropped = viewport.surface.subsurface((
            max(0, offset_x), 
            max(0, offset_y),
            min(vw, vw - offset_x),
            min(vh, vh - offset_y)
        ))
        
        surface = pygame.transform.smoothscale(cropped, resolution)
        surface = pygame.transform.flip(surface, False, True)
        pygame.display.update()
        output_surface.blit(surface, (0, 0))

    return interactive_system


def create_export_system(writer, resolution: tuple[int, int]):
    @for_each
    def export_system(_: World, __: Entity, viewport: Viewport, transform: Transform):
        vw, vh = viewport.resolution
        cam_x, cam_y = transform.get_world_position()
        
        offset_x = int(cam_x - vw / 2)
        offset_y = int(cam_y - vh / 2)
        
        cropped = viewport.surface.subsurface((
            max(0, offset_x), 
            max(0, offset_y),
            min(vw, vw - offset_x),
            min(vh, vh - offset_y)
        ))
        
        scaled_surface = pygame.transform.smoothscale(cropped, resolution)
        flipped_surface = pygame.transform.flip(scaled_surface, False, True)
        frame_array = pygame.surfarray.array3d(flipped_surface)
        frame_array = np.transpose(frame_array, (1, 0, 2))
        writer.append_data(frame_array)

    return export_system

