from typing import Iterable
from application.collisions.components import (
    CircleCollider,
    EdgeCollider,
    BoxCollider,
    Collider,
    CollisionInfo,
    CollisionMatrix,
)
from application.math import Vector, get_corners
from application.transform import Transform
from application.physics import Rigidbody, Acceleration
from ecs.world import World
from ecs.entity import Entity
from ecs.system import for_each, singleton
import math


@for_each
def clear_collisions(_: World, __: Entity, collider: Collider) -> None:
    collider.collisions = []


def create_vertices_finder(collider_type: type, locals: Iterable[Vector]):
    def wrap(
        _, __, ___,
        collider: Collider,
        transform: Transform,
    ):
        matrix = transform.get_world_matrix()
        collider.vertices = [matrix @ vertex for vertex in locals]

    wrap.__annotations__ = {
        "_": World,
        "__": Entity,
        "___": collider_type,
        "collider": Collider,
        "transform": Transform,
        "return": None,
    }

    return for_each(wrap)

@singleton
def sat_collision_system(world: World, _: Entity, collision_matrix: CollisionMatrix):
    @for_each
    def a_inner(
        _: World,
        a_entity: Entity,
        a_collider_comp: Collider,
    ):
        @for_each
        def b_inner(
            _: World,
            b_entity: Entity,
            b_collider_comp: Collider,
        ):
            if id(a_entity) >= id(b_entity):
                return

            if not collision_matrix[(a_collider_comp.layer, b_collider_comp.layer)]:
                return

            if (
                len(a_collider_comp.vertices) < 2
                or len(b_collider_comp.vertices) < 2
            ):
                return

            min_overlap = float("inf")
            collision_normal = None

            def get_axes(vertices):
                axes = []
                for i in range(len(vertices)):
                    edge = vertices[(i + 1) % len(vertices)] - vertices[i]
                    edge_len = edge.length()
                    if edge_len > 0:
                        normal = Vector(-edge.y / edge_len, edge.x / edge_len)
                        axes.append(normal)
                return axes

            def project_polygon(vertices, axis):
                dots = [vertex.dot(axis) for vertex in vertices]
                return min(dots), max(dots)

            all_axes = get_axes(a_collider_comp.vertices) + get_axes(
                b_collider_comp.vertices
            )

            for axis in all_axes:
                a_min, a_max = project_polygon(a_collider_comp.vertices, axis)
                b_min, b_max = project_polygon(b_collider_comp.vertices, axis)

                if a_max < b_min or b_max < a_min:
                    return

                overlap = min(a_max, b_max) - max(a_min, b_min)
                if overlap < min_overlap:
                    min_overlap = overlap
                    if a_min < b_min:
                        collision_normal = axis
                    else:
                        collision_normal = Vector(-axis.x, -axis.y)

            if collision_normal is not None:
                contact_point = None
                
                max_proj = float('-inf')
                for vertex in a_collider_comp.vertices:
                    proj = vertex.dot(collision_normal)
                    if proj > max_proj:
                        max_proj = proj
                        contact_point = vertex
                
                a_collider_comp.collisions.append(
                    CollisionInfo(b_entity, -collision_normal, min_overlap, contact_point)
                )
                b_collider_comp.collisions.append(
                    CollisionInfo(a_entity, collision_normal, min_overlap, contact_point)
                )

        b_inner(world)

    a_inner(world)

@for_each
def collision_response_system(
    _: World,
    __: Entity,
    collider: Collider,
    rigidbody: Rigidbody,
    transform: Transform,
) -> None:
    if len(collider.collisions) == 0:
        return

    for collision in collider.collisions:
        normal = collision.normal

        velocity_along_normal = rigidbody.vx * normal.x + rigidbody.vy * normal.y
        if velocity_along_normal < 0:
            impulse_mag = (
                -(1 + rigidbody.restitution) * velocity_along_normal * rigidbody.mass
            )
            rigidbody.vx += rigidbody.inv_mass * impulse_mag * normal.x
            rigidbody.vy += rigidbody.inv_mass * impulse_mag * normal.y

            if collision.contact_point is not None:
                cx, cy = transform.get_world_position()
                rx = collision.contact_point.x - cx
                ry = collision.contact_point.y - cy
                torque = rx * (impulse_mag * normal.y) - ry * (impulse_mag * normal.x)
                rigidbody.angular_velocity += torque * rigidbody.inv_inertia
            
            if rigidbody.friction > 0:
                tangent_x = -normal.y
                tangent_y = normal.x
                
                velocity_along_tangent = rigidbody.vx * tangent_x + rigidbody.vy * tangent_y
                
                friction_impulse_mag = -velocity_along_tangent * rigidbody.mass * rigidbody.friction
                friction_impulse_mag = max(min(friction_impulse_mag, abs(impulse_mag) * rigidbody.friction), -abs(impulse_mag) * rigidbody.friction)
                
                rigidbody.vx += rigidbody.inv_mass * friction_impulse_mag * tangent_x
                rigidbody.vy += rigidbody.inv_mass * friction_impulse_mag * tangent_y
                
                if collision.contact_point is not None:
                    friction_torque = rx * (friction_impulse_mag * tangent_y) - ry * (friction_impulse_mag * tangent_x)
                    rigidbody.angular_velocity += friction_torque * rigidbody.inv_inertia


@for_each
def position_correction_system(
    _: World,
    __: Entity,
    collider: Collider,
    rigidbody: Rigidbody,
    transform: Transform,
) -> None:
    if len(collider.collisions) == 0:
        return

    for collision in collider.collisions:
        normal = collision.normal
        penetration = collision.penetration
        
        correction_amount = max(penetration - rigidbody.slop, 0.0) * rigidbody.position_correction
        correction = normal * correction_amount
        
        wx, wy = transform.get_world_position()
        transform.set_world_position(wx + correction.x, wy + correction.y)

_target_segments = 36
_edge_thickness = 0.01

export = [
    clear_collisions,
    create_vertices_finder(BoxCollider, list(get_corners(Vector.identity()))),
    # create_vertices_finder(CircleCollider, [
    #     Vector(math.cos(a), math.sin(a))
    #     for a in [2 * math.pi * i / _target_segments for i in range(_target_segments)]
    # ]),
    create_vertices_finder(EdgeCollider, [
        Vector(-1, -_edge_thickness),
        Vector(1, -_edge_thickness),
        Vector(1, _edge_thickness),
        Vector(-1, _edge_thickness),
    ]),
    sat_collision_system,
    collision_response_system,
    position_correction_system,
]


