from pygame import Rect
from alt.application.background import Background
from domain import Entity
from components import Bounds, Transform, Rigidbody, CircleCollider, Renderable, Acceleration


def create_background():
    entity = Entity()
    entity.add_component(Background((255, 255, 255)))
    return entity

def create_bounds():
    entity = Entity()
    entity.add_component(Bounds(Rect(50, 50, 300, 600), (0, 0, 0)))
    return entity

def create_sphere(x: float, y: float, radius: float, color: tuple[int, int, int], vx: float = 1000.0, vy: float = 1000.0):
    entity = Entity()
    entity.add_component(Transform(x, y))
    entity.add_component(Rigidbody(vx, vy, restitution=1.0))
    entity.add_component(CircleCollider(radius, 'sphere'))
    entity.add_component(Renderable('circle', color, radius=radius))
    entity.add_component(Acceleration(0.0, 980.0))
    return entity
