from application.metal.metal_shape import ShapeRenderer
from application.collisions.n import Shape
from application.collisions.components import Collider
from application.math import Vector, identity_corners
from application.transform import Transform
from application.physics.acceleration import Acceleration
from application.physics.damping import Damping
from application.physics.body import Body
from application.physics.velocity import Velocity

from ecs.system import SystemsGroup
from ecs.world import World
from ecs.entity import Entity

from scenarios.types import Scenario

import math


def bake(world: World):
    sphere = Entity('sphere')
    sphere.add_component(Transform(0, 0, 0, 400, 400))
    count = 64
    iis = [i / (count - 1) for i in range(count)]
    pis = [2 * math.pi * i for i in iis] 
    vertices = [Vector(math.cos(x), math.sin(x)) for x in pis]
    edges = [(vertices[i], vertices[(i + 1) % len(vertices)]) for i in range(len(vertices))]
    sphere.add_component(Shape(edges=edges))
    sphere.add_component(Collider())
    sphere.add_component(ShapeRenderer((1.0, 0.1, 0.8, 1)))
    sphere.add_component(Velocity(linear=Vector(0, 0)))
    sphere.add_component(Body(mass=1000, inertia=1000000, restitution=0, friction=1.0))
    world.add(sphere)

    box = Entity("Box")
    box.add_component(Transform(0, 900, 0, 120, 120))
    box.add_component(Shape(edges=[(identity_corners[i], identity_corners[(i + 1) % len(identity_corners)]) for i in range(len(identity_corners))]))
    box.add_component(Collider())
    box.add_component(ShapeRenderer((1, 0.5, 1, 1)))
    box.add_component(Velocity(linear=Vector(0, -100)))
    box.add_component(Acceleration(x=0, y=-980.0))
    box.add_component(Body(mass=1, inertia=10000, restitution=0, friction=0.0))
    box.add_component(Damping(linear=0, angular=0.5))
    world.add(box)

scenario = Scenario(bake, SystemsGroup([], [], []), SystemsGroup([], [], []))
