import math
from numpy import identity
from pygame import ver
from application.background import Background
from application.collisions.n import Shape
from application.math import Vector, identity_corners
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
from application.rendering.circle import CircleRenderable
from application.rendering.line import LineRenderer
from application.rendering.box import BoxRenderable


def create_background():
    entity = Entity('background')
    entity.add_component(Background((255, 255, 255)))
    return entity


def create_bounds(x, y, width, height):
    def create_edge(x, y, angle, length):
        entity = Entity(name='edge')
        entity.add_component(Transform(x, y, angle, scale_x=length, scale_y=1))
        entity.add_component(LineRenderer(color, 2))
        entity.add_component(Kinematic())
        entity.add_component(Shape(edges=[(-Vector.right(), Vector.right())]))
        entity.add_component(EdgeCollider())
        entity.add_component(Collider())
        return entity

    color = (0, 0, 0)

    yield create_edge(x, y - height, 0, width)  # Bottom: point right, normal points up
    # yield create_edge(x, y - height, -math.pi, width)  # Top: point left, normal points down
    # yield create_edge(x - width, y, math.pi / 2, height)  # Left: point down, normal points right
    # yield create_edge(x + width, y, -math.pi / 2, height)  # Right: point up, normal points left


def create_sphere(
    x: float,
    y: float,
    radius: float,
    color: tuple[int, int, int],
    vx: float = 1000.0,
    vy: float = 1000.0,
):
    entity = Entity('sphere')
    entity.add_component(Transform(x, y, 32, 2*radius, radius))
    entity.add_component(
        Rigidbody(
            velocity=Vector(vx, vy),
            mass=1,
            angular_damping=0.5,
            center_of_mass=Vector.zero(),
            restitution=0.5,
            inertia=1000,
        )
    )
    iis = [i / 23 for i in range(24)]
    pis = [2 * math.pi * i for i in iis] 
    vertices = [Vector(math.cos(x), math.sin(x)) for x in pis]
    edges = [(vertices[i], vertices[(i + 1) % len(vertices)]) for i in range(len(vertices))]
    entity.add_component(Shape(edges=edges))
    entity.add_component(CircleCollider())
    entity.add_component(Collider())
    entity.add_component(CircleRenderable(color))
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
    entity.add_component(BoxRenderable(color))
    entity.add_component(Health(100))
    return entity
