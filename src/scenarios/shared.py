from application.background import Background
from application.stats.components import Damage, Health
from ecs.entity import Entity
from application.collisions.components import EdgeCollider, CircleCollider, BoxCollider, Collider
from application.transform import Transform
from application.physics import Rigidbody, Acceleration
from application.rendering.circle import CircleRenderable
from application.rendering.line import LineRenderer
from application.rendering.box import BoxRenderable
import math


def create_background():
    entity = Entity()
    entity.add_component(Background((255, 255, 255)))
    return entity


def create_bounds(x, y, width, height):
    def create_edge(x, y, angle, length):
        entity = Entity()
        entity.add_component(Transform(x, y, angle, length, length))
        entity.add_component(LineRenderer(color, 2))
        entity.add_component(EdgeCollider())
        entity.add_component(Collider())
        return entity

    color = (0, 0, 0)
    
    yield create_edge(x, y + height, 0, width)  # Bottom: point right, normal points up
    yield create_edge(x, y - height, -math.pi, width)  # Top: point left, normal points down
    yield create_edge(x - width, y, math.pi / 2, height)  # Left: point down, normal points right
    yield create_edge(x + width, y, -math.pi / 2, height)  # Right: point up, normal points left

def create_sphere(
    x: float,
    y: float,
    radius: float,
    color: tuple[int, int, int],
    vx: float = 1000.0,
    vy: float = 1000.0,
):
    entity = Entity()
    entity.add_component(Transform(x, y, 0, 2*radius, radius))
    entity.add_component(Rigidbody(vx*4, vy, restitution=1.0, inertia=100000))
    entity.add_component(CircleCollider())
    entity.add_component(Collider())
    entity.add_component(CircleRenderable(color))
    entity.add_component(Acceleration(0.0, 980.0))
    entity.add_component(Damage(10))
    return entity


def create_box(
    x: float,
    y: float,
    width: float,
    height: float,
    angle: float = 0.0,
    color: tuple[int, int, int] = (0, 0, 255),
    vx: float = 0.0,
    vy: float = 0.0,
):
    entity = Entity()
    entity.add_component(Transform(x, y, angle, width, height))
    entity.add_component(Rigidbody(vx, vy, friction=1, restitution=00, inertia=1000000))
    entity.add_component(BoxCollider())
    entity.add_component(Collider())
    entity.add_component(BoxRenderable(color))
    entity.add_component(Acceleration(0.0, 980.0))
    entity.add_component(Health(100))
    return entity
