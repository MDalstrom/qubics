from components import Transform, Velocity, Acceleration, Health, Damage, CircleCollider, Renderable, Parent
from infrastructure.world import Entity


def create_armer(world, hp: float, x: float, y: float, radius: float, color: tuple[int, int, int], vx: float, vy: float):
    entity = Entity()
    entity.add_component(Transform(x, y))
    entity.add_component(Velocity(vx, vy))
    entity.add_component(Health(hp))
    entity.add_component(Damage(lambda: 5))
    entity.add_component(CircleCollider(radius, 'sphere'))
    entity.add_component(Renderable('circle', color, radius=radius))
    
    return world.add(entity)


def create_swordsman(world, hp: float, x: float, y: float, radius: float, color: tuple[int, int, int], vx: float, vy: float):
    entity = Entity()
    entity.add_component(Transform(x, y))
    entity.add_component(Velocity(vx, vy, angular_velocity=0.05))
    entity.add_component(Health(hp))
    entity.add_component(CircleCollider(radius, 'sphere'))
    entity.add_component(Renderable('circle', color, radius=radius))
    
    swordsman_ref = world.add(entity)
    
    sword = Entity()
    sword.add_component(Transform(0, 0))
    sword.add_component(Damage(lambda: 10))
    sword.add_component(CircleCollider(10, 'weapon'))
    sword.add_component(Renderable('circle', (50, 50, 50), radius=10))
    sword.add_component(Parent(swordsman_ref, offset_distance=radius + 10, offset_angle=0))
    world.add(sword)
    
    return swordsman_ref
