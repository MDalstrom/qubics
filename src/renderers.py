from pygame import gfxdraw
from pygame.font import SysFont as Font

font = Font("Monaco", size=32)


def render_system(surface, entity):
    if 'renderable' not in entity or 'transform' not in entity:
        return
    
    renderable = entity['renderable']
    transform = entity['transform']
    
    if renderable['shape'] == 'circle':
        # clamp to safe ranges to avoid pygame/gfxdraw OverflowError
        MAX_COORD = 30000
        MAX_RADIUS = 30000
        x = int(round(transform['x']))
        y = int(round(transform['y']))
        radius = int(round(renderable['radius']))
        color = renderable['color']

        if radius <= 0:
            return
        if abs(x) > MAX_COORD or abs(y) > MAX_COORD or radius > MAX_RADIUS:
            # skip rendering if values are out of drawable range
            return

        gfxdraw.aacircle(surface, x, y, radius, color)
        gfxdraw.filled_circle(surface, x, y, radius, color)

        if 'health' in entity:
            hp = entity['health']['hp']
            text_surface = font.render(str(hp), True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(x, y))
            return surface.blit(text_surface, text_rect)


def bounds_render_system(surface, entity):
    if 'bounds' not in entity:
        return
    
    gfxdraw.rectangle(surface, entity['rect'], entity['color'])
