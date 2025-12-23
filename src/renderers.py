from pygame import gfxdraw
from pygame.font import SysFont as Font

font = Font("Monaco", size=32)
def sphere(surface, entity):
    if 'sphere' not in entity:
        return
    
    gfxdraw.aacircle(surface, int(entity['x']), int(entity['y']), int(entity['radius']), entity['color'])
    gfxdraw.filled_circle(surface, int(entity['x']), int(entity['y']), int(entity['radius']), entity['color'])
    
    text_surface = font.render(str(entity['hp']), True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(int(entity['x']), int(entity['y'])))
    return surface.blit(text_surface, text_rect)

def bounds(surface, entity):
    if 'bounds' not in entity:
        return
    
    gfxdraw.rectangle(surface, entity['rect'], entity['color'])
