from pygame import draw, gfxdraw, ver
from application.cleaner import Destroyed
from pygame.draw import line as draw_line
from application.collisions.components import Collider
from application.collisions.n import Shape
from application.physics.rigidbody import Rigidbody
from application.transform import Transform
from application.rendering.viewport import Viewport
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World

class Debug_ContactPoint():
    timer: float | None = None

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
            transform = Transform(x=c.contact_point.x, y=c.contact_point.y)
            transform.up = c.normal
            scale = max(c.penetration, 1.0)
            transform.set_world_scale(1, scale)
            e.add_component(transform)
            world.add(e)
    spawn_contact_points(world)

    @for_each
    def draw_shapes(world: World, entity: Entity, shape: Shape, transform: Transform):
        matrix = transform.get_world_matrix()
        vertices = [matrix @ p for p, _ in shape.edges]
        coords = [(p.x, p.y) for p in vertices]
        if len(vertices) < 3:
            return
        gfxdraw.aapolygon(viewport.surface, coords, (255, 0, 255))
    draw_shapes(world)

    @for_each
    def draw_contact_points(world: World, entity: Entity, __: Debug_ContactPoint, transform: Transform):
        if entity.has_component(Destroyed):
            return
        matrix = transform.get_world_matrix()
        position = Transform.get_position(matrix)
        up = Transform.get_up(matrix)
        x, y = position.round()
        vx, vy = up.round()
        gfxdraw.aacircle(viewport.surface, x, y, 5, (255, 0, 0))
        gfxdraw.line(viewport.surface, x, y, x + vx, y + vy, (255, 0, 255))
    draw_contact_points(world)

    @for_each
    def elapse_contact_points(world: World, e: Entity, cp: Debug_ContactPoint):
        if cp.timer:
            cp.timer -= world.timestep
            if cp.timer > 0:
                return
        e.add_component(Destroyed())
    elapse_contact_points(world)
