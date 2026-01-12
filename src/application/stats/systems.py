from application.collisions.components import Collider
from application.rendering.viewport import Viewport
from application.stats.components import Damage, Health
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@for_each
def deal_damage(world: World, entity: Entity, damage: Damage, collider: Collider):
    for c in collider.collisions:
        health = c.other.get_component(Health)
        if not health: 
            return
        health.value -= damage.value

def create_render_text():
    from pygame.font import init, SysFont
    init()
    font = SysFont('Monaco', size=24)

    @for_each
    def render_text(world: World, entity: Entity, viewport: Viewport):
        @for_each
        def inner(world: World, entity: Entity, health: Health, transform: Transform):
            text = str(health.value)
            text_surface = font.render(text, False, (0, 0, 0))
            x, y = transform.get_world_position()
            viewport.surface.blit(text_surface, (x, y))
        inner(world)
    return render_text
