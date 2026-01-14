from dataclasses import dataclass
from typing import Iterable
from application.collisions.components import Collider, CollisionInfo, CollisionMatrix
from application.math import Vector
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World

@dataclass
class Shape:
    edges: Iterable[tuple[Vector, Vector]]

@for_each
def s(w: World, e: Entity, collision_matrix: CollisionMatrix):
    @for_each
    def a(_: World, a_entity: Entity, a_shape: Shape, a_transform: Transform, a_collider: Collider):
        @for_each
        def b(_: World, b_entity: Entity, b_shape: Shape, b_transform: Transform, b_collider: Collider):
            if a_entity == b_entity:
                return

            a_wm = a_transform.get_world_matrix()
            b_wm = b_transform.get_world_matrix()
            for lp1, lp2 in a_shape.edges:
                for lp3, lp4 in b_shape.edges:
                    p1 = a_wm @ lp1
                    p2 = a_wm @ lp2
                    p3 = b_wm @ lp3
                    p4 = b_wm @ lp4

                    r = p2 - p1
                    s = p4 - p3
                    qp = p3 - p1

                    rxs = r.cross(s)
                    qpxr = qp.cross(r)

                    if abs(rxs) < 1e-5:
                        continue

                    t = qp.cross(s) / rxs
                    u = qpxr / rxs

                    if 0 <= t <= 1 and 0 <= u <= 1:
                        intersection = p1 + t * r
                        
                        a_collider.collisions.append(CollisionInfo(
                            other=b_entity,
                            normal=r.perpendicular(),
                            penetration=0.01,
                            contact_point=intersection
                        ))
                        b_collider.collisions.append(CollisionInfo(
                            other=a_entity,
                            normal=r.perpendicular(),
                            penetration=0.01,
                            contact_point=intersection
                        ))
        b(w)
    a(w)
