from pygame import gfxdraw
from pygame.font import SysFont as Font
from components import Renderable, Transform, Health, Bounds
from infrastructure.world import Entity

font = Font("Monaco", size=32)


def render_system(surface, entity: Entity):
    renderable = entity.get_component(Renderable)
    transform = entity.get_component(Transform)
    
    if not renderable or not transform:
        return
    
    if renderable.shape == 'circle':
        MAX_COORD = 30000
        MAX_RADIUS = 30000
        x, y = transform.get_world_position()
        x = int(round(x))
        y = int(round(y))
        radius = int(round(renderable.radius))
        color = renderable.color

        if radius <= 0:
            return
        if abs(x) > MAX_COORD or abs(y) > MAX_COORD or radius > MAX_RADIUS:
            return

        gfxdraw.aacircle(surface, x, y, radius, color)
        gfxdraw.filled_circle(surface, x, y, radius, color)

        health = entity.get_component(Health)
        if health:
            hp = health.hp
            text_surface = font.render(str(int(hp)), True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(x, y))
            return surface.blit(text_surface, text_rect)


def bounds_render_system(surface, entity: Entity):
    bounds = entity.get_component(Bounds)
    if not bounds:
        return
    
    gfxdraw.rectangle(surface, bounds.rect, bounds.color)
