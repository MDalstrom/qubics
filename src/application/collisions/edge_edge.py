from application import collisions
from application.collisions.components import BoxCollider, Collider, CollisionInfo, CollisionMatrix, EdgeCollider
from application.math import Vector, clamp1, identity_corners
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World

@for_each
def system(world: World, _: Entity, matrix: CollisionMatrix):
    @for_each
    def a(_: World, a: Entity, __: EdgeCollider, a_collider: Collider, a_transform: Transform):
        @for_each
        def b(_: World, b: Entity, __: EdgeCollider, b_collider: Collider, b_transform: Transform):
            
            ...
        b(world)
    a(world)
