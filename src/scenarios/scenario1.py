from application.math import Vector
from application.physics.acceleration import Acceleration
from application.physics.damping import Damping
from application.physics.body import Body
from application.physics.velocity import Velocity
from ecs.system import SystemsGroup
from ecs.world import World
from scenarios import battle
from scenarios.types import Scenario

from .shared import create_sphere, create_box


def bake(world: World):
    # sphere = create_sphere(
    #     x=450, y=900, radius=40, color=(100, 150, 255), vx=0, vy=-200
    # )
    # world.add(sphere)
    sphere = create_sphere(
        x=450, y=500, radius=300, color=(0, 255, 000), vx=0, vy=0
    )
    world.add(sphere)
    sphere.add_component(Velocity(linear=Vector(0, 0)))
    sphere.add_component(Body(mass=1000, inertia=1000000, restitution=0, friction=1.0))
    
    box = create_box(
        x=450, y=1100, width=150, height=150, color=(50, 200, 50), vx=0, vy=0, angle=0
    )
    box.add_component(Velocity(linear=Vector(0, -100)))
    box.add_component(Acceleration(x=0, y=-980.0))
    box.add_component(Body(mass=1, inertia=10000, restitution=0, friction=0.0))
    box.add_component(Damping(linear=0, angular=0.5))
    world.add(box)
    # box = create_box(
    #     x=500, y=600, width=30, height=30, color=(100, 150, 255), vx=0, vy=0, angle=0
    # )
    # world.add(box)

scenario = Scenario(bake, SystemsGroup([], [], []), SystemsGroup([], [], []))
scenario = battle.scenario.merge(scenario)
