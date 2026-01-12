from application.rendering.viewport import Viewport
from ecs.system import for_each
from ecs.world import World
from ecs.entity import Entity
from pygame import gfxdraw, Surface, SRCALPHA
import pygame
from application.transform import Transform
from dataclasses import dataclass
import math


@dataclass
class CircleRenderable:
    color: tuple[int, int, int]


@for_each
def render(world: World, _: Entity, viewport: Viewport):
    @for_each
    def inner(_: World, __: Entity, renderable: CircleRenderable, transform: Transform):
        matrix = transform.get_interpolated_world_matrix(world.alpha)
       
        position = Transform.get_position(matrix)
        x, y = position.round()
        x = min(max(x, -32768), 32767)
        y = min(max(y, -32768), 32767)
        
        scale = Transform.get_scale(matrix)
        rx, ry = scale.round()
        
        angle = math.atan2(matrix[1, 0], matrix[0, 0])
        angle_deg = math.degrees(angle)
        
        size = max(rx, ry) * 2 + 4
        temp_surface = Surface((size, size), SRCALPHA)
        temp_surface.fill((0, 0, 0, 0))
        
        center = size // 2
        gfxdraw.filled_ellipse(temp_surface, center, center, rx, ry, renderable.color)
        gfxdraw.aaellipse(temp_surface, center, center, rx, ry, renderable.color)
        
        rotated_surface = pygame.transform.rotate(temp_surface, -angle_deg)
        
        rect = rotated_surface.get_rect(center=(x, y))
        viewport.surface.blit(rotated_surface, rect)

    inner(world)
