from application.collisions.components import CircleCollider, Collider, CollisionInfo, CollisionMatrix, EdgeCollider
from application.math import Vector, clamp1
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@for_each
def system(world: World, _: Entity, collision_matrix: CollisionMatrix):
    @for_each
    def a(world: World, edge: Entity, __: EdgeCollider, a_collider: Collider, a_transform: Transform):
        @for_each
        def b(_: World, b: Entity, ___: CircleCollider, circle_collider: Collider, b_transform: Transform):
            a_wm = a_transform.get_world_matrix()
            b_wm = b_transform.get_world_matrix()

            b_local = a_wm.inverse() @ Transform.get_position(b_wm)
            b_radius = Transform.get_scale(b_wm)
            contact_point = b_local.divide(b_radius)
            a_collider.collisions.append(CollisionInfo(
                other=b,
                normal=Vector.zero(),
                penetration=0,
                contact_point=a_wm @ contact_point
            ))
        b(world)
    a(world)
