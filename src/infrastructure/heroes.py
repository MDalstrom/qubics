from components import Transform, Rigidbody, Acceleration, Health, Damage, CircleCollider, Renderable, Parent
from domain import Entity


def create_armer(world, hp: float, x: float, y: float, radius: float, color: tuple[int, int, int], vx: float, vy: float):
    entity = Entity()
    entity.add_component(Transform(x, y))
    entity.add_component(Rigidbody(vx, vy, angular_damping=0.5, friction=0.1, restitution=1.0))
    entity.add_component(Health(hp))
    entity.add_component(Damage(lambda: 5))
    entity.add_component(CircleCollider(radius, 'sphere'))
    entity.add_component(Renderable('circle', color, radius=radius))
    entity.add_component(Acceleration(0.0, 2000.0))
    
    return world.add(entity)


def create_swordsman(world, hp: float, x: float, y: float, radius: float, color: tuple[int, int, int], vx: float, vy: float):
    entity = Entity()
    entity.add_component(Transform(x, y))
    entity.add_component(Rigidbody(vx, vy, angular_velocity=0, angular_damping=0.5, friction=0.1, restitution=1.0))
    entity.add_component(Health(hp))
    entity.add_component(CircleCollider(radius, 'sphere'))
    entity.add_component(Renderable('circle', color, radius=radius))
    entity.add_component(Acceleration(0.0, 2000.0))

    swordsman_ref = world.add(entity)
    
    sword = Entity()
    sword.add_component(Transform(0, 0))
    sword.add_component(Damage(lambda: 10))
    sword.add_component(CircleCollider(10, 'weapon'))
    sword.add_component(Renderable('circle', (50, 50, 50), radius=10))
    sword.add_component(Parent(swordsman_ref, offset_distance=radius + 10, offset_angle=0))
    world.add(sword)
    
    return swordsman_ref
