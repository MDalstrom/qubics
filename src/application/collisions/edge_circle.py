from os import close
from application.collisions.components import CircleCollider, Collider, CollisionInfo, CollisionMatrix, EdgeCollider
from application.math import Vector, clamp1
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@for_each
def system(world: World, _: Entity, collision_matrix: CollisionMatrix):
    @for_each
    def edges(world: World, edge: Entity, __: EdgeCollider, edge_collider: Collider, edge_transform: Transform):
        @for_each
        def circles(_: World, circle: Entity, ___: CircleCollider, circle_collider: Collider, circle_transform: Transform):
            edge_wm = edge_transform.get_world_matrix()
            circle_wm = circle_transform.get_world_matrix()
            
            local_center = edge_wm.inverse() @ Transform.get_position(circle_wm)
            local_radius = Transform.get_scale(circle_wm).x / Transform.get_scale(edge_wm).x

            closest = Vector(clamp1(local_center.x), 0)
            delta = local_center - closest
            distance = delta.length()
            
            if distance >= local_radius:
                return
            
            normal = delta.normalized()
            contact_point = edge_wm @ closest

            circle_collider.collisions.append(CollisionInfo(
                other=edge,
                normal=normal,
                penetration=distance,
                contact_point=contact_point
            ))
            edge_collider.collisions.append(CollisionInfo(
                other=circle,
                normal=-normal,
                penetration=distance,
                contact_point=contact_point
            ))

        circles(world)
    edges(world)
