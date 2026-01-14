from pygame import draw, gfxdraw
from pygame.draw import line as draw_line
from application.collisions.components import Collider
from application.physics.rigidbody import Rigidbody
from application.transform import Transform
from application.rendering.viewport import Viewport
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World

class Destroyed():
    pass

class Debug_ContactPoint():
    timer: float = 0.1

@for_each
def debug(world: World, _: Entity, viewport: Viewport):
    @for_each
    def draw_velocities(world: World, _: Entity, transform: Transform, rigidbody: Rigidbody):
        x0, y0 = transform.get_world_position()
        v = rigidbody.velocity * world.timestep * 10
        x1, y1 = x0 + v.x, y0 + v.y
        draw_line(viewport.surface, (0, 0, 0), (int(x0), int(y0)), ((int(x1), int(y1))))
    draw_velocities(world)

    @for_each
    def spawn_contact_points(world: World, _: Entity, collider: Collider):
        for c in collider.collisions:
            e = Entity()
            e.add_component(Debug_ContactPoint())
            e.add_component(Transform(x=c.contact_point.x, y=c.contact_point.y))
            world.add(e)
    spawn_contact_points(world)

    @for_each
    def draw_contact_points(world: World, entity: Entity, __: Debug_ContactPoint, transform: Transform):
        if entity.has_component(Destroyed):
            return
        x, y = transform.get_world_position()
        gfxdraw.aacircle(viewport.surface, int(x), int(y), 5, (255, 0, 0))
    draw_contact_points(world)

    @for_each
    def elapse_contact_points(world: World, e: Entity, cp: Debug_ContactPoint):
        cp.timer -= world.timestep
        if cp.timer > 0:
            return
        e.add_component(Destroyed())
    elapse_contact_points(world)
