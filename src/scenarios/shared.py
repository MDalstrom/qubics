from pygame import Rect
from application.background import Background
from ecs.entity import Entity
from application.collision import BoundsCollider, CircleCollider
from application.transform import Transform
from application.physics import Rigidbody, Acceleration
from application.rendering.circle import CircleRenderable
from application.rendering.bounds import BoundsRenderable


def create_background():
    entity = Entity()
    entity.add_component(Background((255, 255, 255)))
    return entity

def create_bounds():
    entity = Entity()
    entity.add_component(Transform(50, 50))
    entity.add_component(BoundsRenderable((300, 600), (0, 0, 0)))
    entity.add_component(BoundsCollider(Rect(50, 50, 300, 600)))
    return entity

def create_sphere(x: float, y: float, radius: float, color: tuple[int, int, int], vx: float = 1000.0, vy: float = 1000.0):
    entity = Entity()
    entity.add_component(Transform(x, y))
    entity.add_component(Rigidbody(vx, vy, restitution=1.0))
    entity.add_component(CircleCollider(radius))
    entity.add_component(CircleRenderable(color, radius=radius))
    entity.add_component(Acceleration(0.0, 980.0))
    return entity
