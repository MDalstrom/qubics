import math
from application.collisions.n import Shape
from application.math import Vector, identity_corners
from application.metal.metal_shape import ShapeRenderer
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


def create_sphere(
    x: float,
    y: float,
    radius: float,
    color: tuple[int, int, int],
    vx: float = 1000.0,
    vy: float = 1000.0,
):

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
    entity = Entity("Box")
    entity.add_component(Transform(x, y, angle, width, height))
    entity.add_component(
        Rigidbody(
            velocity=Vector(vx, vy),
            mass=1.0,
            center_of_mass=Vector.zero(),
            angular_damping=0.5,
            restitution=0,
            inertia=100,
        )
    )
    entity.add_component(Shape(edges=[(identity_corners[i], identity_corners[(i + 1) % len(identity_corners)]) for i in range(len(identity_corners))]))
    entity.add_component(BoxCollider())
    entity.add_component(Collider())
    entity.add_component(ShapeRenderer(color))
    entity.add_component(Health(100))
    return entity
