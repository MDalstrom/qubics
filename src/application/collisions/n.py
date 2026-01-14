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


def _get_axes(edges: list[tuple[Vector, Vector]]) -> list[Vector]:
    """Get perpendicular axes for SAT from edges."""
    axes = []
    for p1, p2 in edges:
        edge = p2 - p1
        normal = edge.perpendicular().normalized()
        axes.append(normal)
    return axes


def _project_shape(vertices: list[Vector], axis: Vector) -> tuple[float, float]:
    """Project all vertices onto an axis, return min and max."""
    projections = [v.dot(axis) for v in vertices]
    return min(projections), max(projections)


def _get_overlap(min_a: float, max_a: float, min_b: float, max_b: float) -> float:
    """Get overlap between two projections. Negative means separation."""
    return min(max_a, max_b) - max(min_a, min_b)


def _sat_collision(
    a_vertices: list[Vector],
    b_vertices: list[Vector],
    a_edges: list[tuple[Vector, Vector]],
    b_edges: list[tuple[Vector, Vector]],
) -> tuple[bool, Vector, float]:
    """
    SAT collision detection.
    Returns (colliding, normal, penetration).
    Normal points from B toward A.
    """
    min_overlap = float('inf')
    collision_normal = Vector.zero()

    # Get axes from both shapes
    axes = _get_axes(a_edges) + _get_axes(b_edges)

    for axis in axes:
        min_a, max_a = _project_shape(a_vertices, axis)
        min_b, max_b = _project_shape(b_vertices, axis)

        overlap = _get_overlap(min_a, max_a, min_b, max_b)

        if overlap < 0:
            return False, Vector.zero(), 0.0

        if overlap < min_overlap:
            min_overlap = overlap
            collision_normal = axis

    # Ensure normal points from B toward A
    a_center = Vector(
        sum(v.x for v in a_vertices) / len(a_vertices),
        sum(v.y for v in a_vertices) / len(a_vertices),
    )
    b_center = Vector(
        sum(v.x for v in b_vertices) / len(b_vertices),
        sum(v.y for v in b_vertices) / len(b_vertices),
    )
    direction = a_center - b_center
    if collision_normal.dot(direction) < 0:
        collision_normal = -collision_normal

    return True, collision_normal, min_overlap


def _find_contact_points(
    a_edges: list[tuple[Vector, Vector]],
    b_edges: list[tuple[Vector, Vector]],
) -> list[Vector]:
    """Find contact points via edge-edge intersection."""
    contacts = []

    for a1, a2 in a_edges:
        for b1, b2 in b_edges:
            r = a2 - a1
            s = b2 - b1
            qp = b1 - a1

            rxs = r.cross(s)

            if abs(rxs) < 1e-9:
                continue

            t = qp.cross(s) / rxs
            u = qp.cross(r) / rxs

            if 0 <= t <= 1 and 0 <= u <= 1:
                intersection = a1 + t * r
                contacts.append(intersection)

    return contacts


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

            # Transform edges to world space
            a_edges_world = [(a_wm @ p1, a_wm @ p2) for p1, p2 in a_shape.edges]
            b_edges_world = [(b_wm @ p1, b_wm @ p2) for p1, p2 in b_shape.edges]

            # Get vertices from edges
            a_vertices = [e[0] for e in a_edges_world]
            b_vertices = [e[0] for e in b_edges_world]

            # SAT for collision detection, normal, and penetration
            colliding, normal, penetration = _sat_collision(
                a_vertices, b_vertices, a_edges_world, b_edges_world
            )

            if not colliding:
                return

            # Edge intersection for contact points
            contacts = _find_contact_points(a_edges_world, b_edges_world)

            for contact in contacts:
                a_collider.collisions.append(CollisionInfo(
                    other=b_entity,
                    normal=normal,
                    penetration=penetration,
                    contact_point=contact,
                ))
                b_collider.collisions.append(CollisionInfo(
                    other=a_entity,
                    normal=-normal,
                    penetration=penetration,
                    contact_point=contact,
                ))

        b(w)
    a(w)
