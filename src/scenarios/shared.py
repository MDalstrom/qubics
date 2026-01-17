from application.collisions.n import Shape
from application.math import Vector, identity_corners
from rendering.metal_shape import ShapeRenderer
from application.stats.components import Damage, Health
from ecs.entity import Entity
from application.collisions.components import (
    EdgeCollider,
    CircleCollider,
    BoxCollider,
    Collider,
)
from application.transform import Transform
from application.physics.rigidbody import Kinematic, Rigidbody


def create_bounds(x, y, width, height):
    def create_edge(x, y, angle, length):
        entity = Entity(name='edge')
        entity.add_component(Transform(x, y, angle, scale_x=length, scale_y=1))
        entity.add_component(ShapeRenderer(color))
        entity.add_component(Kinematic())
        entity.add_component(Shape(edges=[(-Vector.right(), Vector.right())]))
        entity.add_component(EdgeCollider())
        entity.add_component(Collider())
        return entity

    color = (0, 0, 0)
    
    # yield create_edge(x, y - height, 0, width)  # Bottom: point right, normal points up
    # yield create_edge(x, y - height, -math.pi, width)  # Top: point left, normal points down
    # yield create_edge(x - width, y, math.pi / 2, height)  # Left: point down, normal points right
    # yield create_edge(x + width, y, -math.pi / 2, height)  # Right: point up, normal points left
    return
    yield


